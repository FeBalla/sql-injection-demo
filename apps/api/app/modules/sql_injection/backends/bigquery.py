"""BigQuery backend (google-cloud-bigquery), authenticated with Application Default Credentials."""

from functools import cached_property

import google.auth
from google.api_core.exceptions import GoogleAPIError, NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery

from app.config import Settings

from ..schemas import COLUMNS, Customer, Db, StatementPreview
from ..seed import SEED_ROWS
from .base import DatabaseUnavailableError, Execution

_QUERY_TIMEOUT_S = 60
# Injected SQL runs with the project's job permissions, so cap what any single query may scan
# (e.g. a public dataset). The demo table itself is tiny.
_MAX_BYTES_BILLED = 100 * 1024 * 1024


class BigQueryBackend:
    id: Db = "bigquery"
    label = "BigQuery"

    def __init__(self, settings: Settings) -> None:
        self.table = f"{settings.bq_dataset}.{settings.bq_table}"
        self.statement_table = self.table
        self._project = settings.gcp_project_id
        self._location = settings.bq_location

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
        rows = self._query(f"SELECT COUNT(*) FROM `{self.table}`").result(timeout=_QUERY_TIMEOUT_S)
        return next(iter(rows))[0]

    def page(self, limit: int, offset: int) -> list[Customer]:
        job = self._query(
            f"SELECT id, name, email, country, plan FROM `{self.table}` "
            "ORDER BY id LIMIT @limit OFFSET @offset",
            [
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
                bigquery.ScalarQueryParameter("offset", "INT64", offset),
            ],
        )
        return [Customer(**dict(row.items())) for row in job.result(timeout=_QUERY_TIMEOUT_S)]

    def reset(self) -> int:
        self._query(
            f"CREATE OR REPLACE TABLE `{self.table}` "
            "(id INT64, name STRING, email STRING, country STRING, plan STRING)"
        ).result(timeout=_QUERY_TIMEOUT_S)

        values: list[str] = []
        params: list[bigquery.ScalarQueryParameter] = []
        for row_id, row in enumerate(SEED_ROWS, start=1):
            values.append(f"(@id{row_id}, " + ", ".join(f"@{c}{row_id}" for c in COLUMNS) + ")")
            params.append(bigquery.ScalarQueryParameter(f"id{row_id}", "INT64", row_id))
            params += [
                bigquery.ScalarQueryParameter(f"{column}{row_id}", "STRING", getattr(row, column))
                for column in COLUMNS
            ]
        self._query(
            f"INSERT INTO `{self.table}` (id, {', '.join(COLUMNS)}) VALUES {', '.join(values)}",
            params,
        ).result(timeout=_QUERY_TIMEOUT_S)
        return self.count()

    def seed_if_empty(self) -> None:
        try:
            empty = self.count() == 0
        except NotFound:
            empty = True
        if empty:
            self.reset()

    def drop(self) -> None:
        """Drop the table (used by tests that work on a scratch table)."""
        self._query(f"DROP TABLE IF EXISTS `{self.table}`").result(timeout=_QUERY_TIMEOUT_S)

    def execute(self, statement: StatementPreview) -> Execution:
        params = [
            bigquery.ScalarQueryParameter(
                param.placeholder.removeprefix("@"), "STRING", param.value
            )
            for param in statement.params
        ]
        try:
            job = self._query(statement.sql, params)
            job.result(timeout=_QUERY_TIMEOUT_S)
        except (GoogleAPIError, TimeoutError) as exc:
            return Execution(False, None, self._count_or_none(), _error_message(exc))
        return Execution(True, self._rows_affected(job), self._count_or_none())

    def _query(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> bigquery.QueryJob:
        config = bigquery.QueryJobConfig(
            query_parameters=params or [], maximum_bytes_billed=_MAX_BYTES_BILLED
        )
        return self._client.query(sql, job_config=config)

    def _count_or_none(self) -> int | None:
        try:
            return self.count()
        except (GoogleAPIError, TimeoutError):
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
        except GoogleAPIError:
            return None
        return sum(counts) if counts else None


def _error_message(exc: Exception) -> str:
    """The database's own message, without the job id, location or query dump."""
    errors = getattr(exc, "errors", None)
    if errors and isinstance(errors[0], dict) and errors[0].get("message"):
        return str(errors[0]["message"])
    return getattr(exc, "message", None) or str(exc)
