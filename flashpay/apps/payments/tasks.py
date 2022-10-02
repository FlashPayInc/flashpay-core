import hmac
import json
from logging import getLogger

import requests
from algosdk.error import IndexerHTTPError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, db_task, lock_task

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from flashpay.apps.account.models import Account, APIKey, Webhook
from flashpay.apps.core.models import Asset, Network
from flashpay.apps.payments.models import DailyRevenue, PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.serializers import TransactionSerializer
from flashpay.apps.payments.utils import verify_transaction

logger = getLogger(__name__)


@db_task(retries=5, retry_delay=1800)
def send_webhook_transaction_status(account: Account, transaction: Transaction) -> None:
    """Task that sends webhook confirmation to users on successful transaction.
    The request times out if a response is not received in 10 seconds.

    If an error occurs, the action is repeated for a maximum of five(5) every 30 minutes.
    May raise:
    - requests.RequestException
    """
    try:
        webhook = Webhook.objects.get(account=account, network=transaction.network)
    except Webhook.DoesNotExist:
        logger.warning(
            f"Webhook was not found for account: {account.address} "
            f"with network: {account.network}"
        )
    else:
        try:
            api_key = APIKey.objects.get(account=account, network=transaction.network)
        except APIKey.DoesNotExist:
            pass
        else:
            payload = TransactionSerializer(transaction).data
            secret_key = api_key.secret_key
            hashed_payload = hmac.new(
                key=secret_key.encode(),
                msg=json.dumps(payload).encode(),
                digestmod="sha512",
            )
            headers = {
                "Accept": "text/plain",
                "Content-Type": "application/json",
                "X-FlashPay-Signature": hashed_payload.hexdigest(),
            }
            try:
                # timeout request in 10 seconds.
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    raise requests.RequestException(
                        f"Webhook confirmation failed with message {response.text} "
                        f"and status code {response.status_code}"
                    )
            except requests.RequestException:
                logger.error(
                    "An error occurred while sending webhook confirmation due to:", exc_info=True
                )


def calculate_daily_revenue(network: Network) -> None:
    date = timezone.now().date()
    accounts = Account.objects.filter(is_verified=True)
    assets = Asset.objects.filter(network=network)
    for account in accounts:
        for asset in assets:
            revenue_exists = DailyRevenue.objects.filter(
                network=network, account=account, asset=asset, created_at__date=date
            ).exists()
            if revenue_exists:
                continue
            total_revenue = Transaction.objects.filter(
                asset=asset,
                status=TransactionStatus.SUCCESS,
                updated_at__date=date,
                recipient__iexact=account.address,
            ).aggregate(total=Sum("amount"))["total"]
            if total_revenue is not None:
                DailyRevenue.objects.create(
                    account=account, asset=asset, amount=total_revenue, network=network
                )


@db_periodic_task(crontab(minute="*/1"))
@lock_task("lock-verify-txn")
def verify_transactions() -> None:
    db_txns = Transaction.objects.filter(status=TransactionStatus.PENDING)
    for db_txn in db_txns:
        try:
            indexer = (
                settings.TESTNET_INDEXER_CLIENT
                if db_txn.network == Network.TESTNET
                else settings.MAINNET_INDEXER_CLIENT
            )
            results = indexer.search_transactions(
                note_prefix=db_txn.txn_reference.encode(),
                address=db_txn.sender,
                address_role="sender",
            )
            # TODO: Handle edge cases properly.
            # this should be only one transaction.
            for onchain_txn in results["transactions"]:
                if not verify_transaction(db_txn=db_txn, onchain_txn=onchain_txn):
                    continue

                db_txn.status = TransactionStatus.SUCCESS
                db_txn.txn_hash = onchain_txn["id"]
                db_txn.save(update_fields=["status", "txn_hash"])

                # check if the txn is related to a one-time payment link and disable it.
                try:
                    # at this point, a valid txn reference is expected.
                    supposed_payment_link_uid = db_txn.txn_reference.split("_")[1]
                    payment_link = PaymentLink.objects.get(uid=supposed_payment_link_uid)
                    if payment_link.is_one_time and db_txn.amount > 0:
                        payment_link.is_active = False
                        payment_link.save()
                except PaymentLink.DoesNotExist:
                    pass

                # only send webhook on successful transactions
                if db_txn.status == TransactionStatus.SUCCESS:
                    try:
                        account = Account.objects.get(address=db_txn.recipient)
                    except Account.DoesNotExist:
                        continue
                    else:
                        send_webhook_transaction_status(account, db_txn)
        except IndexerHTTPError:
            continue


@db_periodic_task(crontab(day="*/1"))
@lock_task("lock-tesnet-daily-revenue-calculation")
def calculate_testnet_daily_revenue() -> None:
    try:
        calculate_daily_revenue(Network.TESTNET)
    except Exception:
        logger.exception(
            "An error occurred while calculating testnet daily revenue due to: ",
            exc_info=True,
        )


@db_periodic_task(crontab(day="*/1"))
@lock_task("lock-mainnet-daily-revenue-calculation")
def calculate_mainnet_daily_transaction() -> None:
    try:
        calculate_daily_revenue(Network.MAINNET)
    except Exception:
        logger.exception(
            "An error occurred while calculating mainnet daily revenue due to: ",
            exc_info=True,
        )
