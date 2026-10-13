"""The interface shared by the two databases behind the demo."""

from dataclasses import dataclass
from typing import Protocol

from ..schemas import Customer, Db, StatementPreview


class DatabaseUnavailableError(Exception):
    """The database is not configured or cannot be reached (served as HTTP 503)."""


@dataclass(frozen=True)
class Execution:
    ok: bool
    rows_affected: int | None
    total_rows: int | None
    """COUNT(*) after the statement ran, or None if counting failed."""
    error: str | None = None


class Database(Protocol):
    id: Db
    label: str
    table: str
    """Table reference shown in the UI and usable in SQL (never includes a project id)."""
    statement_table: str
    """Table reference as written in the INSERT template."""

    def availability(self) -> tuple[bool, str | None]: ...
    def count(self) -> int: ...
    def page(self, limit: int, offset: int) -> list[Customer]: ...
    def reset(self) -> int: ...
    def seed_if_empty(self) -> None: ...
    def execute(self, statement: StatementPreview) -> Execution:
        """Run exactly ``statement.sql`` with ``statement.params``. DB errors -> ok=False."""
        ...
