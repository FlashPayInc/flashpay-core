from typing import Any

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def algod_client() -> Any:
    return settings.ALGOD_CLIENT


@pytest.fixture
def indexer_client() -> Any:
    return settings.INDEXER_CLIENT


@pytest.fixture
def test_account() -> Any:
    account = Account.objects.create(
        address="4PFBQOUG4AQPAIYEYOIVOOFCQXYUPVVW3UECD5MS3SEOM64LOWB5GFWDZM", is_verified=True
    )
    auth_token = RefreshToken.for_user(account)
    return (account, auth_token)
