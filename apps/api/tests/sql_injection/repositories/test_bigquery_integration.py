"""Integration tests against BigQuery, on a scratch ``customers_test`` table (see conftest)."""

import pytest

from app.sql_injection.repositories.bigquery import (
    BigQueryCustomerRepository,
)

from ..samples import APOSTROPHE, build, malicious

pytestmark = pytest.mark.bigquery


def test_reset_restores_the_seed_rows(bq: BigQueryCustomerRepository) -> None:
    assert bq.count() == 12
    assert [row.id for row in bq.page(50, 0)] == list(range(1, 13))


def test_parameterized_insert_stores_apostrophe_literally(bq: BigQueryCustomerRepository) -> None:
    result = bq.insert(APOSTROPHE, parameterized=True)
    assert result.ok, result.error
    assert result.total_rows == 13
    last = bq.page(1, 12)[0]
    assert (last.id, last.name) == (13, APOSTROPHE.name)


def test_concatenated_apostrophe_is_a_syntax_error(bq: BigQueryCustomerRepository) -> None:
    result = bq.insert(APOSTROPHE, parameterized=False)
    assert not result.ok
    assert result.error
    assert result.total_rows == 12


def test_concatenated_malicious_input_deletes_every_row(bq: BigQueryCustomerRepository) -> None:
    row = malicious(bq.table)
    assert build("bigquery", row, parameterized=False).statement_count == 3
    result = bq.insert(row, parameterized=False)
    assert result.ok, result.error
    assert result.total_rows == 0


def test_parameterized_malicious_input_is_stored_literally(bq: BigQueryCustomerRepository) -> None:
    row = malicious(bq.table)
    result = bq.insert(row, parameterized=True)
    assert result.ok, result.error
    assert result.total_rows == 13
    assert bq.page(1, 12)[0].plan == row.plan
