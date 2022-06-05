from unittest import mock

from rest_framework.test import APIClient


def test_ping_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/ping")
    assert response.status_code == 200
    assert response.data is None


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
