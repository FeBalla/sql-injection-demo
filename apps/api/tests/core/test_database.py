"""Unit tests for the database connection factories (no database or GCP access needed)."""

from typing import Any

import google.auth
import pytest
from google.auth.credentials import AnonymousCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.database import MAX_BYTES_BILLED, create_bigquery_client, create_postgres_engine


def test_postgres_engine_uses_psycopg_and_a_fresh_session_per_request() -> None:
    settings = Settings(
        database_url="postgresql://app:secret@db:5432/lab", statement_timeout_ms=1234
    )
    engine = create_postgres_engine(settings)
    assert engine is not None
    assert engine.url.drivername == "postgresql+psycopg"
    assert (engine.url.host, engine.url.database) == ("db", "lab")
    assert isinstance(engine.pool, NullPool)
    assert create_postgres_engine(Settings(database_url="")) is None


def test_bigquery_client_caps_every_query_job(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(google.auth, "default", lambda: (AnonymousCredentials(), None))
    client = create_bigquery_client(Settings(gcp_project_id="demo", bq_job_timeout_ms=2000))
    assert isinstance(client, bigquery.Client)
    defaults = client.default_query_job_config
    assert defaults is not None
    assert defaults.maximum_bytes_billed == MAX_BYTES_BILLED == 100 * 1024 * 1024
    assert int(defaults.job_timeout_ms) == 2000


def test_bigquery_without_project_or_credentials_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert create_bigquery_client(Settings(gcp_project_id="")) == "GCP_PROJECT_ID is not set."

    def no_credentials() -> Any:
        raise DefaultCredentialsError("none")

    monkeypatch.setattr(google.auth, "default", no_credentials)
    assert create_bigquery_client(Settings(gcp_project_id="demo")) == (
        "No Google Cloud credentials found (Application Default Credentials)."
    )
