"""Builds the statement preview from the same templates and functions that ``queries/`` runs.

The SQL is never written twice, so the preview cannot drift from what runs. The tests check
both modes against what really reaches each database.

* Concatenated: the SQL is the query's own output. Which characters the user typed is read
  from the template itself (its ``{field}`` placeholders, see :func:`template_pieces`).
* Parameterized: the SQL text has placeholders only, and the values are listed as bound params.
"""

from collections.abc import Mapping
from string import Formatter
from typing import cast

from sqlalchemy.dialects.postgresql.psycopg import PGDialect_psycopg

from ..models import COLUMNS, ColumnName, CustomerIn, Db
from ..queries import bigquery, postgres
from .analysis import Piece, analyze
from .statement import BoundParam, StatementPreview

_POSTGRES_WIRE_DIALECT = PGDialect_psycopg(paramstyle="numeric_dollar")
"""psycopg sends SQLAlchemy's ``%(name)s`` placeholders to Postgres as ``$1, $2...`` in order of
appearance; compiling with the ``numeric_dollar`` paramstyle renders that same text."""


def postgres_preview(customer: CustomerIn, parameterized: bool) -> StatementPreview:
    """The Postgres INSERT for ``customer``, as Postgres receives it.

    Parameterized, the ``text()`` statement is compiled the way the server sees it (``$1..$4``)
    and its values become bound params in that order.
    """
    if not parameterized:
        sql = postgres.build_concatenated_insert(customer)
        return _concatenated("postgres", postgres.CONCATENATED_INSERT, sql, customer.model_dump())
    compiled = postgres.PARAMETERIZED_INSERT.compile(dialect=_POSTGRES_WIRE_DIALECT)
    values = customer.model_dump()
    params = [
        BoundParam(placeholder=f"${index}", column=name, type="text", value=values[name])
        for index, name in enumerate(compiled.positiontup or (), start=1)
    ]
    return _parameterized("postgres", compiled.string, params)


def bigquery_preview(customer: CustomerIn, parameterized: bool, *, table: str) -> StatementPreview:
    """The BigQuery INSERT for ``customer`` into ``table``, as the query job receives it.

    Parameterized, the SQL is the job's query text (``@name``...) and the bound params are the
    job's own query parameters.
    """
    if not parameterized:
        sql = bigquery.build_concatenated_insert(table, customer)
        values = {"table": table, **customer.model_dump()}
        return _concatenated("bigquery", bigquery.CONCATENATED_INSERT, sql, values)
    params = [
        BoundParam(
            placeholder=f"@{param.name}", column=param.name, type=param.type_, value=param.value
        )
        for param in bigquery.query_parameters(customer)
    ]
    return _parameterized("bigquery", bigquery.build_parameterized_insert(table), params)


def template_pieces(template: str, values: Mapping[str, str]) -> list[Piece]:
    """Split ``template.format(**values)`` into pieces of template text and values.

    Values of customer columns (user input) are tagged with their column; any other field (the
    BigQuery table) counts as template text. For example, ``"VALUES ('{name}')"`` with
    ``name="Ana"`` gives ``[("VALUES ('", None), ("Ana", "name"), ("')", None)]``.
    """
    pieces: list[Piece] = []
    for literal, field, format_spec, conversion in Formatter().parse(template):
        if literal:
            pieces.append((literal, None))
        if field is None:
            continue
        if format_spec or conversion:
            raise ValueError(f"Templates use plain {{field}} placeholders only, got {field!r}.")
        column = cast(ColumnName, field) if field in COLUMNS else None
        pieces.append((values[field], column))
    return pieces


def _concatenated(db: Db, template: str, sql: str, values: Mapping[str, str]) -> StatementPreview:
    """The preview of ``sql``, built from ``template`` and ``values``, with the user's input
    tagged. Fails if the pieces do not add up to ``sql`` exactly (the preview would lie)."""
    pieces = template_pieces(template, values)
    if "".join(text for text, _ in pieces) != sql:
        raise ValueError("The template pieces do not rebuild the SQL the query runs.")
    return _preview(db, sql, pieces, parameterized=False, params=[])


def _parameterized(db: Db, sql: str, params: list[BoundParam]) -> StatementPreview:
    """The preview of a parameterized ``sql``: all template text, since no value is in it."""
    return _preview(db, sql, [(sql, None)], parameterized=True, params=params)


def _preview(
    db: Db, sql: str, pieces: list[Piece], *, parameterized: bool, params: list[BoundParam]
) -> StatementPreview:
    """Analyze ``pieces`` and assemble the preview."""
    analysis = analyze(pieces, db)
    return StatementPreview(
        database=db,
        parameterized=parameterized,
        sql=sql,
        lines=analysis.lines,
        params=params,
        statement_count=analysis.statement_count,
        escaped_fields=analysis.escaped_fields,
    )
