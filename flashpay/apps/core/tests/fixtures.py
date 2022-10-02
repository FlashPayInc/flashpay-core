import pytest

from flashpay.apps.core.models import Asset, Network


@pytest.fixture
def network() -> Network:
    return Network.TESTNET


@pytest.fixture
@pytest.mark.django_db
def algo_asa(network: Network) -> Asset:
    return Asset.objects.create(
        asa_id=0 if network == Network.TESTNET else 1,
        short_name="ALGO",
        long_name="Algorand",
        image_url="https://www.algorand.com",
        decimals=6,
        network=network,
    )


@pytest.fixture
@pytest.mark.django_db
def usdc_asa(network: Network) -> Asset:
    return Asset.objects.create(
        asa_id=10458941 if network == Network.TESTNET else 31566704,
        short_name="USDC",
        long_name="USD Coin",
        image_url="https://www.centre.io/usdc",
        decimals=6,
        network=network,
    )


@pytest.fixture
@pytest.mark.django_db
def choice_asa(network: Network) -> Asset:
    return Asset.objects.create(
        asa_id=21364625 if network == Network.TESTNET else 297995609,
        short_name="CHOICE",
        long_name="Choice Coin",
        image_url="https://choice-coin.com",
        decimals=2,
        network=network,
    )


@pytest.fixture
@pytest.mark.django_db
def usdt_asa(network: Network) -> Asset:
    return Asset.objects.create(
        asa_id=67396430 if network == Network.TESTNET else 312769,
        short_name="USDt",
        long_name="Tether USDt",
        image_url="https://tether.to",
        decimals=6,
        network=network,
    )
