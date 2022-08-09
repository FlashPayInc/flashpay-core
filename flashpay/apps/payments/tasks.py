from base64 import b64decode

from algosdk.error import IndexerHTTPError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, lock_task

from django.conf import settings

from flashpay.apps.payments.models import Transaction, TransactionStatus
from flashpay.apps.payments.utils import verify_txn


@db_periodic_task(crontab(minute="*/1"))
@lock_task("lock-verify-txn")
def verify_transactions() -> None:
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
                    if verify_txn(transaction=transaction, txn=txn):
                        transaction.status = TransactionStatus.SUCCESS
                        transaction.txn_hash = txn["id"]
                        transaction.save(update_fields=["status", "txn_hash"])
                else:
                    continue
        except IndexerHTTPError:
            continue
