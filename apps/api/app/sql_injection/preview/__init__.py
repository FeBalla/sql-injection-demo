"""The statement preview: the exact SQL of the demo INSERT, highlighted and analyzed. No DB access.

Entry points: :func:`postgres_preview` and :func:`bigquery_preview` return a
:class:`StatementPreview` for a customer, concatenated or parameterized.

How a preview is made:

1. ``builder`` takes the SQL from the same templates and functions in ``queries/`` that run the
   INSERT, and splits it into *pieces*: template text, and the value of each form field.
2. ``analysis`` colors every character, counts the statements and flags the fields whose value
   escaped its string literal.
3. ``statement`` holds the result returned by the API.

The SQL lexing behind step 2 (each database's quoting, comment and parameter rules) lives in
``sql_syntax``. Reading it is only needed to change how SQL is tokenized.
"""

from .builder import bigquery_preview, postgres_preview
from .statement import BoundParam, Segment, StatementPreview

__all__ = ["BoundParam", "Segment", "StatementPreview", "bigquery_preview", "postgres_preview"]
