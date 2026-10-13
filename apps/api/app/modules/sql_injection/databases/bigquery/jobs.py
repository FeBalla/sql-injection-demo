"""Running BigQuery query jobs within the demo's limits: start, wait (or cancel), count rows."""

from contextlib import suppress

from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

from .errors import UNAVAILABLE_ERRORS, unavailable_on_transport_errors

MAX_BYTES_BILLED = 100 * 1024 * 1024
"""Injected SQL runs with the project's job permissions, so cap what any single query may scan
(e.g. a public dataset). The demo table itself is tiny."""

_WAIT_MARGIN_S = 5


def start_query(
    client: bigquery.Client,
    sql: str,
    params: list[bigquery.ScalarQueryParameter] | None,
    *,
    job_timeout_ms: int,
) -> bigquery.QueryJob:
    """Start a query job (raises DatabaseUnavailableError if the API cannot be reached)."""
    config = bigquery.QueryJobConfig(
        query_parameters=params or [],
        maximum_bytes_billed=MAX_BYTES_BILLED,
        job_timeout_ms=job_timeout_ms,
    )
    with unavailable_on_transport_errors():
        return client.query(sql, job_config=config)


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
