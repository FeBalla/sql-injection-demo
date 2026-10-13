"""Integration tests against BigQuery, on a scratch ``customers_test`` table.

Skipped unless GCP_PROJECT_ID is set and Application Default Credentials are available.
"""

import pytest

from app.modules.sql_injection.backends.bigquery import BigQueryBackend
from app.modules.sql_injection.schemas import CustomerIn, StatementPreview
from app.modules.sql_injection.statements import build_statement

from .samples import APOSTROPHE, malicious

pytestmark = pytest.mark.bigquery


def statement(backend: BigQueryBackend, row: CustomerIn, parameterized: bool) -> StatementPreview:
    return build_statement(backend.id, row, parameterized, backend.statement_table)


@pytest.fixture
def bq(bigquery: BigQueryBackend) -> BigQueryBackend:
    assert bigquery.table.endswith(".customers_test")
    bigquery.reset()
    return bigquery


def test_reset_restores_the_seed_rows(bq: BigQueryBackend) -> None:
    assert bq.count() == 12
    assert [row.id for row in bq.page(50, 0)] == list(range(1, 13))


def test_parameterized_insert_stores_apostrophe_literally(bq: BigQueryBackend) -> None:
    result = bq.execute(statement(bq, APOSTROPHE, parameterized=True))
    assert result.ok, result.error
    assert result.total_rows == 13
    last = bq.page(1, 12)[0]
    assert (last.id, last.name) == (13, APOSTROPHE.name)


def test_concatenated_apostrophe_is_a_syntax_error(bq: BigQueryBackend) -> None:
    result = bq.execute(statement(bq, APOSTROPHE, parameterized=False))
    assert not result.ok
    assert result.error
    assert result.total_rows == 12


def test_concatenated_malicious_input_deletes_every_row(bq: BigQueryBackend) -> None:
    preview = statement(bq, malicious(bq.table), parameterized=False)
    assert preview.statement_count == 3
    result = bq.execute(preview)
    assert result.ok, result.error
    assert result.total_rows == 0


def test_parameterized_malicious_input_is_stored_literally(bq: BigQueryBackend) -> None:
    row = malicious(bq.table)
    result = bq.execute(statement(bq, row, parameterized=True))
    assert result.ok, result.error
    assert result.total_rows == 13
    assert bq.page(1, 12)[0].plan == row.plan
