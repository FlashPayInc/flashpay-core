import pytest

from flashpay.apps.account.models import Account, APIKey, Setting
from flashpay.apps.core.models import Network


@pytest.mark.django_db
def test_models() -> None:
    acct_data = {"address": "q6yuwvcyui"}
    setting_data = {"email": "hello@test.flashpay"}
    api_key_dat = {"secret_key": "wyeboyiowpyehif", "public_key": "buwehfhvowioiehfgl"}
    account = Account.objects.create(**acct_data)
    setting = Setting.objects.create(**setting_data, account=account)
    api_key = APIKey(**api_key_dat, account=account)

    assert account.address == acct_data["address"]
    assert str(account) == f"Account {account.address}"
    assert setting.account == account
    assert setting.email == setting_data["email"]
    assert str(setting) == f"<Settings For Account: {account.address}>"
    assert api_key.secret_key == api_key_dat["secret_key"]
    assert api_key.public_key == api_key_dat["public_key"]
    assert api_key.account == account


@pytest.mark.django_db
def test_api_keys_creation_signal_works(random_algorand_address: str) -> None:
    account = Account.objects.create(address=random_algorand_address)
    assert account.api_keys.count() == 0

    account.is_verified = True
    account.save()
    assert account.api_keys.count() == 2

    api_key_testnet = account.api_keys.get(network=Network.TESTNET)
    assert api_key_testnet.secret_key.startswith("sk_test_")
    assert api_key_testnet.public_key.startswith("pk_test_")

    api_key_mainnet = account.api_keys.get(network=Network.MAINNET)
    assert api_key_mainnet.secret_key.startswith("sk_")
    assert api_key_mainnet.public_key.startswith("pk_")
