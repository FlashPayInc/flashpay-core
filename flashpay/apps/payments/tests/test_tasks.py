from uuid import UUID

import pytest

from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Asset
from flashpay.apps.payments.models import (
    DailyRevenue,
    Network,
    PaymentLink,
    Transaction,
    TransactionStatus,
)
from flashpay.apps.payments.tasks import (
    calculate_daily_revenue,
    send_webhook_transaction_status_task,
    verify_transactions_task,
)


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True])
def test_verify_transactions_task_task(
    jwt_api_client: APIClient,
    account: Account,
    usdc_asa: Asset,
) -> None:
    # Create testnet webhook
    data = {"url": "https://webhook.site/f43114db-7a3d-4cec-a49d-6d053b887fea"}
    response = jwt_api_client.post("/api/accounts/webhook", data=data)
    assert response.status_code == 201
    assert response.data["data"]["network"] == "testnet"

    # Create Payment Link
    payment_link: PaymentLink = PaymentLink.objects.create(
        uid=UUID("399c37cb-d282-4aed-8917-38a033a1ad5b"),
        name="Test Link",
        description="test",
        asset=usdc_asa,
        amount=10,
        account=account,
    )

    # fp_399c37cbd2824aed891738a033a1ad5b_03ef72
    # https://testnet.algoexplorer.io/tx/F23RSTSTWEWMX3LWZ3ZEUHRWFPOIXXAPOWS2DJ7YHK5NC3VKKTDA
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    transaction = Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=10,
        asset=usdc_asa,
        recipient=str(payment_link.account.address),  # type: ignore
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    verify_transactions_task.call_local()

    transaction = get_object_or_404(Transaction, uid=transaction.uid)
    send_webhook_transaction_status_task.call_local(payment_link.account, transaction)
    assert transaction.txn_hash == "F23RSTSTWEWMX3LWZ3ZEUHRWFPOIXXAPOWS2DJ7YHK5NC3VKKTDA"
    assert transaction.status == TransactionStatus.SUCCESS


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [True, False])
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_revenue_calculator(
    api_client: APIClient,
    account: Account,
    algo_asa: Asset,
    usdc_asa: Asset,
    usdt_asa: Asset,
    choice_asa: Asset,
    network: Network,
    random_algorand_address: str,
) -> None:
    # Create Transactions
    Transaction.objects.create(
        txn_reference="fp_hello_hii",
        txn_type="payment_link",
        amount=10000,
        asset=usdc_asa,
        recipient=str(account.address),
        status=TransactionStatus.SUCCESS,
        sender=random_algorand_address,
        network=network,
    )
    Transaction.objects.create(
        txn_reference="fp_hello_hii_hello",
        txn_type="payment_link",
        amount=100,
        asset=algo_asa,
        recipient=str(account.address),
        status=TransactionStatus.SUCCESS,
        sender=random_algorand_address,
        network=network,
    )
    Transaction.objects.create(
        txn_reference="fp_helii_hello",
        txn_type="payment_link",
        amount=1000000,
        asset=usdt_asa,
        recipient=str(account.address),
        status=TransactionStatus.SUCCESS,
        sender=random_algorand_address,
        network=network,
    )
    Transaction.objects.create(
        txn_reference="fp_hello_hii_llo",
        txn_type="payment_link",
        amount=10000000,
        asset=choice_asa,
        recipient=str(account.address),
        status=TransactionStatus.FAILED,
        sender=random_algorand_address,
        network=network,
    )

    # Calculate Daily Revenue
    calculate_daily_revenue(network)

    # Check Tests
    algo_revenue = DailyRevenue.objects.filter(
        created_at__date=timezone.now().date(),
        asset=algo_asa,
        network=network,
        account=account,
    )
    usdc_revenue = DailyRevenue.objects.filter(
        created_at__date=timezone.now().date(),
        asset=usdc_asa,
        network=network,
        account=account,
    )
    usdt_revenue = DailyRevenue.objects.filter(
        created_at__date=timezone.now().date(),
        asset=usdt_asa,
        network=network,
        account=account,
    )
    choice_coin_revenue = DailyRevenue.objects.filter(
        created_at__date=timezone.now().date(),
        asset=choice_asa,
        network=network,
        account=account,
    )
    assert algo_revenue.exists()
    assert algo_revenue.count() == 1
    assert algo_revenue.first().amount == 100  # type: ignore

    assert usdc_revenue.exists()
    assert usdc_revenue.count() == 1
    assert usdc_revenue.first().amount == 10000  # type: ignore

    assert usdt_revenue.exists()
    assert usdt_revenue.count() == 1
    assert usdt_revenue.first().amount == 1000000  # type: ignore

    assert choice_coin_revenue.exists()
    assert choice_coin_revenue.count() == 1
    assert choice_coin_revenue.first().amount == 0  # type: ignore
