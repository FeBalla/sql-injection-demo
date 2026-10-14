"""Per-database SQL syntax rules the lexer needs, and the keywords highlighted in the preview.

The templates only ever emit plain quoted strings, but concatenated user input can produce any
syntax the database accepts, so the rules cover every way a string or comment can start:

Postgres: ``'...'`` strings with ``''`` as the escaped quote (standard_conforming_strings on),
``E'...'`` strings that also accept backslash escapes, dollar-quoted strings (``$$...$$`` and
``$tag$...$tag$``, no escapes), ``"..."`` identifiers, ``--`` and nested ``/* /* */ */``
comments, ``$1`` parameters. ``U&'...'`` strings lex like plain strings, which they are for
finding where they end.

BigQuery: ``'...'`` / ``"..."`` and triple-quoted strings with backslash escapes, optionally
prefixed with ``r``, ``b``, ``rb`` or ``br`` (any case). Raw strings keep their backslashes, but
an escaped quote still does not close them (as in GoogleSQL's own lexer), so they end exactly
where non-raw strings do. Backtick identifiers, ``--``, ``#`` and ``/* */`` comments (not
nested), ``@name`` parameters.
"""

from dataclasses import dataclass
from typing import Literal

from ..models import Db


@dataclass(frozen=True)
class Dialect:
    string_quotes: str
    """Characters that open a string literal."""
    identifier_quotes: str
    """Characters that open a quoted identifier."""
    string_prefixes: frozenset[str]
    """Lowercased prefixes that can start a string literal right before its opening quote.
    Prefixed strings always accept backslash escapes."""
    backslash_escapes: bool
    """Whether ``\\x`` is an escape in every quoted literal (not only in prefixed strings)."""
    doubled_quote_escapes: bool
    """Whether a doubled quote (``''``) inside a literal is an escaped quote."""
    triple_quoted_strings: bool
    """Whether ``'''`` / ``\"\"\"`` open a triple-quoted string."""
    hash_comments: bool
    """Whether ``#`` starts a line comment (``--`` always does)."""
    nested_block_comments: bool
    """Whether ``/* */`` comments nest."""
    dollar_quoted_strings: bool
    """Whether ``$$...$$`` / ``$tag$...$tag$`` strings exist."""
    dollar_in_identifiers: bool
    """Whether ``$`` may appear in a word after its first character (so ``a$$`` is a word)."""
    parameters: Literal["numbered", "named"]
    """Query parameter syntax: ``$1`` (numbered) or ``@name`` (named)."""


DIALECTS: dict[Db, Dialect] = {
    "postgres": Dialect(
        string_quotes="'",
        identifier_quotes='"',
        string_prefixes=frozenset({"e"}),
        backslash_escapes=False,
        doubled_quote_escapes=True,
        triple_quoted_strings=False,
        hash_comments=False,
        nested_block_comments=True,
        dollar_quoted_strings=True,
        dollar_in_identifiers=True,
        parameters="numbered",
    ),
    "bigquery": Dialect(
        string_quotes="'\"",
        identifier_quotes="`",
        string_prefixes=frozenset({"r", "b", "rb", "br"}),
        backslash_escapes=True,
        doubled_quote_escapes=False,
        triple_quoted_strings=True,
        hash_comments=True,
        nested_block_comments=False,
        dollar_quoted_strings=False,
        dollar_in_identifiers=False,
        parameters="named",
    ),
}

# fmt: off
KEYWORDS = frozenset({
    "ALL", "ALTER", "AND", "AS", "ASC", "BETWEEN", "BY", "CASE", "CREATE", "CROSS", "DEFAULT",
    "DELETE", "DESC", "DISTINCT", "DROP", "ELSE", "END", "EXCEPT", "EXISTS", "FALSE", "FROM",
    "FULL", "GRANT", "GROUP", "HAVING", "IF", "IN", "INNER", "INSERT", "INTERSECT", "INTO", "IS",
    "JOIN", "LEFT", "LIKE", "LIMIT", "MERGE", "NOT", "NULL", "OFFSET", "ON", "OR", "ORDER",
    "OUTER", "REPLACE", "RETURNING", "REVOKE", "RIGHT", "SELECT", "SET", "TABLE", "THEN", "TRUE",
    "TRUNCATE", "UNION", "UPDATE", "USING", "VALUES", "WHEN", "WHERE", "WITH",
})
"""SQL keywords highlighted as such (both dialects). Function names (COALESCE, MAX, ...) are
deliberately absent."""
# fmt: on
