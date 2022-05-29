from rest_framework.test import APIClient


def test_ping_view(api_client: APIClient) -> None:
    response = api_client.get("/api/core/ping")
    assert response.status_code == 200
    assert response.data is None
