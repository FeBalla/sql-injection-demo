"""The statement preview returned by the API: the exact SQL a database receives, highlighted, with
its bound values."""

from typing import Literal

from pydantic import BaseModel

from ..models import ColumnName, Db

SegmentKind = Literal["keyword", "plain", "string", "param", "input", "escaped"]
"""How the UI colors a piece of SQL. ``input`` is text typed by the user that stayed inside its
string literal, and ``escaped`` is text typed by the user that ended up outside it (now parsed
as SQL). The other kinds are ordinary syntax highlighting."""


class Segment(BaseModel):
    """A run of characters on one line that share the same color."""

    text: str
    kind: SegmentKind


class BoundParam(BaseModel):
    """A value sent separately from a parameterized statement's SQL text."""

    placeholder: str
    """How the SQL refers to it: ``$1`` (Postgres) or ``@name`` (BigQuery)."""
    column: ColumnName
    type: Literal["text", "STRING"]
    """The parameter's type in the database's own terms."""
    value: str


class StatementPreview(BaseModel):
    """What the database would receive for an INSERT, and what that does to it."""

    database: Db
    parameterized: bool
    sql: str
    """The exact text sent to the database."""
    lines: list[list[Segment]]
    """``sql`` split into lines (without the ``\\n``), each one a list of colored segments."""
    params: list[BoundParam]
    """The bound values, in placeholder order. Empty when concatenated."""
    statement_count: int
    """How many statements the database will run (more than 1 means input injected some)."""
    escaped_fields: list[ColumnName]
    """The fields whose value escaped its string literal. Always empty when parameterized."""
