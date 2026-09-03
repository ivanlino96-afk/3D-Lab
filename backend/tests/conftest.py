from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
