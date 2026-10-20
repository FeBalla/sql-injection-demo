"""BigQuery integration fixtures: a scratch ``customers_test`` table in the configured dataset.

Skipped unless GCP_PROJECT_ID is set and Application Default Credentials are available.
"""

from collections.abc import Iterator

import pytest
from google.cloud import bigquery

from app.core.config import Settings
from app.sql_injection.repositories.bigquery import (
    BigQueryCustomerRepository,
)


@pytest.fixture(scope="session")
def bigquery_repository() -> Iterator[BigQueryCustomerRepository]:
    """The repository on the scratch table, which is dropped afterwards."""
    repository = BigQueryCustomerRepository(Settings(bq_table="customers_test"))
    reason = repository.unavailable_reason()
    if reason is not None:
        pytest.skip(f"BigQuery unavailable: {reason}")
    try:
        yield repository
    finally:
        client = _client(repository)
        client.query(f"DROP TABLE IF EXISTS `{repository.table}`").result(timeout=60)


@pytest.fixture
def bq(bigquery_repository: BigQueryCustomerRepository) -> BigQueryCustomerRepository:
    assert bigquery_repository.table.endswith(".customers_test")
    bigquery_repository.reset()
    return bigquery_repository


@pytest.fixture
def bigquery_client(bq: BigQueryCustomerRepository) -> bigquery.Client:
    """The real client the repository uses."""
    return _client(bq)


def _client(repository: BigQueryCustomerRepository) -> bigquery.Client:
    client = repository._client_or_reason
    assert isinstance(client, bigquery.Client)
    return client
