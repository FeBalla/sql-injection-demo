"""Detecting where a concatenated input value escapes the string literal it was pasted into.

The template wraps every value in quotes, so the character right before the value opens the
literal and the character right after it should close it. A value escapes in three ways:

* leading quotes turn the opening quote into a triple quote (``'''`` on BigQuery),
* a quote inside the value closes the literal early,
* the value ends with an escape (a trailing ``'`` forming ``''`` on Postgres, a trailing ``\\``
  on BigQuery) that swallows the template's closing quote.
"""

from .dialects import Dialect
from .lexer import QuotedScan, scan_quoted


def escaped_span(sql: str, start: int, end: int, dialect: Dialect) -> tuple[int, int] | None:
    """Return the part of the value ``sql[start:end]`` that is outside its string literal."""
    literal = scan_quoted(sql, start - 1, dialect)
    if literal.open_end > start:
        # The opening delimiter grew into the value (``'''``): those quotes are syntax.
        return start, min(literal.open_end, end)
    if literal.close_start == end:
        return None  # Closed exactly where the template closes it.
    if literal.close_start is not None and literal.close_start < end:
        # Closed early: everything from that quote to the end of the value is outside.
        return literal.close_start, end
    return _swallowed_closing_quote(literal, end)


def _swallowed_closing_quote(literal: QuotedScan, end: int) -> tuple[int, int] | None:
    """The escape sequence that starts inside the value and ends after it, if any: it turns the
    template's closing quote into an escaped character."""
    for escape_start, escape_end in literal.escapes:
        if escape_start < end < escape_end:
            return escape_start, end
    return None
