"""BigQuery backend (google-cloud-bigquery), authenticated with Application Default Credentials."""

import re
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from functools import cached_property

import google.auth
import requests
from google.api_core.exceptions import GoogleAPIError, NotFound, RetryError
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

from app.config import Settings

from ..schemas import COLUMNS, Customer, Db, StatementPreview
from ..seed import SEED_ROWS
from .base import DatabaseUnavailableError, Execution

# Injected SQL runs with the project's job permissions, so cap what any single query may scan
# (e.g. a public dataset). The demo table itself is tiny.
_MAX_BYTES_BILLED = 100 * 1024 * 1024
_WAIT_MARGIN_S = 5
# Failures to authenticate or to reach the API at all: the database is unavailable (HTTP 503),
# as opposed to a query error. RetryError is what api_core raises once retries of a
# connection failure run out.
_UNAVAILABLE_ERRORS = (GoogleAuthError, requests.exceptions.RequestException, RetryError)
_SERVICE_ACCOUNT = re.compile(r"[\w.+-]+@[\w.-]+\.iam\.gserviceaccount\.com")


class BigQueryBackend:
    id: Db = "bigquery"
    label = "BigQuery"

    def __init__(self, settings: Settings) -> None:
        self.table = f"{settings.bq_dataset}.{settings.bq_table}"
        self.statement_table = self.table
        self._project = settings.gcp_project_id
        self._location = settings.bq_location
        self._job_timeout_ms = settings.bq_job_timeout_ms

    @cached_property
    def _client_or_reason(self) -> bigquery.Client | str:
        """The client, created on first use, or the reason BigQuery is unavailable."""
        if not self._project:
            return "GCP_PROJECT_ID is not set."
        try:
            credentials, _ = google.auth.default()
        except DefaultCredentialsError:
            return "No Google Cloud credentials found (Application Default Credentials)."
        return bigquery.Client(
            project=self._project, location=self._location, credentials=credentials
        )

    @property
    def _client(self) -> bigquery.Client:
        client = self._client_or_reason
        if isinstance(client, str):
            raise DatabaseUnavailableError(f"BigQuery is unavailable: {client}")
        return client

    def availability(self) -> tuple[bool, str | None]:
        client = self._client_or_reason
        return (False, client) if isinstance(client, str) else (True, None)

    def count(self) -> int:
        # Iterating the rows can make API calls too, hence the wrapper around it.
        with _unavailable_on_transport_errors():
            rows = self._run(f"SELECT COUNT(*) FROM `{self.table}`")
            return next(iter(rows))[0]

    def page(self, limit: int, offset: int) -> list[Customer]:
        with _unavailable_on_transport_errors():
            rows = self._run(
                f"SELECT id, name, email, country, plan FROM `{self.table}` "
                "ORDER BY id LIMIT @limit OFFSET @offset",
                [
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                    bigquery.ScalarQueryParameter("offset", "INT64", offset),
                ],
            )
            return [Customer(**dict(row.items())) for row in rows]

    def reset(self) -> int:
        self._run(
            f"CREATE OR REPLACE TABLE `{self.table}` "
            "(id INT64, name STRING, email STRING, country STRING, plan STRING)"
        )

        values: list[str] = []
        params: list[bigquery.ScalarQueryParameter] = []
        for row_id, row in enumerate(SEED_ROWS, start=1):
            values.append(f"(@id{row_id}, " + ", ".join(f"@{c}{row_id}" for c in COLUMNS) + ")")
            params.append(bigquery.ScalarQueryParameter(f"id{row_id}", "INT64", row_id))
            params += [
                bigquery.ScalarQueryParameter(f"{column}{row_id}", "STRING", getattr(row, column))
                for column in COLUMNS
            ]
        self._run(
            f"INSERT INTO `{self.table}` (id, {', '.join(COLUMNS)}) VALUES {', '.join(values)}",
            params,
        )
        return self.count()

    def seed_if_empty(self) -> None:
        try:
            empty = self.count() == 0
        except NotFound:
            empty = True
        if empty:
            self.reset()

    def execute(self, statement: StatementPreview) -> Execution:
        params = [
            bigquery.ScalarQueryParameter(
                param.placeholder.removeprefix("@"), "STRING", param.value
            )
            for param in statement.params
        ]
        # Auth/transport failures raise DatabaseUnavailableError (HTTP 503): they are not a
        # result of the demo SQL.
        try:
            job = self._query(statement.sql, params)
            self._wait(job)
        except TimeoutError:
            error = f"Cancelled: the query ran longer than {self._job_timeout_ms} ms."
            return Execution(False, None, self._count_or_none(), error)
        except GoogleAPIError as exc:
            error = _error_message(exc, self._project)
            return Execution(False, None, self._count_or_none(), error)
        return Execution(True, self._rows_affected(job), self._count_or_none())

    def _query(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> bigquery.QueryJob:
        """Start a query job (raises DatabaseUnavailableError if the API cannot be reached)."""
        config = bigquery.QueryJobConfig(
            query_parameters=params or [],
            maximum_bytes_billed=_MAX_BYTES_BILLED,
            job_timeout_ms=self._job_timeout_ms,
        )
        with _unavailable_on_transport_errors():
            return self._client.query(sql, job_config=config)

    def _wait(self, job: bigquery.QueryJob) -> RowIterator:
        """Wait for the job's result, cancelling the job if the wait times out.

        BigQuery itself fails the job after ``job_timeout_ms``; the client waits a little longer
        so that normally wins, and cancels the job if it is somehow still running.
        """
        try:
            with _unavailable_on_transport_errors():
                return job.result(timeout=self._job_timeout_ms / 1000 + _WAIT_MARGIN_S)
        except TimeoutError:
            with suppress(GoogleAPIError, *_UNAVAILABLE_ERRORS):
                job.cancel()
            raise

    def _run(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> RowIterator:
        return self._wait(self._query(sql, params))

    def _count_or_none(self) -> int | None:
        try:
            return self.count()
        except (GoogleAPIError, TimeoutError, DatabaseUnavailableError):
            return None

    def _rows_affected(self, job: bigquery.QueryJob) -> int | None:
        """Rows changed by the job. A multi-statement query runs as a script whose parent job
        reports no DML count, so add up its child jobs (null if they cannot be listed)."""
        if job.num_dml_affected_rows is not None:
            return job.num_dml_affected_rows
        if job.statement_type != "SCRIPT":
            return None
        try:
            counts = [
                child.num_dml_affected_rows
                for child in self._client.list_jobs(parent_job=job)
                if isinstance(child, bigquery.QueryJob) and child.num_dml_affected_rows is not None
            ]
        except (GoogleAPIError, *_UNAVAILABLE_ERRORS):
            return None
        return sum(counts) if counts else None


@contextmanager
def _unavailable_on_transport_errors() -> Iterator[None]:
    try:
        yield
    except _UNAVAILABLE_ERRORS as exc:
        # The original message is not passed on: it can name the project or service account.
        raise DatabaseUnavailableError(
            "BigQuery is unavailable: could not authenticate or reach the API."
        ) from exc


def _error_message(exc: Exception, project: str) -> str:
    """The database's own message, without the job id, location, query dump, project id or
    service account email (this is a public demo)."""
    errors = getattr(exc, "errors", None)
    if errors and isinstance(errors[0], dict) and errors[0].get("message"):
        message = str(errors[0]["message"])
    else:
        message = getattr(exc, "message", None) or str(exc)
    message = _SERVICE_ACCOUNT.sub("<service-account>", message)
    return message.replace(project, "<project>") if project else message
