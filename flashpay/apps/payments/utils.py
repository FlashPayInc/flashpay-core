import secrets
from typing import Any
from uuid import uuid4

from django.conf import settings

from flashpay.apps.payments.models import Transaction


def generate_txn_ref(uid: Any = None) -> str:
    if not uid:
        uid = uuid4()
    return f"fp_{uid.hex}_{secrets.token_hex(3)}"


def check_if_opted_in_asa(address: str, asset_id: int) -> bool:
    algod_client = settings.ALGOD_CLIENT
    if asset_id == 0:
        return True
    account_info = algod_client.account_info(address)
    for asset in account_info["assets"]:
        if asset_id == asset["asset-id"]:
            return True
    return False


def verify_txn(transaction: Transaction, txn: dict) -> bool:
    if txn["tx-type"] == "axfer":
        recipient = txn["asset-transfer-transaction"]["receiver"]
        amount = txn["asset-transfer-transaction"]["amount"]
        asset_id = txn["asset-transfer-transaction"]["asset-id"]
    elif txn["tx-type"] == "pay":
        recipient = txn["payment-transaction"]["receiver"]
        amount = txn["payment-transaction"]["amount"]
        asset_id = 0
    else:
        return False

    if (
        transaction.recipient == recipient
        and transaction.sender == txn["sender"]
        and transaction.asset.asa_id == asset_id  # type: ignore
        and (transaction.amount * (10**transaction.asset.decimals) == amount)  # type: ignore
    ):
        return True
    return False
