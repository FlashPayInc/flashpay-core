from base64 import b64encode
from typing import Tuple

import pytest
from cryptography.fernet import Fernet

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Network


@pytest.mark.django_db
def test_account_auth_view(
    api_client: APIClient,
    fernet: Fernet,
    account_auth_tx_details: Tuple[str, str, str],
    random_algorand_address: str,
) -> None:
    tx_hash = account_auth_tx_details[0]
    address = account_auth_tx_details[1]
    nonce = account_auth_tx_details[2]
    # first connect wallet
    b64_encrypted_payload = b64encode(fernet.encrypt(f"100,{address}".encode())).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]

    # now set it up
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{address},{tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 200
    assert "Your account was set up successfully" in response.data["message"]

    b64_encrypted_payload = b64encode(fernet.encrypt(f"60,{address}".encode())).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 200
    assert "access_token" in response.data["data"]
    assert "refresh_token" in response.data["data"]

    # Try authenticating an unverified wallet
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{random_algorand_address}".encode())
    ).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]
    assert response.data["data"] is None


@pytest.mark.django_db
def test_account_setup_view_errors(
    api_client: APIClient,
    fernet: Fernet,
    account_auth_tx_details: Tuple[str, str, str],
    random_algorand_address: str,
) -> None:
    # This is a valid mainnet transaction.
    tx_hash = account_auth_tx_details[0]
    address = account_auth_tx_details[1]
    nonce = account_auth_tx_details[2]

    # first connect wallet for both addresses
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"900,{random_algorand_address}".encode())
    ).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]

    b64_encrypted_payload = b64encode(fernet.encrypt(f"{nonce},{address}".encode())).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]

    # check that using a valid tx_hash with the wrong sender address fails.
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{random_algorand_address},{tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 400
    assert (
        "An error occured while setting up your account due to bad transaction provided"
        in response.data["message"]
    )

    # check that using a valid tx_hash with the wrong nonce fails.
    wrong_nonce = "wrong"
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{wrong_nonce},{address},{tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 400
    assert (
        "An error occured while setting up your account due to bad transaction provided"
        in response.data["message"]
    )

    # check that setting up an account that is already set up account fails.
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{address},{tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 200
    assert "Your account was set up successfully" in response.data["message"]
    # now it fails
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 400
    assert "Your account has already been set up." in response.data["message"]


@pytest.mark.django_db
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
@pytest.mark.parametrize("is_account_opted_in", [False, True])
def test_api_key_views(
    jwt_api_client: APIClient,
    account: Account,
    network: Network,
) -> None:
    def verify_api_key_and_network(_network: Network, _data: dict) -> None:
        if _network == Network.TESTNET:
            assert "sk_test_" in _data["secret_key"]
            assert "pk_test_" in _data["public_key"]
        else:
            assert "sk_" in _data["secret_key"]
            assert "pk_" in _data["public_key"]

    jwt_api_client.post("/api/accounts/network", data={"network": network.value})
    response = jwt_api_client.post("/api/accounts/api-keys")
    assert response.status_code == 201
    assert response.data["data"]["network"] == network.value
    verify_api_key_and_network(network, response.data["data"])

    # Fetch APIKey
    response2 = jwt_api_client.get("/api/accounts/api-keys")
    assert response2.status_code == 200
    verify_api_key_and_network(network, response2.data["data"])


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [False, True])
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_update_account_network(
    jwt_api_client: APIClient,
    account: Account,
    network: Network,
) -> None:
    network = Network.TESTNET if network == Network.MAINNET else Network.MAINNET
    response = jwt_api_client.post("/api/accounts/network", data={"network": network.value})
    assert response.status_code == 200
    assert response.data["data"]["network"] == network


@pytest.mark.django_db
@pytest.mark.parametrize("is_account_opted_in", [False, True])
@pytest.mark.parametrize("network", [Network.TESTNET, Network.MAINNET])
def test_webhook_crud(
    jwt_api_client: APIClient,
    network: Network,
) -> None:
    response = jwt_api_client.get("/api/accounts/webhook")
    assert response.status_code == 200
    assert response.data["data"] is None

    data = {"url": "https://flashpay.netlify.app/hook"}
    response = jwt_api_client.post("/api/accounts/webhook", data=data)
    assert response.status_code == 201
    assert response.data["data"]["network"] == network.value

    response = jwt_api_client.get("/api/accounts/webhook")
    assert response.status_code == 200
    assert response.data["data"]["url"] == data["url"]
    assert response.data["data"]["network"] == network.value
