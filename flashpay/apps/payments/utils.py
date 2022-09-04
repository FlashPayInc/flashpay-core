import secrets
from typing import Optional
from uuid import UUID, uuid4

from django.conf import settings

from flashpay.apps.core.models import Network
from flashpay.apps.payments.models import Transaction


def generate_txn_reference(uid: Optional[UUID] = None) -> str:
    """Generate transaction reference using a payment link's pk
    (if transaction is for payment link) or a random uuid is used as a placeholder.
    """
    if uid is None:
        uid = uuid4()
    return f"fp_{uid.hex}_{secrets.token_hex(3)}"


def check_if_address_opted_in_asa(address: str, asset_id: int, network: Network) -> bool:
    """Checks if the provided address is opted into a given ASA."""
    algod_client = (
        settings.TESTNET_ALGOD_CLIENT
        if network == Network.TESTNET
        else settings.MAINNET_ALGOD_CLIENT
    )
    # asset_id = 0  || 1 is used for Algorand native token.
    if asset_id == 0 or asset_id == 1:
        return True
    account_info = algod_client.account_info(address)
    for asset in account_info["assets"]:
        if asset_id == asset["asset-id"]:
            return True
    return False


def verify_transaction(db_txn: Transaction, onchain_txn: dict) -> bool:
    """Verifies that a transaction entry in the db conforms with its
    onchain transaction information.
    """
    if onchain_txn["tx-type"] == "axfer":
        recipient = onchain_txn["asset-transfer-transaction"]["receiver"]
        amount = onchain_txn["asset-transfer-transaction"]["amount"]
        asset_id = onchain_txn["asset-transfer-transaction"]["asset-id"]
    elif onchain_txn["tx-type"] == "pay":
        recipient = onchain_txn["payment-transaction"]["receiver"]
        amount = onchain_txn["payment-transaction"]["amount"]
        asset_id = 1 if db_txn.network == Network.MAINNET else 0
    else:
        return False

    if (
        db_txn.recipient == recipient
        and db_txn.sender == onchain_txn["sender"]
        and db_txn.asset.asa_id == asset_id
        and (db_txn.amount * (10**db_txn.asset.decimals) == amount)
    ):
        return True
    return False
