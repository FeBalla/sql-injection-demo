"""Shared fixtures. Integration tests use the dedicated test databases/tables only."""

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.modules.sql_injection.backends.postgres import PostgresBackend


@pytest.fixture(scope="session")
def postgres_settings() -> Settings:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    # BigQuery disabled so API tests only touch the Postgres test database.
    return Settings(database_url=url, gcp_project_id="")


@pytest.fixture
def postgres(postgres_settings: Settings) -> PostgresBackend:
    backend = PostgresBackend(postgres_settings)
    backend.reset()
    return backend


@pytest.fixture
def client(postgres_settings: Settings, postgres: PostgresBackend) -> Iterator[TestClient]:
    with TestClient(create_app(postgres_settings)) as test_client:
        yield test_client
