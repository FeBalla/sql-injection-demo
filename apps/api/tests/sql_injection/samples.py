"""Demo inputs from the shared contract, and helpers to build and inspect their previews."""

from app.sql_injection.models import CustomerIn, Db
from app.sql_injection.preview import StatementPreview, bigquery_preview, postgres_preview

APOSTROPHE = CustomerIn(
    name="Bernardo O'Higgins", email="bohiggins@example.cl", country="CL", plan="pro"
)
PLAIN_ROW = CustomerIn(name="Ana Pérez", email="aperez@example.cl", country="CL", plan="free")
PLACEHOLDER_LOOKALIKES = CustomerIn(
    name="100% :name %(x)s %s ::text", email="a:b@c", country="$1 ?", plan="pro"
)
"""Harmless input that looks like driver/SQLAlchemy placeholders: must stay plain SQL text."""


def malicious(table: str) -> CustomerIn:
    """The malicious example: deletes every row of ``table``."""
    return CustomerIn(
        name="Mallory",
        email="mallory@example.com",
        country="CL",
        plan=f"free'); DELETE FROM {table} WHERE TRUE; SELECT ('",
    )


BIGQUERY_TABLE = "injection_lab.customers"
"""The BigQuery demo table as the INSERT writes it (Postgres's is fixed: ``customers``)."""


def build(db: Db, row: CustomerIn, parameterized: bool) -> StatementPreview:
    if db == "postgres":
        return postgres_preview(row, parameterized)
    return bigquery_preview(row, parameterized, table=BIGQUERY_TABLE)


def segments(statement: StatementPreview, line: int) -> list[tuple[str, str]]:
    return [(segment.text, segment.kind) for segment in statement.lines[line]]
