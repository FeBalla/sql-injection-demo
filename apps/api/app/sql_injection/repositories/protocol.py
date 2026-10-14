"""What the service needs from each database's repository, so it treats both the same way."""

from dataclasses import dataclass
from typing import Protocol

from ..models import Customer, CustomerIn


@dataclass(frozen=True)
class Execution:
    """How running the demo INSERT went. Database errors are a result here, not an exception."""

    ok: bool
    rows_affected: int | None
    total_rows: int | None
    """COUNT(*) after the statement ran, or None if counting failed."""
    error: str | None = None


class CustomerRepository(Protocol):
    table: str
    """Table reference shown in the UI (never includes a project id)."""

    def unavailable_reason(self) -> str | None:
        """Why the database cannot be used (not configured, no credentials), or None."""
        ...

    def count(self) -> int: ...
    def page(self, limit: int, offset: int) -> list[Customer]: ...
    def is_empty(self) -> bool:
        """Whether the table has no rows (or does not exist yet)."""
        ...

    def reset(self) -> int:
        """Restore the seed rows (ids 1..12) and return the row count."""
        ...

    def insert(self, customer: CustomerIn, *, parameterized: bool) -> Execution:
        """Run the demo INSERT from ``queries/``. Database errors give ``ok=False``."""
        ...
