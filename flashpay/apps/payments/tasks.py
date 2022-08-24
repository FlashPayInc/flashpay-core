from algosdk.error import IndexerHTTPError
from huey import crontab
from huey.contrib.djhuey import db_periodic_task, lock_task

from django.conf import settings

from flashpay.apps.payments.models import Transaction, TransactionStatus
from flashpay.apps.payments.utils import verify_transaction


@db_periodic_task(crontab(minute="*/1"))
@lock_task("lock-verify-txn")
def verify_transactions() -> None:
    indexer = settings.INDEXER_CLIENT
    db_txns = Transaction.objects.filter(status=TransactionStatus.PENDING)
    for db_txn in db_txns:
        try:
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
                else:
                    continue
        except IndexerHTTPError:
            continue
