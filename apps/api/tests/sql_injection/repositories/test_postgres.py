"""Integration tests against the Postgres test database (injection_lab_test)."""

import time

import psycopg
import pytest

from app.core.config import Settings
from app.core.errors import DatabaseUnavailableError
from app.sql_injection.models import CustomerIn
from app.sql_injection.repositories.postgres import PostgresCustomerRepository
from app.sql_injection.seed_data import SEED_ROWS

from ..samples import APOSTROPHE, PLACEHOLDER_LOOKALIKES, build, malicious


def all_rows(repository: PostgresCustomerRepository) -> list[CustomerIn]:
    return [CustomerIn(**row.model_dump(exclude={"id"})) for row in repository.page(50, 0)]


def test_reset_restores_the_seed_rows_with_ids_1_to_12(
    postgres: PostgresCustomerRepository,
) -> None:
    postgres.insert(APOSTROPHE, parameterized=True)
    assert postgres.reset() == 12
    rows = postgres.page(50, 0)
    assert [row.id for row in rows] == list(range(1, 13))
    assert all_rows(postgres) == list(SEED_ROWS)
    # The id sequence restarts too: the next insert gets id 13.
    postgres.insert(APOSTROPHE, parameterized=True)
    assert postgres.page(1, 12)[0].id == 13


def test_parameterized_insert_stores_apostrophe_literally(
    postgres: PostgresCustomerRepository,
) -> None:
    result = postgres.insert(APOSTROPHE, parameterized=True)
    assert result.ok, result.error
    assert result.rows_affected == 1
    assert result.total_rows == 13
    assert all_rows(postgres)[-1] == APOSTROPHE


def test_concatenated_apostrophe_is_a_syntax_error(postgres: PostgresCustomerRepository) -> None:
    result = postgres.insert(APOSTROPHE, parameterized=False)
    assert not result.ok
    assert result.error is not None
    assert "syntax error" in result.error
    assert result.total_rows == 12


def test_concatenated_malicious_input_deletes_every_row(
    postgres: PostgresCustomerRepository,
) -> None:
    row = malicious(postgres.table)
    assert build("postgres", row, parameterized=False).statement_count == 3
    result = postgres.insert(row, parameterized=False)
    assert result.ok, result.error
    assert result.rows_affected == 1 + 13  # the INSERT, then the DELETE of all 13 rows
    assert result.total_rows == 0
    assert postgres.count() == 0


def test_parameterized_malicious_input_is_stored_literally(
    postgres: PostgresCustomerRepository,
) -> None:
    row = malicious(postgres.table)
    result = postgres.insert(row, parameterized=True)
    assert result.ok, result.error
    assert result.total_rows == 13
    assert all_rows(postgres) == [*SEED_ROWS, row]


@pytest.mark.parametrize("parameterized", [True, False])
def test_placeholder_lookalikes_are_stored_as_typed(
    postgres: PostgresCustomerRepository, parameterized: bool
) -> None:
    """`%` and `:` in the input are plain characters on both paths (no placeholder parsing)."""
    result = postgres.insert(PLACEHOLDER_LOOKALIKES, parameterized=parameterized)
    assert result.ok, result.error
    assert result.rows_affected == 1
    assert all_rows(postgres)[-1] == PLACEHOLDER_LOOKALIKES


def test_app_role_cannot_drop_the_table(
    postgres_settings: Settings, postgres: PostgresCustomerRepository
) -> None:
    """Blast radius: even a successful injection cannot DROP the table."""
    row = malicious(postgres.table).model_copy(
        update={"plan": "free'); DROP TABLE customers; SELECT ('"}
    )
    result = postgres.insert(row, parameterized=False)
    assert not result.ok
    assert result.error == "must be owner of table customers"
    assert result.total_rows == 12  # the whole multi-statement run was rolled back

    with (
        psycopg.connect(postgres_settings.database_url, autocommit=True) as conn,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        conn.execute("DROP TABLE customers")


def test_watchdog_cancels_statements_that_disable_the_timeout(
    postgres_settings: Settings, postgres: PostgresCustomerRepository
) -> None:
    """The executed SQL can turn statement_timeout off; the client-side watchdog still fires."""
    repository = PostgresCustomerRepository(
        postgres_settings.model_copy(update={"statement_timeout_ms": 300})
    )
    row = malicious(postgres.table).model_copy(
        update={"plan": "free'); SET statement_timeout = 0; SELECT pg_sleep(30); SELECT ('"}
    )
    started = time.monotonic()
    result = repository.insert(row, parameterized=False)
    assert time.monotonic() - started < 5
    assert not result.ok
    assert result.error == "Cancelled: the statement ran longer than 300 ms."
    assert result.total_rows == 12  # the INSERT before the sleep was rolled back


def test_session_changes_do_not_leak_into_the_next_request(
    postgres: PostgresCustomerRepository,
) -> None:
    """Every request gets a fresh session, so injected SET commands die with it."""
    row = malicious(postgres.table).model_copy(
        update={"plan": "free'); SET statement_timeout = 0; SELECT ('"}
    )
    assert postgres.insert(row, parameterized=False).ok
    assert postgres.engine is not None
    with postgres.engine.connect() as conn:
        assert conn.exec_driver_sql("SHOW statement_timeout").scalar_one() == "5s"


def test_unconfigured_or_unreachable_postgres_is_unavailable() -> None:
    unconfigured = PostgresCustomerRepository(Settings(database_url=""))
    assert unconfigured.unavailable_reason() == "DATABASE_URL is not set."

    unreachable = PostgresCustomerRepository(
        Settings(database_url="postgresql://nobody:x@127.0.0.1:1/none")
    )
    assert unreachable.unavailable_reason() is None
    with pytest.raises(DatabaseUnavailableError, match="Postgres is unreachable"):
        unreachable.count()
