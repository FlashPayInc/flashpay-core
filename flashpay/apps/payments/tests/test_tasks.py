from typing import Any, Tuple
from uuid import UUID

import pytest

from django.shortcuts import get_object_or_404

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Asset
from flashpay.apps.payments.models import PaymentLink, Transaction, TransactionStatus
from flashpay.apps.payments.tasks import send_tx_status_notification, verify_transactions


@pytest.mark.django_db
def test_verify_transactions_task(
    api_client: APIClient,
    test_opted_in_account: Tuple[Account, Any],
) -> None:
    auth_token = test_opted_in_account[1]
    api_client.credentials(HTTP_AUTHORIZATION="Bearer " + str(auth_token.access_token))

    # Create Asset
    asset = Asset.objects.create(
        asa_id=10458941,
        short_name="USDC",
        long_name="USDC",
        image_url="https://hi.com/usdc",
        decimals=6,
    )

    # Create testnet webhook
    data = {"url": "https://webhook.site/f43114db-7a3d-4cec-a49d-6d053b887fea"}
    response = api_client.post("/api/accounts/webhook", data=data)
    assert response.status_code == 201
    assert response.data["data"]["network"] == "testnet"

    # Create Payment Link
    payment_link: PaymentLink = PaymentLink.objects.create(
        uid=UUID("399c37cb-d282-4aed-8917-38a033a1ad5b"),
        name="Test Link",
        description="test",
        asset=asset,
        amount=10,
        account=test_opted_in_account[0],
    )

    # fp_399c37cbd2824aed891738a033a1ad5b_03ef72
    # https://testnet.algoexplorer.io/tx/F23RSTSTWEWMX3LWZ3ZEUHRWFPOIXXAPOWS2DJ7YHK5NC3VKKTDA
    tx_ref = "fp_" + payment_link.uid.hex + "_03ef72"

    # Create Payment link transaction
    transaction = Transaction.objects.create(
        txn_reference=tx_ref,
        txn_type="payment_link",
        amount=10,
        asset=asset,
        recipient=str(payment_link.account.address),  # type: ignore
        sender="XQ52337XYJMFNUM73IC5KSLG6UXYKMK3H36LW6RI2DRBSGIJRQBI6X6OYI",
    )

    verify_transactions.call_local()

    transaction = get_object_or_404(Transaction, uid=transaction.uid)
    send_tx_status_notification.call_local(payment_link.account, transaction)
    assert transaction.txn_hash == "F23RSTSTWEWMX3LWZ3ZEUHRWFPOIXXAPOWS2DJ7YHK5NC3VKKTDA"
    assert transaction.status == TransactionStatus.SUCCESS
