"""Integration tests against BigQuery, on a scratch ``customers_test`` table.

Skipped unless GCP_PROJECT_ID is set and Application Default Credentials are available.
"""

from collections.abc import Iterator

import pytest

from app.config import Settings
from app.modules.sql_injection.databases.bigquery.database import BigQueryDatabase
from app.modules.sql_injection.schemas import CustomerIn, StatementPreview
from app.modules.sql_injection.statements.builder import build_statement

from .samples import APOSTROPHE, malicious

pytestmark = pytest.mark.bigquery


def statement(database: BigQueryDatabase, row: CustomerIn, parameterized: bool) -> StatementPreview:
    return build_statement(database.id, row, parameterized, database.statement_table)


@pytest.fixture(scope="module")
def bigquery() -> Iterator[BigQueryDatabase]:
    """A scratch ``customers_test`` table in the configured dataset, dropped afterwards."""
    database = BigQueryDatabase(Settings(bq_table="customers_test"))
    available, reason = database.availability()
    if not available:
        pytest.skip(f"BigQuery unavailable: {reason}")
    try:
        yield database
    finally:
        client = database._client_or_reason
        assert not isinstance(client, str)
        client.query(f"DROP TABLE IF EXISTS `{database.table}`").result(timeout=60)


@pytest.fixture
def bq(bigquery: BigQueryDatabase) -> BigQueryDatabase:
    assert bigquery.table.endswith(".customers_test")
    bigquery.reset()
    return bigquery


def test_reset_restores_the_seed_rows(bq: BigQueryDatabase) -> None:
    assert bq.count() == 12
    assert [row.id for row in bq.page(50, 0)] == list(range(1, 13))


def test_parameterized_insert_stores_apostrophe_literally(bq: BigQueryDatabase) -> None:
    result = bq.execute(statement(bq, APOSTROPHE, parameterized=True))
    assert result.ok, result.error
    assert result.total_rows == 13
    last = bq.page(1, 12)[0]
    assert (last.id, last.name) == (13, APOSTROPHE.name)


def test_concatenated_apostrophe_is_a_syntax_error(bq: BigQueryDatabase) -> None:
    result = bq.execute(statement(bq, APOSTROPHE, parameterized=False))
    assert not result.ok
    assert result.error
    assert result.total_rows == 12


def test_concatenated_malicious_input_deletes_every_row(bq: BigQueryDatabase) -> None:
    preview = statement(bq, malicious(bq.table), parameterized=False)
    assert preview.statement_count == 3
    result = bq.execute(preview)
    assert result.ok, result.error
    assert result.total_rows == 0


def test_parameterized_malicious_input_is_stored_literally(bq: BigQueryDatabase) -> None:
    row = malicious(bq.table)
    result = bq.execute(statement(bq, row, parameterized=True))
    assert result.ok, result.error
    assert result.total_rows == 13
    assert bq.page(1, 12)[0].plan == row.plan
