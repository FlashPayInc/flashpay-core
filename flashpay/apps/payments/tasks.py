import hmac
import json
import requests
from algosdk.error import IndexerHTTPError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, lock_task, task

from django.conf import settings

from flashpay.apps.account.models import Account, APIKey, Webhook
from flashpay.apps.core.models import Network
from flashpay.apps.payments.models import Transaction, TransactionStatus
from flashpay.apps.payments.serializers import TransactionSerializer
from flashpay.apps.payments.utils import verify_transaction


@task(retries=5, retry_delay=10)
def send_tx_status_notification(account: Account, transaction: Transaction) -> bool:
    # sends webhook notification to set webhook url
    try:
        webhook = Webhook.objects.get(account=account, network=account.network)
    except Webhook.DoesNotExist as e:
        raise e

    try:
        api_keys = APIKey.objects.get(account=account, network=account.network)
    except APIKey.DoesNotExist:
        pass
    else:
        payload = TransactionSerializer(transaction).data
        public_key = api_keys.public_key
        hash = hmac.new(public_key.encode(), json.dumps(payload).encode(), "sha512")
        headers = {
            "Accept": "text/plain",
            "Content-Type": "application/json",
            "X-FlashPay-Sig": hash.hexdigest(),
        }
        response = requests.post(webhook.url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Webhook Client Server Error: {response.status_code}")
    return True


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
            for onchain_txn in results["transactions"]:
                if verify_transaction(db_txn=db_txn, onchain_txn=onchain_txn):
                    db_txn.status = TransactionStatus.SUCCESS
                    db_txn.txn_hash = onchain_txn["id"]
                    db_txn.save(update_fields=["status", "txn_hash"])

                    # send webhook notification to recipient
                    try:
                        account = Account.objects.get(address=db_txn.recipient)
                    except Account.DoesNotExist:
                        continue
                    send_tx_status_notification(account, db_txn)
                else:
                    continue
        except IndexerHTTPError:
            continue
