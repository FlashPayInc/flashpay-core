from typing import Any

import pytest

from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def algod_client() -> Any:
    return settings.ALGOD_CLIENT


@pytest.fixture
def indexer_client() -> Any:
    return settings.INDEXER_CLIENT
