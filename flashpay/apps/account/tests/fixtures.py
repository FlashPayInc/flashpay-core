from typing import Tuple

import pytest

from flashpay.apps.account.models import Account, APIKey
from flashpay.apps.account.utils import generate_api_key
from flashpay.apps.core.models import Network


@pytest.fixture
def is_account_opted_in() -> bool:
    """Boolean to specify whether to use opted in account or regular verified account."""
    return False


@pytest.fixture
def account_auth_tx_details() -> Tuple[str, str, str]:
    """The transaction information used for authenticating a wallet."""
    return (
        "27PZRMWDLJCCEBI7YYGYGWVFY2VB3HPVUV63T4ERIQKROFFFL2NQ",
        "MNUPZ7LXWZGJKEOPX43PHIBPSWAES3NCK3W25DHEMXB7C2MHBLTUSA7CGM",
        "1",
    )


@pytest.fixture(autouse=True)
def add_api_keys(account: Account) -> None:
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


@pytest.fixture
def account_api_key(account: Account, network: Network) -> APIKey:
    api_key = account.api_keys.filter(network=network).first()
    assert api_key is not None
    return api_key


@pytest.fixture
@pytest.mark.django_db
def account(network: Network, is_account_opted_in: bool) -> Account:
    if is_account_opted_in is True:
        account = Account.objects.create(
            address="J7ZIYHAHBSNHO5SDR44WY3R4GKSBA6DWJGNUNYB2F3SNMEU2WAVY6OTFNQ",
            network=network,
            is_verified=True,
        )
        return account

    account = Account.objects.create(
        address="4PFBQOUG4AQPAIYEYOIVOOFCQXYUPVVW3UECD5MS3SEOM64LOWB5GFWDZM",
        network=network,
        is_verified=True,
    )
    return account
