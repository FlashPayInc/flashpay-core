from unittest import mock

import pytest
from algosdk.error import AlgodHTTPError, IndexerHTTPError

from django.conf import LazySettings
from django.db import DatabaseError

from rest_framework.test import APIClient


def test_ping_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/ping")
    assert response.status_code == 200
    assert response.data is None


@pytest.mark.django_db
def test_healthcheck_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/health")
    assert response.status_code == 200

    with mock.patch(
        "flashpay.apps.core.views.HealthCheckView.get",
        side_effect=DatabaseError("Kaboom!"),
    ):
        response = api_client.get("/api/core/health")
        assert response.status_code == 500


def test_thirdparty_healthcheck_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/health/thirdparty")
    assert response.status_code == 200

    with mock.patch(
        "flashpay.apps.core.views.settings.ALGOD_CLIENT.health",
        side_effect=AlgodHTTPError("Kaboom!"),
    ):
        response = api_client.get("/api/core/health/thirdparty")
        assert response.status_code == 500

    with mock.patch(
        "flashpay.apps.core.views.settings.INDEXER_CLIENT.health",
        side_effect=IndexerHTTPError("Kaboom!"),
    ):
        response = api_client.get("/api/core/health/thirdparty")
        assert response.status_code == 500


def test_404_page(api_client: APIClient) -> None:
    response = api_client.get("/api/doesnotexist")
    assert response.status_code == 404
    assert response.request["PATH_INFO"] == "/api/doesnotexist"
    assert response.headers["Content-Type"] == "application/json"


def test_custom_exception_handler_response(api_client: APIClient) -> None:
    with mock.patch("flashpay.apps.core.views.PingView.get", side_effect=Exception("Kaboom!")):
        response = api_client.get("/api/core/ping")
        assert response.status_code == 500
        assert response.data == {
            "status_code": 500,
            "data": None,
            "message": "Internal Server Error",
        }

    response = api_client.post("/api/core/ping")
    assert response.status_code == 405


@pytest.mark.django_db
def test_assets_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/assets")
    assert response.status_code == 200


@pytest.mark.django_db
def test_update_assets_view_no_auth(api_client: APIClient) -> None:
    response = api_client.post("/api/core/assets")
    assert response.status_code == 401
    assert response.data["message"] == "Missing API Key"


@pytest.mark.django_db
def test_update_assets_view_wrong_auth(api_client: APIClient) -> None:
    api_client.credentials(HTTP_AUTHORIZATION="Token invalid")
    response = api_client.post("/api/core/assets")
    assert response.status_code == 401
    assert response.data["message"] == "Invalid API Key provided"


@pytest.mark.django_db
def test_update_assets_view(api_client: APIClient, settings: LazySettings) -> None:
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {settings.ASSETS_UPLOAD_API_KEY}")
    data = [
        {
            "asa_id": 0,
            "short_name": "ALGO",
            "long_name": "ALGORAND",
            "image_url": "https://flashpay.com/img.png",
            "decimals": 6,
            "network": "mainnet",
        },
        {
            "asa_id": 100,
            "short_name": "USDt",
            "long_name": "Tether USDt",
            "decimals": 6,
            "image_url": "https://flashpay.com/img.png",
            "network": "mainnet",
        },
        {
            "asa_id": 200,
            "short_name": "USDC",
            "long_name": "USDC",
            "decimals": 6,
            "image_url": "https://flashpay.com/img.png",
            "network": "mainnet",
        },
    ]
    response = api_client.post("/api/core/assets", data=data, format="json")
    assert response.status_code == 201
    assert response.data["message"] == "Assets updated successfully"

    # adding the same asset but with a different network fails.
    data = [
        {
            "asa_id": 0,
            "short_name": "ALGO",
            "long_name": "ALGORAND",
            "image_url": "https://flashpay.com/img.png",
            "decimals": 6,
            "network": "testnet",
        },
    ]
    response = api_client.post("/api/core/assets", data=data, format="json")
    assert response.status_code == 400
    assert response.data["message"] == "Validation Error"
    assert "asset with this asa id already exists." in str(response.data["data"])
