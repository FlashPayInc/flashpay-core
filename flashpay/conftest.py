from typing import TYPE_CHECKING, Any

import pytest
from algosdk.account import generate_account
from cryptography.fernet import Fernet
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings

from rest_framework.test import APIClient

from flashpay.apps.account.tests.fixtures import *  # noqa: F403 F401
from flashpay.apps.core.tests.fixtures import *  # noqa: F403 F401

if TYPE_CHECKING:
    from flashpay.apps.account.models import Account, APIKey


@pytest.fixture
def api_client() -> Any:
    return APIClient()


@pytest.fixture
def jwt_api_client(
    api_client: APIClient,
    account: "Account",
) -> Any:
    access_token = str(RefreshToken.for_user(account).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def secret_key_api_client(
    api_client: APIClient,
    account_api_key: "APIKey",
) -> Any:
    api_client.credentials(HTTP_X_SECRET_KEY=account_api_key.secret_key)
    return api_client


@pytest.fixture
def public_key_api_client(
    api_client: APIClient,
    account_api_key: "APIKey",
) -> Any:
    api_client.credentials(HTTP_X_PUBLIC_KEY=account_api_key.public_key)
    return api_client


@pytest.fixture
def fernet() -> Any:
    return Fernet(settings.ENCRYPTION_KEY.encode())


@pytest.fixture
def random_algorand_address() -> Any:
    return generate_account()[1]
