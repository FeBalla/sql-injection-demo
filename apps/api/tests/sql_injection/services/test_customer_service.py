"""Unit tests for the use cases, with an in-memory repository (no database needed)."""

from dataclasses import dataclass, field

from app.sql_injection.models import Customer, CustomerIn
from app.sql_injection.preview.builder import postgres_preview
from app.sql_injection.repositories.protocol import Execution
from app.sql_injection.services.customer_service import CustomerService

from ..samples import APOSTROPHE, PLAIN_ROW


@dataclass
class FakeRepository:
    rows: list[Customer] = field(default_factory=list)
    table: str = "public.customers"
    resets: int = 0
    inserts: list[tuple[CustomerIn, bool]] = field(default_factory=list)

    def unavailable_reason(self) -> str | None:
        return None

    def count(self) -> int:
        return len(self.rows)

    def page(self, limit: int, offset: int) -> list[Customer]:
        return self.rows[offset : offset + limit]

    def is_empty(self) -> bool:
        return not self.rows

    def reset(self) -> int:
        self.resets += 1
        self.rows = [Customer(id=i, **PLAIN_ROW.model_dump()) for i in range(1, 13)]
        return len(self.rows)

    def insert(self, customer: CustomerIn, *, parameterized: bool) -> Execution:
        self.inserts.append((customer, parameterized))
        return Execution(True, 1, len(self.rows) + 1)


def service_with(repository: FakeRepository) -> CustomerService:
    return CustomerService("postgres", "Postgres", repository, postgres_preview)


def test_list_page_is_one_based() -> None:
    repository = FakeRepository()
    repository.reset()
    rows, total = service_with(repository).list_page(page=3, page_size=5)
    assert [row.id for row in rows] == [11, 12]
    assert total == 12


def test_seed_if_empty_resets_only_an_empty_table() -> None:
    repository = FakeRepository()
    service = service_with(repository)
    service.seed_if_empty()
    service.seed_if_empty()
    assert repository.resets == 1


def test_insert_runs_the_previewed_statement() -> None:
    repository = FakeRepository()
    service = service_with(repository)
    statement, execution = service.insert(APOSTROPHE, parameterized=False)
    assert statement == service.preview(APOSTROPHE, parameterized=False)
    assert repository.inserts == [(APOSTROPHE, False)]
    assert execution == Execution(True, 1, 1)


def test_table_and_availability_come_from_the_repository() -> None:
    service = service_with(FakeRepository(table="dataset.table"))
    assert service.table == "dataset.table"
    assert service.unavailable_reason() is None
