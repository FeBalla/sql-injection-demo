"""Unit tests for the BigQuery repository with a stubbed client (no GCP access needed)."""

from collections.abc import Callable
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient
from google.auth.exceptions import RefreshError, TransportError
from google.cloud import bigquery

from app.core.config import Settings
from app.core.errors import DatabaseUnavailableError
from app.main import create_app
from app.sql_injection.repositories.bigquery import (
    BigQueryCustomerRepository,
)

from ..samples import APOSTROPHE

PROJECT = "demo-project-123"  # fake


class FakeJob:
    def __init__(self, result: Callable[[], Any]) -> None:
        self._result = result
        self.cancelled = False
        self.timeouts: list[float] = []

    def result(self, timeout: float) -> Any:
        self.timeouts.append(timeout)
        return self._result()

    def cancel(self) -> bool:
        self.cancelled = True
        return True


class FakeClient:
    """Fails when starting a job (``query_error``) or hands out ``job``."""

    def __init__(self, query_error: Exception | None = None, job: FakeJob | None = None) -> None:
        self._query_error = query_error
        self._job = job

    def query(self, sql: str, job_config: bigquery.QueryJobConfig | None = None) -> FakeJob:
        if self._query_error is not None:
            raise self._query_error
        assert self._job is not None
        return self._job


def repository_with(client: FakeClient, **settings: Any) -> BigQueryCustomerRepository:
    repository = BigQueryCustomerRepository(Settings(gcp_project_id=PROJECT, **settings))
    repository.__dict__["_client_or_reason"] = client  # pre-fills the cached_property
    return repository


def raise_(exc: Exception) -> Callable[[], Any]:
    def fail() -> Any:
        raise exc

    return fail


TRANSPORT_ERRORS = [
    RefreshError("token refresh failed"),
    TransportError("connection reset"),
    requests.exceptions.ConnectionError("Max retries exceeded"),
]


@pytest.mark.parametrize("error", TRANSPORT_ERRORS)
@pytest.mark.parametrize("fails_on", ["query", "result"])
def test_transport_errors_mean_unavailable(error: Exception, fails_on: str) -> None:
    client = (
        FakeClient(query_error=error)
        if fails_on == "query"
        else FakeClient(job=FakeJob(raise_(error)))
    )
    repository = repository_with(client)
    calls: list[Callable[[], Any]] = [
        repository.count,
        lambda: repository.page(5, 0),
        repository.reset,
        lambda: repository.insert(APOSTROPHE, parameterized=True),
        lambda: repository.insert(APOSTROPHE, parameterized=False),
    ]
    for call in calls:
        with pytest.raises(DatabaseUnavailableError) as raised:
            call()
        assert PROJECT not in str(raised.value)


def test_transport_errors_are_served_as_503() -> None:
    app = create_app(Settings(database_url="", gcp_project_id=PROJECT))
    repository = app.state.sql_injection_services["bigquery"].repository
    repository.__dict__["_client_or_reason"] = FakeClient(
        query_error=RefreshError("token refresh failed")
    )
    body = {"row": APOSTROPHE.model_dump(), "parameterized": True}
    client = TestClient(app)  # not a context manager: skips startup seeding
    for response in [
        client.get("/api/sql-injection/bigquery/customers"),
        client.post("/api/sql-injection/bigquery/reset"),
        client.post("/api/sql-injection/bigquery/insert", json=body),
    ]:
        assert response.status_code == 503
        assert PROJECT not in response.text


def test_jobs_are_cancelled_when_the_wait_times_out() -> None:
    job = FakeJob(raise_(TimeoutError()))
    repository = repository_with(FakeClient(job=job), bq_job_timeout_ms=2000)

    result = repository.insert(APOSTROPHE, parameterized=True)

    assert not result.ok
    assert result.error == "Cancelled: the query ran longer than 2000 ms."
    assert job.cancelled
    assert all(timeout > 2 for timeout in job.timeouts)


def test_unconfigured_bigquery_is_unavailable() -> None:
    assert BigQueryCustomerRepository(Settings(gcp_project_id="")).unavailable_reason() == (
        "GCP_PROJECT_ID is not set."
    )
