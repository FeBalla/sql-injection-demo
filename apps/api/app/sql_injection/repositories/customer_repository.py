"""Postgres (SQLAlchemy Core over psycopg 3), connected as the least-privilege ``lab_app`` role.

Paging, counting and reset are plain Core statements on the ``customers`` table. The demo INSERT
comes from ``queries/postgres.py``; this module only runs it within the demo's safety limits.
"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from typing import Any

import psycopg
from sqlalchemy import Connection, Engine, event, func, insert, select, text
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.config import Settings
from app.core.database import DatabaseUnavailableError, create_postgres_engine

from ..models import Customer, CustomerIn, customers
from ..queries.postgres import insert_customer_concatenated, insert_customer_parameterized
from ..seed_data import SEED_ROWS
from .protocol import Execution


class PostgresCustomerRepository:
    table = customers.fullname

    def __init__(self, settings: Settings) -> None:
        self.engine: Engine | None = create_postgres_engine(settings)
        self._statement_timeout_ms = settings.statement_timeout_ms

    def unavailable_reason(self) -> str | None:
        return None if self.engine is not None else "DATABASE_URL is not set."

    def count(self) -> int:
        with self._connect() as conn:
            return _count(conn)

    def is_empty(self) -> bool:
        return self.count() == 0

    def page(self, limit: int, offset: int) -> list[Customer]:
        query = select(customers).order_by(customers.c.id).limit(limit).offset(offset)
        with self._connect() as conn:
            return [Customer(**row) for row in conn.execute(query).mappings()]

    def reset(self) -> int:
        with self._connect() as conn, conn.begin():
            # The app role does not own the table on purpose (so injected SQL cannot DROP or
            # ALTER it), which also rules out TRUNCATE ... RESTART IDENTITY. It was granted
            # TRUNCATE on the table and UPDATE on the id sequence, so restart ids with setval().
            conn.execute(text(f"TRUNCATE {customers.fullname}"))
            sequence = func.pg_get_serial_sequence(customers.fullname, "id")
            conn.execute(select(func.setval(sequence, 1, False)))
            conn.execute(insert(customers), [row.model_dump() for row in SEED_ROWS])
            return _count(conn)

    def insert(self, customer: CustomerIn, *, parameterized: bool) -> Execution:
        insert_customer = (
            insert_customer_parameterized if parameterized else insert_customer_concatenated
        )
        with self._connect() as conn:
            # Like a SQL console: every request is its own transaction (autocommit), and SQL
            # without parameters reaches psycopg as-is (no `%` placeholder parsing). psycopg then
            # uses the simple query protocol, which runs every `;`-separated statement in it.
            conn.execution_options(isolation_level="AUTOCOMMIT", no_parameters=True)
            try:
                with (
                    _cancel_after(self._statement_timeout_ms, conn) as timed_out,
                    _rows_affected(conn) as counts,
                ):
                    insert_customer(conn, customer)
            except DBAPIError as exc:
                error = self._timeout_error() if timed_out.is_set() else _error_message(exc)
                return Execution(False, None, _count_or_none(conn), error)
            rows_affected = sum(counts) if counts else None
            return Execution(True, rows_affected, _count_or_none(conn))

    def _timeout_error(self) -> str:
        return f"Cancelled: the statement ran longer than {self._statement_timeout_ms} ms."

    @contextmanager
    def _connect(self) -> Iterator[Connection]:
        if self.engine is None:
            raise DatabaseUnavailableError("Postgres is unavailable: DATABASE_URL is not set.")
        try:
            conn = self.engine.connect()
        except OperationalError as exc:
            raise DatabaseUnavailableError("Postgres is unreachable.") from exc
        with conn:
            yield conn


@contextmanager
def _cancel_after(timeout_ms: int, conn: Connection) -> Iterator[threading.Event]:
    """Cancel whatever ``conn`` is running once ``timeout_ms`` pass; the event tells if it did.

    statement_timeout is only a session default: the executed SQL can raise or disable it
    (`SET statement_timeout = 0; ...`). This client-side watchdog cancels the run after the same
    time limit regardless of what the SQL did to its session.
    """
    driver_connection = conn.connection.driver_connection
    assert isinstance(driver_connection, psycopg.Connection)
    timed_out = threading.Event()

    def cancel() -> None:
        timed_out.set()
        with suppress(psycopg.Error):
            driver_connection.cancel_safe()

    watchdog = threading.Timer(timeout_ms / 1000, cancel)
    watchdog.start()
    try:
        yield timed_out
    finally:
        watchdog.cancel()


@contextmanager
def _rows_affected(conn: Connection) -> Iterator[list[int]]:
    """Collect the row count of every non-query statement that ``conn`` runs meanwhile.

    Concatenated input can append statements, but SQLAlchemy only reports the first one's
    rowcount (and closes the cursor), so read them all from the DBAPI cursor right away.
    """
    counts: list[int] = []

    def collect(_conn: Connection, cursor: Any, *_: Any) -> None:
        while True:
            if cursor.description is None and cursor.rowcount >= 0:
                counts.append(cursor.rowcount)
            if not cursor.nextset():
                return

    event.listen(conn, "after_cursor_execute", collect)
    try:
        yield counts
    finally:
        event.remove(conn, "after_cursor_execute", collect)


def _count(conn: Connection) -> int:
    return conn.execute(select(func.count()).select_from(customers)).scalar_one()


def _count_or_none(conn: Connection) -> int | None:
    try:
        return _count(conn)
    except DBAPIError:
        return None


def _error_message(exc: DBAPIError) -> str:
    if isinstance(exc.orig, psycopg.Error):
        return exc.orig.diag.message_primary or str(exc.orig)
    return str(exc.orig or exc)
