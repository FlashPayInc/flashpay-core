from base64 import b64encode

import pytest
from algosdk.account import generate_account
from cryptography.fernet import Fernet

from django.conf import settings

from rest_framework.test import APIClient


@pytest.mark.django_db
def test_account_auth_view(api_client: APIClient) -> None:
    fernet = Fernet(settings.ENCRYPTION_KEY)
    # This is a valid testnet transaction.
    tx_hash = "JOD624NMQOLGSWY5B4OV377AHRESCRONHZ4G3L3EAI5PKGOOKDPQ"
    address = "4PFBQOUG4AQPAIYEYOIVOOFCQXYUPVVW3UECD5MS3SEOM64LOWB5GFWDZM"
    nonce = "12"

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
    unverified_address = generate_account()[1]
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{unverified_address}".encode())
    ).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]
    assert response.data["data"] is None


@pytest.mark.django_db
def test_account_setup_view_errors(api_client: APIClient) -> None:
    fernet = Fernet(settings.ENCRYPTION_KEY)
    valid_tx_hash = "JOD624NMQOLGSWY5B4OV377AHRESCRONHZ4G3L3EAI5PKGOOKDPQ"
    valid_address = "4PFBQOUG4AQPAIYEYOIVOOFCQXYUPVVW3UECD5MS3SEOM64LOWB5GFWDZM"
    unverified_address = generate_account()[1]
    nonce = "12"

    # first connect wallet for both addresses
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"900,{unverified_address}".encode())
    ).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]

    b64_encrypted_payload = b64encode(fernet.encrypt(f"500,{valid_address}".encode())).decode()
    response = api_client.post("/api/accounts/connect", data={"payload": b64_encrypted_payload})
    assert response.status_code == 401
    assert "Please set up your wallet and try again." in response.data["message"]

    # check that using a valid tx_hash with the wrong sender address fails.
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{unverified_address},{valid_tx_hash}".encode())
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
        fernet.encrypt(f"{wrong_nonce},{valid_address},{valid_tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 400
    assert (
        "An error occured while setting up your account due to bad transaction provided"
        in response.data["message"]
    )

    # check that setting up an already set up account fails.
    b64_encrypted_payload = b64encode(
        fernet.encrypt(f"{nonce},{valid_address},{valid_tx_hash}".encode())
    ).decode()
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 200
    assert "Your account was set up successfully" in response.data["message"]
    # now it fails
    response = api_client.post("/api/accounts/init", data={"payload": b64_encrypted_payload})
    assert response.status_code == 400
    assert "Your account has already been set up." in response.data["message"]
