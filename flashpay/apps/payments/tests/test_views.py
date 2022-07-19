import json
from typing import Any, Tuple

import pytest

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Asset


@pytest.mark.django_db
def test_payment_link_crud_no_auth(api_client: APIClient) -> None:
    # Create Payment Link
    response1 = api_client.post("/api/payment-link/")
    assert response1.status_code == 401

    # Fetch Payment Links
    response2 = api_client.get("/api/payment-link/")
    assert response2.status_code == 401

    # Retreive Payment Link
    response3 = api_client.get("/api/payment-link/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response3.status_code == 401

    # Active | Inactive Update Test
    response5 = api_client.put("/api/payment-link/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response5.status_code == 401

    # Fetch Transactions Endpoint
    response6 = api_client.get(
        "/api/payment-link/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c/transactions"
    )
    assert response6.status_code == 401


@pytest.mark.django_db
def test_payment_link_crud(api_client: APIClient, test_account: Tuple[Account, Any]) -> None:
    auth_token = test_account[1]
    api_client.credentials(HTTP_AUTHORIZATION="Bearer " + str(auth_token.access_token))

    asset = Asset.objects.create(
        asa_id=1, short_name="ALGO", long_name="Algorand", image_url="https://hi.com/algo"
    )

    # Create Payment Link
    data = {"name": "Test", "description": "test", "asset": asset.uid, "amount": 40}
    response1 = api_client.post("/api/payment-link/", data=data)
    assert response1.status_code == 201

    # Fetch Payment Links
    response2 = api_client.get("/api/payment-link/")
    assert response2.status_code == 200
    results = json.loads(response2.content)["results"]
    assert len(results) == 1

    # Retreive Payment Link
    response3 = api_client.get(f"/api/payment-link/{results[0]['uid']}")
    assert response3.status_code == 200

    # Retrieve Payment Link 404
    response4 = api_client.get("/api/payment-link/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response4.status_code == 404

    # Active | Inactive Update Test
    response5 = api_client.put(f"/api/payment-link/{results[0]['uid']}")
    assert response5.status_code == 200
    assert not json.loads(response5.content)["data"]["is_active"]

    # Fetch Transactions Endpoint
    response6 = api_client.get(f"/api/payment-link/{results[0]['uid']}/transactions")
    assert response6.status_code == 200
