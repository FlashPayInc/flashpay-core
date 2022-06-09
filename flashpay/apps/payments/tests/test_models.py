import pytest

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Asset
from flashpay.apps.payments.models import PaymentLink, PaymentLinkTransaction


@pytest.mark.django_db
def test_models() -> None:
    data = {
        "asa_id": 0,
        "short_name": "ALGO",
        "long_name": "ALGORAND",
        "image_url": "https://flashpay.com/img.png",
    }
    asset = Asset.objects.create(**data)
    account = Account.objects.create(address="fweuibfhcqw")
    link = PaymentLink.objects.create(
        asset=asset,
        account=account,
        name="Test Link",
        description="Test Link",
        amount=70,
        has_fixed_amount=True,
        is_one_time=True,
    )
    txn = PaymentLinkTransaction.objects.create(
        payment_link=link,
        txn_ref="vqhejgfvjk",
        asset=asset,
        sender="uwyeowewbejbf",
        recipient="erguewrbfhvqo",
        txn_hash="wueyfbqwobv",
        amount=70,
    )
    assert str(link) == link.name
    assert str(txn) == f"Txn {txn.txn_ref}"
