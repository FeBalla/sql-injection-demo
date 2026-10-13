"""INTENTIONALLY VULNERABLE: builds SQL by pasting raw user input between quotes.

This module exists only so Injection Lab can demonstrate SQL injection. Never copy it into real
code. It is the moral equivalent of::

    sql = f"VALUES (\\n  '{row.name}',\\n  '{row.email}', ..."

Any quote, backslash or semicolon in the input becomes part of the SQL itself, so a value can
close its string literal early and append statements of its own. The safe alternative is the
parameterized branch of ``builder.py``, where values travel separately from the SQL text.

The text is returned as pieces tagged with the field they came from so the preview can show
which characters were typed by the user; joining the pieces gives the exact SQL that runs.
"""

from ..schemas import COLUMNS, CustomerIn
from ..sql_analysis.analysis import Piece


def concatenated_values(row: CustomerIn) -> list[Piece]:
    """Return one ``  '<value>',`` line per column, values inserted verbatim (unescaped)."""
    pieces: list[Piece] = []
    for index, column in enumerate(COLUMNS):
        separator = "," if index < len(COLUMNS) - 1 else ""
        pieces += [("  '", None), (getattr(row, column), column), (f"'{separator}\n", None)]
    return pieces
