"""BigQuery behind the demo: the customers table's queries, reset and statement execution."""

from functools import cached_property

import google.auth
from google.api_core.exceptions import GoogleAPIError, NotFound
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

from app.config import Settings

from ...schemas import COLUMNS, Customer, Db, StatementPreview
from ...seed_data import SEED_ROWS
from ..protocol import DatabaseUnavailableError, Execution
from .errors import redacted_error_message, unavailable_on_transport_errors
from .jobs import rows_affected, start_query, wait_for_result


class BigQueryDatabase:
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
        with unavailable_on_transport_errors():
            rows = self._run(f"SELECT COUNT(*) FROM `{self.table}`")
            return next(iter(rows))[0]

    def page(self, limit: int, offset: int) -> list[Customer]:
        with unavailable_on_transport_errors():
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
        sql, params = _seed_insert(self.table)
        self._run(sql, params)
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
            job = self._start(statement.sql, params)
            wait_for_result(job, job_timeout_ms=self._job_timeout_ms)
        except TimeoutError:
            error = f"Cancelled: the query ran longer than {self._job_timeout_ms} ms."
            return Execution(False, None, self._count_or_none(), error)
        except GoogleAPIError as exc:
            error = redacted_error_message(exc, self._project)
            return Execution(False, None, self._count_or_none(), error)
        return Execution(True, rows_affected(self._client, job), self._count_or_none())

    def _start(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> bigquery.QueryJob:
        return start_query(self._client, sql, params, job_timeout_ms=self._job_timeout_ms)

    def _run(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> RowIterator:
        return wait_for_result(self._start(sql, params), job_timeout_ms=self._job_timeout_ms)

    def _count_or_none(self) -> int | None:
        try:
            return self.count()
        except (GoogleAPIError, TimeoutError, DatabaseUnavailableError):
            return None


def _seed_insert(table: str) -> tuple[str, list[bigquery.ScalarQueryParameter]]:
    """One INSERT of every seed row with ids 1..12, all values as query parameters."""
    values: list[str] = []
    params: list[bigquery.ScalarQueryParameter] = []
    for row_id, row in enumerate(SEED_ROWS, start=1):
        values.append(f"(@id{row_id}, " + ", ".join(f"@{c}{row_id}" for c in COLUMNS) + ")")
        params.append(bigquery.ScalarQueryParameter(f"id{row_id}", "INT64", row_id))
        params += [
            bigquery.ScalarQueryParameter(f"{column}{row_id}", "STRING", getattr(row, column))
            for column in COLUMNS
        ]
    sql = f"INSERT INTO `{table}` (id, {', '.join(COLUMNS)}) VALUES {', '.join(values)}"
    return sql, params
