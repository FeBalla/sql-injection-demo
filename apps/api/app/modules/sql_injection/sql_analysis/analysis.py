"""Analyzes a built statement for the preview: highlighted lines, statement count, escapes."""

from collections.abc import Sequence
from dataclasses import dataclass

from ..schemas import Column, Db, Segment, SegmentKind
from .dialects import DIALECTS, KEYWORDS, Dialect
from .escapes import escaped_span
from .lexer import Token, tokenize

Piece = tuple[str, Column | None]
"""A chunk of SQL text and the field it came from (``None`` for template text)."""


@dataclass(frozen=True)
class Analysis:
    lines: list[list[Segment]]
    statement_count: int
    escaped_fields: list[Column]


def analyze(pieces: Sequence[Piece], db: Db) -> Analysis:
    """Highlight the SQL built from ``pieces`` and detect values that escape their literal."""
    dialect = DIALECTS[db]
    sql = "".join(text for text, _ in pieces)
    tokens = tokenize(sql, dialect)
    kinds = _token_kinds(sql, tokens)
    escaped_fields = _mark_user_input(kinds, sql, pieces, dialect)
    return Analysis(
        lines=_split_lines(sql, kinds),
        statement_count=count_statements(tokens),
        escaped_fields=escaped_fields,
    )


def count_statements(tokens: Sequence[Token]) -> int:
    """Count non-empty statements separated by top-level semicolons."""
    count = 0
    has_content = False
    for token in tokens:
        if token.kind == "semicolon":
            count += has_content
            has_content = False
        elif token.kind not in ("space", "comment"):
            has_content = True
    return count + has_content


def _token_kinds(sql: str, tokens: Sequence[Token]) -> list[SegmentKind]:
    """The syntax highlighting kind of every character of ``sql``."""
    kinds: list[SegmentKind] = []
    for token in tokens:
        kinds.extend([_segment_kind(sql, token)] * (token.end - token.start))
    return kinds


def _segment_kind(sql: str, token: Token) -> SegmentKind:
    if token.kind == "word":
        return "keyword" if sql[token.start : token.end].upper() in KEYWORDS else "plain"
    if token.kind in ("string", "param"):
        return token.kind
    return "plain"


def _mark_user_input(
    kinds: list[SegmentKind], sql: str, pieces: Sequence[Piece], dialect: Dialect
) -> list[Column]:
    """Recolor the characters typed by the user (``input``, or ``escaped`` where they left
    their string literal) in place, and return the fields that escaped."""
    escaped_fields: list[Column] = []
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
