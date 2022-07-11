from unittest import mock

import pytest
from algosdk.error import AlgodHTTPError, IndexerHTTPError

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
