"""Splits SQL text into tokens and scans quoted literals, following a :class:`Dialect`'s rules.

Only the token boundaries matter (where strings, identifiers and comments start and end), so
the lexer never fails: anything unterminated simply runs to the end of the text.

Public functions: :func:`tokenize`, :func:`count_statements` and :func:`scan_quoted`. The
private helpers below them each recognize one kind of token.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from .dialects import Dialect

TokenKind = Literal[
    "space", "comment", "string", "identifier", "word", "param", "semicolon", "other"
]
"""What a token is. ``word`` covers keywords and unquoted names alike; ``identifier`` is a
quoted name (``"a b"``, ```a.b```); ``param`` a query parameter (``$1``, ``@name``)."""


@dataclass(frozen=True)
class Token:
    """A run of SQL text: ``sql[start:end]`` is a single ``kind`` of token."""

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


def tokenize(sql: str, dialect: Dialect) -> list[Token]:
    """Split ``sql`` into tokens. Never fails: unterminated literals run to the end."""
    tokens: list[Token] = []
    start = 0
    while start < len(sql):
        kind, end = _next_token(sql, start, dialect)
        tokens.append(Token(kind, start, end))
        start = end
    return tokens


def count_statements(tokens: Sequence[Token]) -> int:
    """How many statements the database will run: non-empty runs of tokens separated by
    top-level semicolons (a ``;`` inside a string or comment is part of that token)."""
    count = 0
    has_content = False
    for token in tokens:
        if token.kind == "semicolon":
            count += has_content
            has_content = False
        elif token.kind not in ("space", "comment"):
            has_content = True
    return count + has_content


def scan_quoted(
    sql: str, start: int, dialect: Dialect, *, backslash_escapes: bool = False
) -> QuotedScan:
    """Scan the quoted literal whose opening delimiter is at ``sql[start]``.

    Backslash escapes apply when the dialect always allows them (BigQuery) or when
    ``backslash_escapes`` is set (prefixed strings such as Postgres ``E'...'``).
    """
    quote = sql[start]
    triple = (
        dialect.triple_quoted_strings
        and quote in dialect.string_quotes
        and sql.startswith(quote * 3, start)
    )
    delimiter = quote * 3 if triple else quote
    open_end = start + len(delimiter)
    escapes: list[tuple[int, int]] = []
    i = open_end
    while i < len(sql):
        if (dialect.backslash_escapes or backslash_escapes) and sql[i] == "\\":
            escapes.append((i, min(i + 2, len(sql))))
            i += 2
        elif dialect.doubled_quote_escapes and sql.startswith(quote * 2, i):
            escapes.append((i, i + 2))
            i += 2
        elif sql.startswith(delimiter, i):
            return QuotedScan(open_end, i, i + len(delimiter), tuple(escapes))
        else:
            i += 1
    return QuotedScan(open_end, None, len(sql), tuple(escapes))


def _next_token(sql: str, start: int, dialect: Dialect) -> tuple[TokenKind, int]:
    """Kind and end of the token starting at ``sql[start]``. Checks run in order; the first match
    wins (e.g. ``E'`` is a prefixed string before it is a word)."""
    char = sql[start]
    if char.isspace():
        return "space", _skip_while(sql, start + 1, str.isspace)
    if sql.startswith("--", start) or (dialect.hash_comments and char == "#"):
        return "comment", _find_or_end(sql, "\n", start)
    if sql.startswith("/*", start):
        return "comment", _block_comment_end(sql, start, nested=dialect.nested_block_comments)
    if char in dialect.string_quotes:
        return "string", scan_quoted(sql, start, dialect).end
    if char in dialect.identifier_quotes:
        return "identifier", scan_quoted(sql, start, dialect).end
    if (quote := _prefixed_quote(sql, start, dialect)) is not None:
        return "string", scan_quoted(sql, quote, dialect, backslash_escapes=True).end
    if char.isalpha() or char == "_":
        return "word", _word_end(sql, start + 1, dialect)
    if dialect.dollar_quoted_strings and (tag := _dollar_quote_tag(sql, start)) is not None:
        return "string", _dollar_quoted_end(sql, start, tag)
    if _starts_parameter(sql, start, dialect):
        return "param", _skip_while(sql, start + 2, _is_word_char)
    if char == ";":
        return "semicolon", start + 1
    return "other", start + 1


def _block_comment_end(sql: str, start: int, *, nested: bool) -> int:
    """End of the ``/* */`` comment at ``sql[start]``. Postgres nests them, BigQuery does not."""
    depth = 0
    i = start
    while i < len(sql):
        if sql.startswith("/*", i) and (nested or depth == 0):
            depth, i = depth + 1, i + 2
        elif sql.startswith("*/", i):
            depth, i = depth - 1, i + 2
            if depth == 0:
                return i
        else:
            i += 1
    return len(sql)


def _prefixed_quote(sql: str, start: int, dialect: Dialect) -> int | None:
    """Index of the opening quote if a prefixed string (``E'``, ``r'``, ``rb"``...) starts here."""
    for quote in (start + 1, start + 2):
        if (
            quote < len(sql)
            and sql[quote] in dialect.string_quotes
            and sql[start:quote].lower() in dialect.string_prefixes
        ):
            return quote
    return None


def _word_end(sql: str, start: int, dialect: Dialect) -> int:
    """End of the keyword or unquoted name whose second character is at ``sql[start]``."""

    def in_word(char: str) -> bool:
        return _is_word_char(char) or (dialect.dollar_in_identifiers and char == "$")

    return _skip_while(sql, start, in_word)


def _dollar_quote_tag(sql: str, start: int) -> str | None:
    """The ``$$`` or ``$tag$`` opening a Postgres dollar-quoted string at ``sql[start]``, if any.

    A tag cannot start with a digit, so ``$1`` stays a parameter.
    """
    if sql[start] != "$":
        return None
    j = start + 1
    if j < len(sql) and (sql[j].isalpha() or sql[j] == "_"):
        j += 1
        while j < len(sql) and (sql[j].isalnum() or sql[j] == "_"):
            j += 1
    return sql[start : j + 1] if j < len(sql) and sql[j] == "$" else None


def _dollar_quoted_end(sql: str, start: int, tag: str) -> int:
    """End of the dollar-quoted string opened by ``tag`` at ``sql[start]`` (no escapes inside)."""
    close = sql.find(tag, start + len(tag))
    return len(sql) if close < 0 else close + len(tag)


def _starts_parameter(sql: str, start: int, dialect: Dialect) -> bool:
    """Whether a ``$1`` (numbered) or ``@name`` (named) query parameter starts here."""
    char, following = sql[start], sql[start + 1 : start + 2]
    if dialect.parameters == "numbered":
        return char == "$" and following.isdigit()
    return char == "@" and (following.isalpha() or following == "_")


def _is_word_char(char: str) -> bool:
    """Whether ``char`` can continue a word or a parameter name."""
    return char.isalnum() or char == "_"


def _skip_while(sql: str, start: int, predicate: Callable[[str], bool]) -> int:
    """First index at or after ``start`` whose character does not satisfy ``predicate``."""
    i = start
    while i < len(sql) and predicate(sql[i]):
        i += 1
    return i


def _find_or_end(sql: str, needle: str, start: int) -> int:
    """Index of the next ``needle`` at or after ``start``, or ``len(sql)`` if there is none."""
    found = sql.find(needle, start)
    return len(sql) if found < 0 else found
