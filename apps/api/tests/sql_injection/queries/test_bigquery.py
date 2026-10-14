"""What really reaches BigQuery: the query text and parameters of the jobs the INSERT starts.

The preview must show exactly this. Checked with a recording client, and (marked ``bigquery``)
against the jobs BigQuery itself reports.
"""

from typing import Any

import pytest
from google.cloud import bigquery

from app.core.config import Settings
from app.core.database import MAX_BYTES_BILLED
from app.sql_injection.models import CustomerIn
from app.sql_injection.preview.builder import bigquery_preview
from app.sql_injection.preview.statement import StatementPreview
from app.sql_injection.queries.bigquery import (
    insert_customer_concatenated,
    insert_customer_parameterized,
)
from app.sql_injection.repositories.bigquery_customer_repository import (
    BigQueryCustomerRepository,
)

from ..samples import APOSTROPHE, BIGQUERY_TABLE, PLACEHOLDER_LOOKALIKES, build, malicious

ROWS = [APOSTROPHE, malicious(BIGQUERY_TABLE), PLACEHOLDER_LOOKALIKES]


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bigquery.QueryJobConfig | None]] = []

    def query(self, sql: str, job_config: bigquery.QueryJobConfig | None = None) -> None:
        self.calls.append((sql, job_config))


def previewed_params(preview: StatementPreview) -> list[tuple[str, str, str]]:
    return [
        (param.placeholder.removeprefix("@"), param.type, param.value) for param in preview.params
    ]


def sent_params(params: Any) -> list[tuple[str, str, str]]:
    return [(param.name, param.type_, param.value) for param in params]


@pytest.mark.parametrize("row", ROWS)
def test_concatenated_job_runs_the_previewed_sql(row: CustomerIn) -> None:
    client: Any = RecordingClient()
    insert_customer_concatenated(client, BIGQUERY_TABLE, row)
    [(sql, job_config)] = client.calls
    assert sql == build("bigquery", row, parameterized=False).sql
    assert job_config is None  # no parameters (the client's default config still applies)


@pytest.mark.parametrize("row", ROWS)
def test_parameterized_job_runs_the_previewed_sql_and_params(row: CustomerIn) -> None:
    client: Any = RecordingClient()
    insert_customer_parameterized(client, BIGQUERY_TABLE, row)
    [(sql, job_config)] = client.calls
    preview = build("bigquery", row, parameterized=True)
    assert sql == preview.sql
    assert job_config is not None
    assert sent_params(job_config.query_parameters) == previewed_params(preview)


@pytest.mark.bigquery
@pytest.mark.parametrize("parameterized", [True, False])
def test_bigquery_jobs_run_the_previewed_sql_within_limits(
    bq: BigQueryCustomerRepository,
    bigquery_client: bigquery.Client,
    monkeypatch: pytest.MonkeyPatch,
    parameterized: bool,
) -> None:
    jobs: list[bigquery.QueryJob] = []
    query = bigquery_client.query

    def recording_query(*args: Any, **kwargs: Any) -> bigquery.QueryJob:
        jobs.append(query(*args, **kwargs))
        return jobs[-1]

    monkeypatch.setattr(bigquery_client, "query", recording_query)
    row = malicious(bq.table)
    result = bq.insert(row, parameterized=parameterized)
    assert result.ok, result.error

    job = jobs[0]  # then the COUNT(*)
    job.reload()  # as BigQuery reports it
    preview = bigquery_preview(row, parameterized, table=bq.table)
    assert job.query == preview.sql
    assert sent_params(job.query_parameters) == previewed_params(preview)
    assert job.maximum_bytes_billed == MAX_BYTES_BILLED
    assert int(job._properties["configuration"]["jobTimeoutMs"]) == Settings().bq_job_timeout_ms
