"""BigQuery (google-cloud-bigquery), authenticated with Application Default Credentials.

Paging, counting and reset are plain queries on the ``customers`` table. The demo INSERT comes
from ``queries/bigquery.py``; this module only runs it within the demo's limits. Every job is
capped by the client's default job config (see ``app.core.bigquery``).
"""

from functools import cached_property

from google.api_core.exceptions import GoogleAPIError, NotFound
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

from app.core.bigquery import (
    create_bigquery_client,
    redacted_error_message,
    rows_affected,
    unavailable_on_transport_errors,
    wait_for_result,
)
from app.core.config import Settings
from app.core.errors import DatabaseUnavailableError

from ..models import COLUMNS, Customer, CustomerIn
from ..queries.bigquery import insert_customer_concatenated, insert_customer_parameterized
from ..seed_data import SEED_ROWS
from .protocol import Execution


class BigQueryCustomerRepository:
    def __init__(self, settings: Settings) -> None:
        self.table = f"{settings.bq_dataset}.{settings.bq_table}"
        self._settings = settings
        self._project = settings.gcp_project_id
        self._job_timeout_ms = settings.bq_job_timeout_ms

    @cached_property
    def _client_or_reason(self) -> bigquery.Client | str:
        """The client, created on first use, or the reason BigQuery is unavailable."""
        return create_bigquery_client(self._settings)

    @property
    def _client(self) -> bigquery.Client:
        client = self._client_or_reason
        if isinstance(client, str):
            raise DatabaseUnavailableError(f"BigQuery is unavailable: {client}")
        return client

    def unavailable_reason(self) -> str | None:
        client = self._client_or_reason
        return client if isinstance(client, str) else None

    def count(self) -> int:
        # Iterating the rows can make API calls too, hence the wrapper around it.
        with unavailable_on_transport_errors():
            rows = self._run(f"SELECT COUNT(*) FROM `{self.table}`")
            return next(iter(rows))[0]

    def is_empty(self) -> bool:
        try:
            return self.count() == 0
        except NotFound:
            return True

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
        self._run(*_seed_insert(self.table))
        return self.count()

    def insert(self, customer: CustomerIn, *, parameterized: bool) -> Execution:
        insert_customer = (
            insert_customer_parameterized if parameterized else insert_customer_concatenated
        )
        # Auth/transport failures raise DatabaseUnavailableError (HTTP 503): they are not a
        # result of the demo SQL.
        try:
            with unavailable_on_transport_errors():
                job = insert_customer(self._client, self.table, customer)
            wait_for_result(job, job_timeout_ms=self._job_timeout_ms)
        except TimeoutError:
            error = f"Cancelled: the query ran longer than {self._job_timeout_ms} ms."
            return Execution(False, None, self._count_or_none(), error)
        except GoogleAPIError as exc:
            error = redacted_error_message(exc, self._project)
            return Execution(False, None, self._count_or_none(), error)
        return Execution(True, rows_affected(self._client, job), self._count_or_none())

    def _run(
        self, sql: str, params: list[bigquery.ScalarQueryParameter] | None = None
    ) -> RowIterator:
        job_config = bigquery.QueryJobConfig(query_parameters=params or [])
        with unavailable_on_transport_errors():
            job = self._client.query(sql, job_config=job_config)
        return wait_for_result(job, job_timeout_ms=self._job_timeout_ms)

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
