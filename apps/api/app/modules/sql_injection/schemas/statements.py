"""The INSERT statement: what the client asks for, how it is previewed and how it ran."""

from typing import Literal

from pydantic import BaseModel

from .customers import Column, CustomerIn
from .databases import Db

SegmentKind = Literal["keyword", "plain", "string", "param", "input", "escaped"]


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
