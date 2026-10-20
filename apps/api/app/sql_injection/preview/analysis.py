"""Turns the SQL of a preview into what the UI shows: colored lines, the statement count and the
fields whose value escaped its string literal.

The SQL arrives as *pieces* (see :data:`Piece`), so every character is known to be template
text or part of a form field. The lexing itself is done by ``sql_syntax``; this module only
maps its results onto characters and colors.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from ..models import ColumnName, Db
from .sql_syntax import DIALECTS, KEYWORDS, Dialect, Token, count_statements, escaped_span, tokenize
from .statement import Segment, SegmentKind

Piece = tuple[str, ColumnName | None]
"""A chunk of SQL text and the form field it came from (``None`` for template text)."""


@dataclass(frozen=True)
class Analysis:
    """The parts of a :class:`StatementPreview` that come from reading its SQL."""

    lines: list[list[Segment]]
    statement_count: int
    escaped_fields: list[ColumnName]


def analyze(pieces: Sequence[Piece], db: Db) -> Analysis:
    """Analyze the SQL that ``pieces`` add up to, as ``db`` would parse it.

    1. Tokenize the whole SQL and give each character its syntax color.
    2. Recolor the characters that came from a form field: ``input``, or ``escaped`` where they
       ended up outside the string literal the template put them in.
    3. Split the colored characters into lines of segments.
    """
    dialect = DIALECTS[db]
    sql = "".join(text for text, _ in pieces)
    tokens = tokenize(sql, dialect)
    kinds = _syntax_kinds(sql, tokens)
    escaped_fields = _mark_user_input(kinds, sql, pieces, dialect)
    return Analysis(
        lines=_split_lines(sql, kinds),
        statement_count=count_statements(tokens),
        escaped_fields=escaped_fields,
    )


def _syntax_kinds(sql: str, tokens: Sequence[Token]) -> list[SegmentKind]:
    """The syntax color of every character of ``sql`` (one entry per character)."""
    kinds: list[SegmentKind] = []
    for token in tokens:
        kinds.extend([_syntax_kind(sql, token)] * (token.end - token.start))
    return kinds


def _syntax_kind(sql: str, token: Token) -> SegmentKind:
    """The color of a token: keywords, strings and parameters stand out, the rest is plain."""
    if token.kind == "word":
        return "keyword" if sql[token.start : token.end].upper() in KEYWORDS else "plain"
    if token.kind in ("string", "param"):
        return token.kind
    return "plain"


def _mark_user_input(
    kinds: list[SegmentKind], sql: str, pieces: Sequence[Piece], dialect: Dialect
) -> list[ColumnName]:
    """Recolor, in place, the characters typed by the user, and return the fields that escaped.

    Each field's characters become ``input``; the part that ended up outside its string literal
    becomes ``escaped``. Templates always open a quote right before a field, so a field at the
    very start of the SQL has no literal to escape.
    """
    escaped_fields: list[ColumnName] = []
    position = 0
    for text, field in pieces:
        start, end = position, position + len(text)
        position = end
        if field is None:
            continue
        kinds[start:end] = ["input"] * len(text)
        span = escaped_span(sql, start, end, dialect) if start > 0 else None
        if span is not None:
            kinds[span[0] : span[1]] = ["escaped"] * (span[1] - span[0])
            escaped_fields.append(field)
    return escaped_fields


def _split_lines(sql: str, kinds: Sequence[SegmentKind]) -> list[list[Segment]]:
    """Split into lines on ``\\n`` (not included) and merge adjacent same-kind characters."""
    lines: list[list[Segment]] = [[]]
    for char, kind in zip(sql, kinds, strict=True):
        line = lines[-1]
        if char == "\n":
            lines.append([])
        elif line and line[-1].kind == kind:
            line[-1].text += char
        else:
            line.append(Segment(text=char, kind=kind))
    return lines
