from typing import Any

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.models import Network

# TODO: Clean up our entire test suite


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
        address="4PFBQOUG4AQPAIYEYOIVOOFCQXYUPVVW3UECD5MS3SEOM64LOWB5GFWDZM",
        is_verified=True,
    )
    test_secret, test_public = generate_api_key(account.address, Network.TESTNET)
    main_secret, main_public = generate_api_key(account.address, Network.MAINNET)
    APIKey.objects.create(
        secret_key=test_secret,
        public_key=test_public,
        account=account,
        network=Network.TESTNET,
    )
    APIKey.objects.create(
        secret_key=main_secret,
        public_key=main_public,
        account=account,
        network=Network.MAINNET,
    )
    auth_token = RefreshToken.for_user(account)
    return (account, auth_token)


@pytest.fixture
def test_opted_in_account() -> Any:
    account = Account.objects.create(
        address="J7ZIYHAHBSNHO5SDR44WY3R4GKSBA6DWJGNUNYB2F3SNMEU2WAVY6OTFNQ", is_verified=True
    )
    test_secret, test_public = generate_api_key(account.address, Network.TESTNET)
    main_secret, main_public = generate_api_key(account.address, Network.MAINNET)
    APIKey.objects.create(
        secret_key=test_secret,
        public_key=test_public,
        account=account,
        network=Network.TESTNET,
    )
    APIKey.objects.create(
        secret_key=main_secret,
        public_key=main_public,
        account=account,
        network=Network.MAINNET,
    )
    auth_token = RefreshToken.for_user(account)
    return (account, auth_token)


@pytest.fixture
def api_key_account() -> Any:
    account = Account.objects.create(
        address="C7RYOGEWDT7HZM3HKPSMU7QGWTRWR3EPOQTJ2OHXGYLARD3X62DNWELS34",
        is_verified=True,
    )
    test_secret, test_public = generate_api_key(account.address, Network.TESTNET)
    main_secret, main_public = generate_api_key(account.address, Network.MAINNET)
    test_api_key = APIKey.objects.create(
        secret_key=test_secret,
        public_key=test_public,
        account=account,
        network=Network.TESTNET,
    )
    main_api_key = APIKey.objects.create(
        secret_key=main_secret,
        public_key=main_public,
        account=account,
        network=Network.MAINNET,
    )
    return (test_api_key, main_api_key, account)
