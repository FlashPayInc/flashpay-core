import json
from typing import Any, Dict, List, Tuple, Union, cast

import pytest

from django.conf import settings

from rest_framework.test import APIClient

from flashpay.apps.account.models import Account
from flashpay.apps.core.models import Asset


@pytest.mark.django_db
def test_payment_link_crud_no_auth(api_client: APIClient) -> None:
    # Create Payment Link
    response1 = api_client.post("/api/payment-links/")
    assert response1.status_code == 401

    # Fetch Payment Links
    response2 = api_client.get("/api/payment-links/")
    assert response2.status_code == 401

    # Retreive Payment Link
    response3 = api_client.get("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response3.status_code == 401

    # Active | Inactive Update Test
    response5 = api_client.patch("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response5.status_code == 401

    # Fetch Transactions Endpoint
    response6 = api_client.get(
        "/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c/transactions"
    )
    assert response6.status_code == 401


@pytest.mark.django_db
def test_payment_link_crud(api_client: APIClient, test_account: Tuple[Account, Any]) -> None:
    auth_token = test_account[1]
    api_client.credentials(HTTP_AUTHORIZATION="Bearer " + str(auth_token.access_token))

    asset = Asset.objects.create(
        asa_id=1, short_name="ALGO", long_name="Algorand", image_url="https://hi.com/algo"
    )
    data = {"name": "Test", "description": "test", "asset": asset.uid, "amount": 40}
    response = api_client.post("/api/payment-links/", data=data)
    assert response.status_code == 201
    # check default image
    link = json.loads(response.content)["data"]
    assert link["image"] == settings.DEFAULT_PAYMENT_LINK_IMAGE

    # Retreive Payment Link
    response2 = api_client.get(f"/api/payment-links/{link['uid']}")
    assert response2.status_code == 200

    # Fetch payment links
    response3 = api_client.get("/api/payment-links/")
    assert response3.status_code == 200
    assert len(json.loads(response3.content)["data"]["results"]) == 1

    # Retrieve Payment Link 404
    response4 = api_client.get("/api/payment-links/4cd2344b-8c24-4cc3-8fb1-f84a249d5b0c")
    assert response4.status_code == 404

    # Active | Inactive Update Test
    response5 = api_client.patch(f"/api/payment-links/{link['uid']}")
    assert response5.status_code == 200
    assert not json.loads(response5.content)["data"]["is_active"]

    # Fetch Transactions Endpoint
    response6 = api_client.get(f"/api/payment-links/{link['uid']}/transactions")
    assert response6.status_code == 200


@pytest.mark.django_db
def test_create_payment_link_no_amount_and_zero_amount(
    api_client: APIClient, test_account: Tuple[Account, Any]
) -> None:
    auth_token = test_account[1]
    api_client.credentials(HTTP_AUTHORIZATION="Bearer " + str(auth_token.access_token))

    asset = Asset.objects.create(
        asa_id=1, short_name="ALGO", long_name="Algorand", image_url="https://hi.com/algo"
    )
    data = {"name": "Test", "description": "test", "asset": asset.uid}
    response = api_client.post("/api/payment-links/", data=data)
    data = json.loads(response.content)
    assert response.status_code == 400
    assert data["message"] == "Validation Error"
    assert (
        cast(Dict[str, Union[str, List[str]]], data["data"])["amount"][0]
        == "This field is required."
    )

    data2 = {"name": "Test", "description": "test", "asset": asset.uid, "amount": 0}
    response2 = api_client.post("/api/payment-links/", data=data2)
    data = json.loads(response2.content)
    assert response2.status_code == 400
    assert data["message"] == "Validation Error"
    assert (
        cast(Dict[str, Union[str, List[str]]], data["data"])["amount"][0]
        == "Amount cannot be less than or equal to zero."
    )
