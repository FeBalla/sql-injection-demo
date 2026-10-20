"""Just enough SQL syntax to tell where every string literal starts and ends.

That is exactly what SQL injection abuses: a quote typed by the user ends the literal the
template opened, and everything after it is parsed as SQL. This is not a parser. It is a
lexer that never fails (anything unterminated runs to the end of the text) and knows each
database's quoting, comment and parameter rules.

The preview only needs what this package exports:

* :data:`DIALECTS`: the syntax rules of each database,
* :func:`tokenize`: splits SQL into :class:`Token` objects (strings, comments, words...),
* :func:`count_statements`: how many statements the database will run,
* :func:`escaped_span`: the part of an input value that ended up outside its string literal,
* :data:`KEYWORDS`: the words highlighted as SQL keywords.
"""

from .dialects import DIALECTS, KEYWORDS, Dialect
from .escapes import escaped_span
from .lexer import Token, TokenKind, count_statements, tokenize

__all__ = [
    "DIALECTS",
    "KEYWORDS",
    "Dialect",
    "Token",
    "TokenKind",
    "count_statements",
    "escaped_span",
    "tokenize",
]
