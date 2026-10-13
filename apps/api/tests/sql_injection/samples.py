"""Demo inputs from the shared contract, and helpers to build and inspect their statements."""

from app.modules.sql_injection.schemas import CustomerIn, Db, StatementPreview
from app.modules.sql_injection.statements.builder import build_statement

APOSTROPHE = CustomerIn(
    name="Bernardo O'Higgins", email="bohiggins@example.cl", country="CL", plan="pro"
)
PLAIN_ROW = CustomerIn(name="Ana Pérez", email="aperez@example.cl", country="CL", plan="free")


def malicious(table: str) -> CustomerIn:
    """The malicious example: deletes every row of ``table``."""
    return CustomerIn(
        name="Mallory",
        email="mallory@example.com",
        country="CL",
        plan=f"free'); DELETE FROM {table} WHERE TRUE; SELECT ('",
    )


STATEMENT_TABLES: dict[Db, str] = {"postgres": "customers", "bigquery": "injection_lab.customers"}
"""The demo tables as the INSERT template writes them."""


def build(db: Db, row: CustomerIn, parameterized: bool) -> StatementPreview:
    return build_statement(db, row, parameterized, STATEMENT_TABLES[db])


def segments(statement: StatementPreview, line: int) -> list[tuple[str, str]]:
    return [(segment.text, segment.kind) for segment in statement.lines[line]]
