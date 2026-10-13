"""Request and response models of the SQL injection API (see the shared contract)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

Db = Literal["postgres", "bigquery"]
Column = Literal["name", "email", "country", "plan"]
SegmentKind = Literal["keyword", "plain", "string", "param", "input", "escaped"]

COLUMNS: tuple[Column, ...] = ("name", "email", "country", "plan")

FieldValue = Annotated[str, Field(max_length=500)]


class CustomerIn(BaseModel):
    name: FieldValue
    email: FieldValue
    country: FieldValue
    plan: FieldValue


class Customer(BaseModel):
    id: int
    name: str
    email: str
    country: str
    plan: str


class CustomerPage(BaseModel):
    rows: list[Customer]
    total: int
    page: int
    page_size: int


class DatabaseInfo(BaseModel):
    id: Db
    label: str
    table: str
    available: bool
    reason: str | None


class ResetResult(BaseModel):
    total: int


class StatementRequest(BaseModel):
    row: CustomerIn
    parameterized: bool


class Segment(BaseModel):
    text: str
    kind: SegmentKind


class BoundParam(BaseModel):
    placeholder: str
    column: Column
    type: Literal["text", "STRING"]
    value: str


class StatementPreview(BaseModel):
    database: Db
    parameterized: bool
    sql: str
    """The exact text sent to the database."""
    lines: list[list[Segment]]
    params: list[BoundParam]
    statement_count: int
    escaped_fields: list[Column]


class InsertResult(BaseModel):
    ok: bool
    statement: StatementPreview
    rows_affected: int | None
    total_rows: int | None
    error: str | None
