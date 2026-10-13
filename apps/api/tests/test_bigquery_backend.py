"""Unit tests for the BigQuery backend with a stubbed client (no GCP access needed)."""

from collections.abc import Callable
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient
from google.api_core.exceptions import Forbidden
from google.auth.exceptions import RefreshError, TransportError
from google.cloud import bigquery

from app.config import Settings
from app.main import create_app
from app.modules.sql_injection.backends.base import DatabaseUnavailableError
from app.modules.sql_injection.backends.bigquery import BigQueryBackend, _error_message
from app.modules.sql_injection.statements import build_statement

from .samples import APOSTROPHE

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
        self.configs: list[bigquery.QueryJobConfig] = []

    def query(self, sql: str, job_config: bigquery.QueryJobConfig) -> FakeJob:
        self.configs.append(job_config)
        if self._query_error is not None:
            raise self._query_error
        assert self._job is not None
        return self._job


def backend_with(client: FakeClient, **settings: Any) -> BigQueryBackend:
    backend = BigQueryBackend(Settings(gcp_project_id=PROJECT, **settings))
    backend.__dict__["_client_or_reason"] = client  # pre-fills the cached_property
    return backend


def raise_(exc: Exception) -> Callable[[], Any]:
    def fail() -> Any:
        raise exc

    return fail


def test_error_message_redacts_project_and_service_account() -> None:
    message = (
        f"Access Denied: Table {PROJECT}:injection_lab.customers: Permission denied for "
        f"lab-runner@{PROJECT}.iam.gserviceaccount.com in project {PROJECT}"
    )
    exc = Forbidden("ignored", errors=[{"message": message}])
    assert _error_message(exc, PROJECT) == (
        "Access Denied: Table <project>:injection_lab.customers: Permission denied for "
        "<service-account> in project <project>"
    )
    other = Exception("sa@another-project.iam.gserviceaccount.com cannot read projects/x")
    assert _error_message(other, PROJECT) == "<service-account> cannot read projects/x"


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
    backend = backend_with(client)
    statement = build_statement("bigquery", APOSTROPHE, True, backend.statement_table)
    calls: list[Callable[[], Any]] = [
        backend.count,
        lambda: backend.page(5, 0),
        backend.reset,
        lambda: backend.execute(statement),
    ]
    for call in calls:
        with pytest.raises(DatabaseUnavailableError) as raised:
            call()
        assert PROJECT not in str(raised.value)


def test_transport_errors_are_served_as_503() -> None:
    app = create_app(Settings(database_url="", gcp_project_id=PROJECT))
    app.state.sql_injection_backends["bigquery"].__dict__["_client_or_reason"] = FakeClient(
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


def test_jobs_are_time_capped_and_cancelled_when_the_wait_times_out() -> None:
    job = FakeJob(raise_(TimeoutError()))
    client = FakeClient(job=job)
    backend = backend_with(client, bq_job_timeout_ms=2000)
    statement = build_statement("bigquery", APOSTROPHE, True, backend.statement_table)

    result = backend.execute(statement)

    assert not result.ok
    assert result.error == "Cancelled: the query ran longer than 2000 ms."
    assert job.cancelled
    assert all(timeout > 2 for timeout in job.timeouts)
    for config in client.configs:
        assert int(config.job_timeout_ms) == 2000
        assert config.maximum_bytes_billed == 100 * 1024 * 1024
