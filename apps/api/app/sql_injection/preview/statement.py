"""The statement preview: the exact SQL a database receives, highlighted, with its bound values."""

from typing import Literal

from pydantic import BaseModel

from ..models import ColumnName, Db

SegmentKind = Literal["keyword", "plain", "string", "param", "input", "escaped"]


class Segment(BaseModel):
    text: str
    kind: SegmentKind


class BoundParam(BaseModel):
    placeholder: str
    column: ColumnName
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
    escaped_fields: list[ColumnName]
