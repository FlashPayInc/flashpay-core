import pytest

from flashpay.apps.account.models import Account, APIKey, Notification, Setting


@pytest.mark.django_db
def test_models() -> None:
    acct_data = {"address": "q6yuwvcyui"}
    setting_data = {"email": "hello@test.flashpay"}
    api_key_dat = {"secret_key": "wyeboyiowpyehif", "public_key": "buwehfhvowioiehfgl"}
    not_data = {"title": "Test Notification", "body": "This is the body"}
    account = Account.objects.create(**acct_data)
    setting = Setting.objects.create(**setting_data, account=account)
    api_key = APIKey(**api_key_dat, account=account)
    notification = Notification.objects.create(**not_data, account=account)

    assert account.address == acct_data["address"]
    assert str(account) == f"Account {account.address}"
    assert setting.account == account
    assert setting.email == setting_data["email"]
    assert str(setting) == f"Settings For Account {account.address}"
    assert api_key.secret_key == api_key_dat["secret_key"]
    assert api_key.public_key == api_key_dat["public_key"]
    assert api_key.account == account
    assert notification.account == account
    assert notification.title == not_data["title"]
    assert notification.body == not_data["body"]
    assert notification.seen is False
    assert str(notification) == f"Notification {notification.title}"