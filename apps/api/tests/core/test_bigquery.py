"""Unit tests for the BigQuery client factory and job helpers (no GCP access needed)."""

from typing import Any

import google.auth
import pytest
from google.api_core.exceptions import Forbidden
from google.auth.credentials import AnonymousCredentials
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from app.core.bigquery import MAX_BYTES_BILLED, create_bigquery_client, redacted_error_message
from app.core.config import Settings

PROJECT = "demo-project-123"  # fake


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


def test_error_message_redacts_project_and_service_account() -> None:
    message = (
        f"Access Denied: Table {PROJECT}:injection_lab.customers: Permission denied for "
        f"lab-runner@{PROJECT}.iam.gserviceaccount.com in project {PROJECT}"
    )
    exc = Forbidden("ignored", errors=[{"message": message}])
    assert redacted_error_message(exc, PROJECT) == (
        "Access Denied: Table <project>:injection_lab.customers: Permission denied for "
        "<service-account> in project <project>"
    )
    other = Exception("sa@another-project.iam.gserviceaccount.com cannot read projects/x")
    assert redacted_error_message(other, PROJECT) == "<service-account> cannot read projects/x"
