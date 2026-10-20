"""The demo's use cases, the same for Postgres and BigQuery. No HTTP and no SQL in here."""

from collections.abc import Callable
from dataclasses import dataclass

from ..models import Customer, CustomerIn, Db
from ..preview import StatementPreview
from ..repositories.protocol import CustomerRepository, Execution

BuildPreview = Callable[[CustomerIn, bool], StatementPreview]
"""Builds the preview of the INSERT for a customer, parameterized or not."""


@dataclass(frozen=True)
class CustomerService:
    db: Db
    label: str
    repository: CustomerRepository
    build_preview: BuildPreview

    @property
    def table(self) -> str:
        """Table reference shown in the UI (never includes a project id)."""
        return self.repository.table

    def unavailable_reason(self) -> str | None:
        return self.repository.unavailable_reason()

    def list_page(self, page: int, page_size: int) -> tuple[list[Customer], int]:
        """One page of customers (1-based) and the total row count."""
        rows = self.repository.page(limit=page_size, offset=(page - 1) * page_size)
        return rows, self.repository.count()

    def reset(self) -> int:
        return self.repository.reset()

    def seed_if_empty(self) -> None:
        if self.repository.is_empty():
            self.repository.reset()

    def preview(self, customer: CustomerIn, parameterized: bool) -> StatementPreview:
        return self.build_preview(customer, parameterized)

    def insert(
        self, customer: CustomerIn, parameterized: bool
    ) -> tuple[StatementPreview, Execution]:
        """Run the INSERT and return it with how it went (a database error is not raised)."""
        statement = self.preview(customer, parameterized)
        return statement, self.repository.insert(customer, parameterized=parameterized)
