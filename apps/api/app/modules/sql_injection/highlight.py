"""A small, dialect-aware SQL lexer that powers the statement preview.

It answers three questions about a statement:

* how to color each character (``keyword``, ``string``, ``param``, ``plain``, or ``input`` /
  ``escaped`` for characters that came from user input),
* how many statements the database will see (top-level ``;`` outside strings and comments),
* which input values escape the string literal the template put them in.

It is not a full parser: it only knows enough of each dialect's literal, identifier and comment
syntax to find where strings start and end, which is exactly what SQL injection abuses.

Postgres: ``'...'`` strings with ``''`` as the escaped quote (standard_conforming_strings on),
``"..."`` identifiers, ``--`` and ``/* */`` comments, ``$1`` parameters. Dollar quoting and
``E'...'`` strings are not handled; the demo templates never produce them.

BigQuery: ``'...'`` / ``"..."`` and triple-quoted strings with backslash escapes, backtick
identifiers, ``--``, ``#`` and ``/* */`` comments, ``@name`` parameters.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from .schemas import Column, Db, Segment, SegmentKind

Piece = tuple[str, Column | None]
"""A chunk of SQL text and the field it came from (``None`` for template text)."""

TokenKind = Literal[
    "space", "comment", "string", "identifier", "word", "param", "semicolon", "other"
]

# fmt: off
KEYWORDS = frozenset({
    "ALL", "ALTER", "AND", "AS", "ASC", "BETWEEN", "BY", "CASE", "CREATE", "CROSS", "DEFAULT",
    "DELETE", "DESC", "DISTINCT", "DROP", "ELSE", "END", "EXCEPT", "EXISTS", "FALSE", "FROM",
    "FULL", "GRANT", "GROUP", "HAVING", "IF", "IN", "INNER", "INSERT", "INTERSECT", "INTO", "IS",
    "JOIN", "LEFT", "LIKE", "LIMIT", "MERGE", "NOT", "NULL", "OFFSET", "ON", "OR", "ORDER",
    "OUTER", "REPLACE", "RETURNING", "REVOKE", "RIGHT", "SELECT", "SET", "TABLE", "THEN", "TRUE",
    "TRUNCATE", "UNION", "UPDATE", "USING", "VALUES", "WHEN", "WHERE", "WITH",
})
"""SQL keywords highlighted as such. Function names (COALESCE, MAX, ...) are deliberately absent."""
# fmt: on

_STRING_QUOTES: dict[Db, str] = {"postgres": "'", "bigquery": "'\""}
_IDENTIFIER_QUOTES: dict[Db, str] = {"postgres": '"', "bigquery": "`"}


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    start: int
    end: int


@dataclass(frozen=True)
class QuotedScan:
    """Where a quoted literal (string or identifier) starting at a given index ends."""

    open_end: int
    """Index right after the opening delimiter (``'`` or ``'''``)."""
    close_start: int | None
    """Index of the closing delimiter, or ``None`` if the literal is unterminated."""
    end: int
    """Index right after the literal (``len(sql)`` if unterminated)."""
    escapes: tuple[tuple[int, int], ...]
    """``(start, end)`` of every escape sequence (``''`` or ``\\x``) inside the literal."""


@dataclass(frozen=True)
class Analysis:
    lines: list[list[Segment]]
    statement_count: int
    escaped_fields: list[Column]


def scan_quoted(sql: str, start: int, dialect: Db) -> QuotedScan:
    """Scan the quoted literal whose opening delimiter is at ``sql[start]``."""
    quote = sql[start]
    triple = dialect == "bigquery" and quote in "'\"" and sql.startswith(quote * 3, start)
    delimiter = quote * 3 if triple else quote
    open_end = start + len(delimiter)
    escapes: list[tuple[int, int]] = []
    i = open_end
    while i < len(sql):
        if dialect == "bigquery" and sql[i] == "\\":
            escapes.append((i, min(i + 2, len(sql))))
            i += 2
        elif dialect == "postgres" and sql.startswith(quote * 2, i):
            escapes.append((i, i + 2))
            i += 2
        elif sql.startswith(delimiter, i):
            return QuotedScan(open_end, i, i + len(delimiter), tuple(escapes))
        else:
            i += 1
    return QuotedScan(open_end, None, len(sql), tuple(escapes))


def tokenize(sql: str, dialect: Db) -> list[Token]:
    """Split ``sql`` into tokens. Never fails: unterminated literals run to the end."""
    tokens: list[Token] = []
    n = len(sql)
    i = 0
    while i < n:
        c = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        kind: TokenKind
        if c.isspace():
            kind, j = "space", i + 1
            while j < n and sql[j].isspace():
                j += 1
        elif sql.startswith("--", i) or (dialect == "bigquery" and c == "#"):
            kind, j = "comment", _find_or_end(sql, "\n", i)
        elif sql.startswith("/*", i):
            close = sql.find("*/", i + 2)
            kind, j = "comment", (n if close < 0 else close + 2)
        elif c in _STRING_QUOTES[dialect]:
            kind, j = "string", scan_quoted(sql, i, dialect).end
        elif c in _IDENTIFIER_QUOTES[dialect]:
            kind, j = "identifier", scan_quoted(sql, i, dialect).end
        elif c.isalpha() or c == "_":
            kind, j = "word", i + 1
            while j < n and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
        elif (dialect == "postgres" and c == "$" and nxt.isdigit()) or (
            dialect == "bigquery" and c == "@" and (nxt.isalpha() or nxt == "_")
        ):
            kind, j = "param", i + 2
            while j < n and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
        elif c == ";":
            kind, j = "semicolon", i + 1
        else:
            kind, j = "other", i + 1
        tokens.append(Token(kind, i, j))
        i = j
    return tokens


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


def escaped_span(sql: str, start: int, end: int, dialect: Db) -> tuple[int, int] | None:
    """Return the part of the value ``sql[start:end]`` that escapes its string literal.

    The template wraps every value in quotes, so ``sql[start - 1]`` opens the literal and
    ``sql[end]`` should close it. The value escapes when the literal closes early (everything
    from that quote to the end of the value is outside the literal) or when the value swallows
    the closing quote (a trailing ``'`` forming ``''`` on Postgres, a trailing ``\\`` on BigQuery,
    or leading quotes turning the opening quote into ``'''`` on BigQuery).
    """
    scan = scan_quoted(sql, start - 1, dialect)
    if scan.open_end > start:
        return start, min(scan.open_end, end)
    if scan.close_start == end:
        return None
    if scan.close_start is not None and scan.close_start < end:
        return scan.close_start, end
    for escape_start, escape_end in scan.escapes:
        if escape_start < end < escape_end:
            return escape_start, end
    return None


def analyze(pieces: Sequence[Piece], dialect: Db) -> Analysis:
    """Highlight the SQL built from ``pieces`` and detect values that escape their literal."""
    sql = "".join(text for text, _ in pieces)
    tokens = tokenize(sql, dialect)

    kinds: list[SegmentKind] = []
    for token in tokens:
        kinds.extend([_segment_kind(sql, token)] * (token.end - token.start))

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

    return Analysis(
        lines=_split_lines(sql, kinds),
        statement_count=count_statements(tokens),
        escaped_fields=escaped_fields,
    )


def _segment_kind(sql: str, token: Token) -> SegmentKind:
    if token.kind == "word":
        return "keyword" if sql[token.start : token.end].upper() in KEYWORDS else "plain"
    if token.kind in ("string", "param"):
        return token.kind
    return "plain"


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


def _find_or_end(sql: str, needle: str, start: int) -> int:
    found = sql.find(needle, start)
    return len(sql) if found < 0 else found
