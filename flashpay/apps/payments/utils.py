import secrets
from typing import Any
from uuid import uuid4

from algosdk.v2client.algod import AlgodClient


def generate_txn_ref(uid: Any = None) -> str:
    if not uid:
        uid = uuid4()
    return f"fp_{uid.hex}_{secrets.token_hex(3)}"


def check_opted_in(  # type: ignore[no-any-unimported]
    address: str, asset_id: int, algod_client: AlgodClient
) -> bool:
    if asset_id == 0:
        return True
    account_info = algod_client.account_info(address)
    for asset in account_info["assets"]:
        if asset_id == asset["asset-id"]:
            return True
    return False
