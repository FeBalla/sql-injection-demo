"""Postgres backend (psycopg 3), connected as the least-privilege ``lab_app`` role."""

import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress

import psycopg
from psycopg.rows import dict_row

from app.config import Settings

from ..schemas import COLUMNS, Customer, Db, StatementPreview
from ..seed import SEED_ROWS
from .base import DatabaseUnavailableError, Execution

_TABLE = "public.customers"


class PostgresBackend:
    id: Db = "postgres"
    label = "Postgres"
    table = _TABLE
    statement_table = "customers"

    def __init__(self, settings: Settings) -> None:
        self._url = settings.database_url
        self._statement_timeout_ms = settings.statement_timeout_ms

    def availability(self) -> tuple[bool, str | None]:
        return (True, None) if self._url else (False, "DATABASE_URL is not set.")

    def count(self) -> int:
        with self._connect() as conn:
            return _count(conn)

    def page(self, limit: int, offset: int) -> list[Customer]:
        with self._connect() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"SELECT id, name, email, country, plan FROM {_TABLE} "
                "ORDER BY id LIMIT $1 OFFSET $2",
                [limit, offset],
            )
            return [Customer(**row) for row in cur.fetchall()]

    def reset(self) -> int:
        with self._connect() as conn, conn.transaction(), conn.cursor() as cur:
            # The app role does not own the table on purpose (so injected SQL cannot DROP or
            # ALTER it), which also rules out TRUNCATE ... RESTART IDENTITY. It was granted
            # TRUNCATE on the table and UPDATE on the id sequence, so restart ids with setval().
            cur.execute(f"TRUNCATE {_TABLE}")
            cur.execute(f"SELECT setval(pg_get_serial_sequence('{_TABLE}', 'id'), 1, false)")
            cur.executemany(
                f"INSERT INTO {_TABLE} ({', '.join(COLUMNS)}) VALUES ($1, $2, $3, $4)",
                [[getattr(row, column) for column in COLUMNS] for row in SEED_ROWS],
            )
            return _count(conn)

    def seed_if_empty(self) -> None:
        if self.count() == 0:
            self.reset()

    def execute(self, statement: StatementPreview) -> Execution:
        # Parameterized: RawCursor sends the `$1..$4` text unchanged and binds the values
        # server-side (extended protocol). Concatenated: no params, so psycopg uses the simple
        # query protocol, which runs every `;`-separated statement in the text (as the attack
        # needs). Autocommit makes each request its own transaction.
        params = [param.value for param in statement.params] if statement.parameterized else None
        with self._connect() as conn:
            # statement_timeout is only a session default: the executed SQL can raise or disable
            # it (`SET statement_timeout = 0; ...`). This client-side watchdog cancels the run
            # after the same time limit regardless of what the SQL did to its session.
            timed_out = threading.Event()

            def cancel() -> None:
                timed_out.set()
                with suppress(psycopg.Error):
                    conn.cancel_safe()

            watchdog = threading.Timer(self._statement_timeout_ms / 1000, cancel)
            watchdog.start()
            try:
                with conn.cursor() as cur:
                    cur.execute(statement.sql, params)
                    rows_affected = _rows_affected(cur)
            except psycopg.Error as exc:
                error = self._timeout_error() if timed_out.is_set() else _error_message(exc)
            else:
                error = None
            finally:
                watchdog.cancel()
            if error is not None:
                return Execution(False, None, _count_or_none(conn), error)
            return Execution(True, rows_affected, _count_or_none(conn))

    def _timeout_error(self) -> str:
        return f"Cancelled: the statement ran longer than {self._statement_timeout_ms} ms."

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection]:
        try:
            conn = psycopg.connect(
                self._url,
                autocommit=True,
                cursor_factory=psycopg.RawCursor,
                connect_timeout=5,
                options=f"-c statement_timeout={self._statement_timeout_ms}",
            )
        except psycopg.OperationalError as exc:
            raise DatabaseUnavailableError("Postgres is unreachable.") from exc
        with conn:
            yield conn


def _count(conn: psycopg.Connection) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {_TABLE}").fetchone()
    assert row is not None
    return row[0]


def _count_or_none(conn: psycopg.Connection) -> int | None:
    try:
        return _count(conn)
    except psycopg.Error:
        return None


def _rows_affected(cur: psycopg.Cursor) -> int | None:
    """Sum the row counts of every non-query statement in the (possibly multi-statement) run."""
    total: int | None = None
    while True:
        if cur.description is None and cur.rowcount >= 0:
            total = (total or 0) + cur.rowcount
        if not cur.nextset():
            return total


def _error_message(exc: psycopg.Error) -> str:
    return exc.diag.message_primary or str(exc)
