"""Unit tests for the BigQuery job helpers (no GCP access needed)."""

from google.api_core.exceptions import Forbidden

from app.core.bigquery import redacted_error_message

PROJECT = "demo-project-123"  # fake


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
