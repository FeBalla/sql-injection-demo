"""What really reaches Postgres, captured from psycopg while the demo INSERT runs.

The preview must show exactly this. Private psycopg attributes are read here, in tests only:
``cursor._query`` is the query as psycopg converted and sent it, with ``.query`` the SQL bytes
and ``.params`` the values sent separately (None when no parameters were given, in which case
psycopg uses the simple query protocol).
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import psycopg
import pytest
from sqlalchemy import Connection, event
from sqlalchemy.exc import ProgrammingError

from app.sql_injection.models import CustomerIn
from app.sql_injection.queries.postgres import insert_customer_concatenated
from app.sql_injection.repositories.customer_repository import PostgresCustomerRepository

from ..samples import APOSTROPHE, PLACEHOLDER_LOOKALIKES, build, malicious


@dataclass(frozen=True)
class Sent:
    cursor_type: type
    sql: str
    params: list[bytes] | None


@pytest.fixture
def sent(postgres: PostgresCustomerRepository) -> Iterator[list[Any]]:
    """The cursors of everything the repository's engine runs while the test runs. They are read
    afterwards, so statements that fail (no ``after_cursor_execute``) are captured too."""
    cursors: list[Any] = []

    def capture(_conn: Connection, cursor: Any, *_: Any) -> None:
        cursors.append(cursor)

    assert postgres.engine is not None
    event.listen(postgres.engine, "before_cursor_execute", capture)
    yield cursors
    event.remove(postgres.engine, "before_cursor_execute", capture)


def sent_insert(cursors: list[Any]) -> Sent:
    """What psycopg sent for the INSERT (it is followed by a COUNT(*))."""
    sent = []
    for cursor in cursors:
        query = cursor._query
        params = None if query.params is None else [bytes(value) for value in query.params]
        sent.append(Sent(type(cursor), query.query.decode(), params))
    inserts = [statement for statement in sent if statement.sql.startswith("INSERT")]
    assert len(inserts) == 1
    return inserts[0]


ROWS = [APOSTROPHE, malicious("public.customers"), PLACEHOLDER_LOOKALIKES]


@pytest.mark.parametrize("parameterized", [True, False])
@pytest.mark.parametrize("row", ROWS)
def test_postgres_receives_exactly_the_previewed_sql(
    postgres: PostgresCustomerRepository, sent: list[Any], row: CustomerIn, parameterized: bool
) -> None:
    preview = build("postgres", row, parameterized)
    postgres.insert(row, parameterized=parameterized)
    assert sent_insert(sent).sql == preview.sql


def test_parameterized_values_are_bound_server_side(
    postgres: PostgresCustomerRepository, sent: list[Any]
) -> None:
    """SQLAlchemy's psycopg dialect uses psycopg's default Cursor (not ClientCursor): the SQL
    keeps ``$1..$4`` and the values travel separately (extended query protocol)."""
    preview = build("postgres", APOSTROPHE, parameterized=True)
    postgres.insert(APOSTROPHE, parameterized=True)
    insert = sent_insert(sent)
    assert insert.cursor_type is psycopg.Cursor
    assert insert.sql == (
        "INSERT INTO customers (name, email, country, plan)\nVALUES ($1, $2, $3, $4);"
    )
    assert insert.params == [param.value.encode() for param in preview.params]


@pytest.mark.parametrize("row", ROWS)
def test_concatenated_sql_is_sent_without_parameters(
    postgres: PostgresCustomerRepository, sent: list[Any], row: CustomerIn
) -> None:
    """No parameters reach psycopg, so it neither parses `%` placeholders nor uses the extended
    protocol: the simple query protocol runs every statement in the text."""
    postgres.insert(row, parameterized=False)
    insert = sent_insert(sent)
    assert insert.cursor_type is psycopg.Cursor
    assert insert.params is None


def test_why_the_demo_connection_sends_sql_without_parameters(
    postgres: PostgresCustomerRepository,
) -> None:
    """On a default connection, ``exec_driver_sql`` hands psycopg an empty parameter dict, so
    psycopg parses `%` in the text as placeholders. The repository's demo connection sets
    ``no_parameters=True`` so the text reaches Postgres exactly as built."""
    assert postgres.engine is not None
    with (
        postgres.engine.connect() as conn,
        pytest.raises(ProgrammingError, match="placeholder"),
    ):
        insert_customer_concatenated(conn, PLACEHOLDER_LOOKALIKES)
