from base64 import b64decode
from typing import Any

from algosdk.error import IndexerHTTPError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, lock_task

from django.conf import settings

from flashpay.apps.payments.models import Transaction, TransactionStatus


@db_periodic_task(crontab(minute="*/1"))
@lock_task("lock-verify-txn")
def verify_transactions() -> Any:
    indexer = settings.INDEXER_CLIENT
    transactions = Transaction.objects.filter(status=TransactionStatus.PENDING)
    for transaction in transactions:
        try:
            results = indexer.search_transactions(
                address=transaction.recipient, asset_id=transaction.asset.asa_id  # type: ignore
            )
            txns = results["transactions"]
            for txn in txns:
                tx_note = txn.get("note", "")
                if b64decode(tx_note).decode() == transaction.txn_ref:
                    if txn["tx-type"] == "axfer":
                        recipient = txn["asset-transfer-transaction"]["receiver"]
                        amount = txn["asset-transfer-transaction"]["amount"]
                        asset_id = txn["asset-transfer-transaction"]["asset-id"]
                    elif txn["tx-type"] == "pay":
                        recipient = txn["payment-transaction"]["receiver"]
                        amount = txn["payment-transaction"]["amount"]
                        asset_id = 0
                    else:
                        continue

                    if (
                        transaction.recipient == recipient
                        and transaction.sender == txn["sender"]
                        and transaction.asset.asa_id == asset_id  # type: ignore
                        and (
                            transaction.amount * (10**transaction.asset.decimal)  # type: ignore
                            == amount
                        )
                    ):
                        transaction.status = TransactionStatus.SUCCESS
                        transaction.txn_hash = txn["id"]
                        transaction.save(update_fields=["status", "txn_hash"])
                else:
                    continue
        except IndexerHTTPError:
            continue
