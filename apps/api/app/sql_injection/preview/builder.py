"""Builds the statement preview from the same templates and builders the ``queries/`` run.

* Concatenated: the SQL is the builder's own output, and which characters were typed by the user
  is read from the template itself (its ``{field}`` placeholders), never from a second copy.
* Parameterized: Postgres's SQLAlchemy statement is shown the way the server receives it
  (``$1..$4``); BigQuery's is its exact query text, with the job's query parameters.

The tests check both against what really reaches each database.
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
    """Split ``template.format(**values)`` into template text and values, tagging the values of
    customer columns (user input) with their column. Other fields (the table) are template text."""
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
    pieces = template_pieces(template, values)
    if "".join(text for text, _ in pieces) != sql:
        raise ValueError("The template pieces do not rebuild the SQL the query runs.")
    analysis = analyze(pieces, db)
    return StatementPreview(
        database=db,
        parameterized=False,
        sql=sql,
        lines=analysis.lines,
        params=[],
        statement_count=analysis.statement_count,
        escaped_fields=analysis.escaped_fields,
    )


def _parameterized(db: Db, sql: str, params: list[BoundParam]) -> StatementPreview:
    analysis = analyze([(sql, None)], db)
    return StatementPreview(
        database=db,
        parameterized=True,
        sql=sql,
        lines=analysis.lines,
        params=params,
        statement_count=analysis.statement_count,
        escaped_fields=analysis.escaped_fields,
    )
