"""Integration tests against the Postgres test database (injection_lab_test)."""

import time
from typing import Any

import psycopg
import pytest

from app.config import Settings
from app.modules.sql_injection.databases.postgres import PostgresDatabase
from app.modules.sql_injection.schemas import CustomerIn, StatementPreview
from app.modules.sql_injection.seed_data import SEED_ROWS
from app.modules.sql_injection.statements.builder import build_statement

from .samples import APOSTROPHE, malicious


def statement(database: PostgresDatabase, row: CustomerIn, parameterized: bool) -> StatementPreview:
    return build_statement(database.id, row, parameterized, database.statement_table)


def all_rows(database: PostgresDatabase) -> list[CustomerIn]:
    return [CustomerIn(**row.model_dump(exclude={"id"})) for row in database.page(50, 0)]


def test_reset_restores_the_seed_rows_with_ids_1_to_12(postgres: PostgresDatabase) -> None:
    postgres.execute(statement(postgres, APOSTROPHE, parameterized=True))
    assert postgres.reset() == 12
    rows = postgres.page(50, 0)
    assert [row.id for row in rows] == list(range(1, 13))
    assert all_rows(postgres) == list(SEED_ROWS)
    # The id sequence restarts too: the next insert gets id 13.
    postgres.execute(statement(postgres, APOSTROPHE, parameterized=True))
    assert postgres.page(1, 12)[0].id == 13


def test_parameterized_insert_stores_apostrophe_literally(postgres: PostgresDatabase) -> None:
    result = postgres.execute(statement(postgres, APOSTROPHE, parameterized=True))
    assert result.ok, result.error
    assert result.rows_affected == 1
    assert result.total_rows == 13
    assert all_rows(postgres)[-1] == APOSTROPHE


def test_concatenated_apostrophe_is_a_syntax_error(postgres: PostgresDatabase) -> None:
    result = postgres.execute(statement(postgres, APOSTROPHE, parameterized=False))
    assert not result.ok
    assert result.error is not None
    assert "syntax error" in result.error
    assert result.total_rows == 12


def test_concatenated_malicious_input_deletes_every_row(postgres: PostgresDatabase) -> None:
    preview = statement(postgres, malicious(postgres.table), parameterized=False)
    assert preview.statement_count == 3
    result = postgres.execute(preview)
    assert result.ok, result.error
    assert result.rows_affected == 1 + 13  # the INSERT, then the DELETE of all 13 rows
    assert result.total_rows == 0
    assert postgres.count() == 0


def test_parameterized_malicious_input_is_stored_literally(postgres: PostgresDatabase) -> None:
    row = malicious(postgres.table)
    result = postgres.execute(statement(postgres, row, parameterized=True))
    assert result.ok, result.error
    assert result.total_rows == 13
    assert all_rows(postgres) == [*SEED_ROWS, row]


def test_app_role_cannot_drop_the_table(
    postgres_settings: Settings, postgres: PostgresDatabase
) -> None:
    """Blast radius: even a successful injection cannot DROP the table."""
    row = malicious(postgres.table).model_copy(
        update={"plan": "free'); DROP TABLE customers; SELECT ('"}
    )
    result = postgres.execute(statement(postgres, row, parameterized=False))
    assert not result.ok
    assert result.error == "must be owner of table customers"
    assert result.total_rows == 12  # the whole multi-statement run was rolled back

    with (
        psycopg.connect(postgres_settings.database_url, autocommit=True) as conn,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        conn.execute("DROP TABLE customers")


@pytest.mark.parametrize("parameterized", [True, False])
@pytest.mark.parametrize("row", [APOSTROPHE, malicious("public.customers")])
def test_executed_sql_is_the_previewed_sql(
    postgres: PostgresDatabase,
    monkeypatch: pytest.MonkeyPatch,
    row: CustomerIn,
    parameterized: bool,
) -> None:
    sent: list[tuple[str, Any]] = []
    original = psycopg.RawCursor.execute

    def spy(self: psycopg.RawCursor, query: Any, params: Any = None, **kwargs: Any) -> Any:
        sent.append((query, params))
        return original(self, query, params, **kwargs)

    monkeypatch.setattr(psycopg.RawCursor, "execute", spy)
    preview = statement(postgres, row, parameterized)
    postgres.execute(preview)

    query, params = sent[0]  # later calls are the COUNT(*) afterwards
    assert query == preview.sql
    expected_params = [p.value for p in preview.params] if parameterized else None
    assert params == expected_params


def test_watchdog_cancels_statements_that_disable_the_timeout(
    postgres_settings: Settings, postgres: PostgresDatabase
) -> None:
    """The executed SQL can turn statement_timeout off; the client-side watchdog still fires."""
    database = PostgresDatabase(postgres_settings.model_copy(update={"statement_timeout_ms": 300}))
    row = malicious(postgres.table).model_copy(
        update={"plan": "free'); SET statement_timeout = 0; SELECT pg_sleep(30); SELECT ('"}
    )
    started = time.monotonic()
    result = database.execute(statement(database, row, parameterized=False))
    assert time.monotonic() - started < 5
    assert not result.ok
    assert result.error == "Cancelled: the statement ran longer than 300 ms."
    assert result.total_rows == 12  # the INSERT before the sleep was rolled back
