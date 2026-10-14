"""Running BigQuery jobs within the demo's limits, and turning their failures into what it shows.

Failing to authenticate or to reach the API means the database is unavailable (HTTP 503), as
opposed to a query error, which is the database's answer to the demo SQL and is shown to the
user without anything that identifies the GCP project (this is a public demo).
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager, suppress

import requests
from google.api_core.exceptions import GoogleAPIError, RetryError
from google.auth.exceptions import GoogleAuthError
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

from .database import DatabaseUnavailableError

UNAVAILABLE_ERRORS = (GoogleAuthError, requests.exceptions.RequestException, RetryError)
"""Authentication and transport failures. RetryError is what api_core raises once retries of a
connection failure run out."""

_SERVICE_ACCOUNT = re.compile(r"[\w.+-]+@[\w.-]+\.iam\.gserviceaccount\.com")
_WAIT_MARGIN_S = 5


@contextmanager
def unavailable_on_transport_errors() -> Iterator[None]:
    """Re-raise :data:`UNAVAILABLE_ERRORS` as :class:`DatabaseUnavailableError`."""
    try:
        yield
    except UNAVAILABLE_ERRORS as exc:
        # The original message is not passed on: it can name the project or service account.
        raise DatabaseUnavailableError(
            "BigQuery is unavailable: could not authenticate or reach the API."
        ) from exc


def redacted_error_message(exc: Exception, project: str) -> str:
    """The database's own message, without the job id, location, query dump, project id or
    service account email."""
    errors = getattr(exc, "errors", None)
    if errors and isinstance(errors[0], dict) and errors[0].get("message"):
        message = str(errors[0]["message"])
    else:
        message = getattr(exc, "message", None) or str(exc)
    message = _SERVICE_ACCOUNT.sub("<service-account>", message)
    return message.replace(project, "<project>") if project else message


def wait_for_result(job: bigquery.QueryJob, *, job_timeout_ms: int) -> RowIterator:
    """Wait for the job's result, cancelling the job if the wait times out.

    BigQuery itself fails the job after ``job_timeout_ms``; the client waits a little longer
    so that normally wins, and cancels the job if it is somehow still running.
    """
    try:
        with unavailable_on_transport_errors():
            return job.result(timeout=job_timeout_ms / 1000 + _WAIT_MARGIN_S)
    except TimeoutError:
        with suppress(GoogleAPIError, *UNAVAILABLE_ERRORS):
            job.cancel()
        raise


def rows_affected(client: bigquery.Client, job: bigquery.QueryJob) -> int | None:
    """Rows changed by the job. A multi-statement query runs as a script whose parent job
    reports no DML count, so add up its child jobs (null if they cannot be listed)."""
    if job.num_dml_affected_rows is not None:
        return job.num_dml_affected_rows
    if job.statement_type != "SCRIPT":
        return None
    try:
        counts = [
            child.num_dml_affected_rows
            for child in client.list_jobs(parent_job=job)
            if isinstance(child, bigquery.QueryJob) and child.num_dml_affected_rows is not None
        ]
    except (GoogleAPIError, *UNAVAILABLE_ERRORS):
        return None
    return sum(counts) if counts else None
