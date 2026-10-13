"""Builds the INSERT statement shown in the preview and executed by /insert.

Both endpoints call :func:`build_statement`, and the backends execute exactly
``statement.sql`` with ``statement.params``, so the preview can never drift from what runs.
"""

from .highlight import Piece, analyze
from .schemas import COLUMNS, BoundParam, CustomerIn, Db, StatementPreview
from .unsafe import concatenated_values

_COLUMN_LIST = ", ".join(COLUMNS)


def build_statement(db: Db, row: CustomerIn, parameterized: bool, table: str) -> StatementPreview:
    """Build the INSERT for ``row`` into ``table`` (as written in SQL, without quoting)."""
    pieces = _pieces(db, row, parameterized, table)
    analysis = analyze(pieces, db)
    return StatementPreview(
        database=db,
        parameterized=parameterized,
        sql="".join(text for text, _ in pieces),
        lines=analysis.lines,
        params=_bound_params(db, row) if parameterized else [],
        statement_count=analysis.statement_count,
        escaped_fields=analysis.escaped_fields,
    )


def _pieces(db: Db, row: CustomerIn, parameterized: bool, table: str) -> list[Piece]:
    if db == "postgres":
        head = f"INSERT INTO {table} ({_COLUMN_LIST})\n"
        if parameterized:
            return [(head + "VALUES ($1, $2, $3, $4);", None)]
        return [(head + "VALUES (\n", None), *concatenated_values(row), (");", None)]

    # BigQuery has no auto-increment, so the next id is computed inside the statement. Two
    # concurrent inserts can read the same MAX(id) and get the same id; that is acceptable for
    # this single-user demo table (ids are only used for ordering and display).
    head = (
        f"INSERT INTO `{table}` (id, {_COLUMN_LIST})\n"
        "VALUES (\n"
        f"  (SELECT COALESCE(MAX(id), 0) + 1 FROM `{table}`),\n"
    )
    if parameterized:
        placeholders = ", ".join(f"@{column}" for column in COLUMNS)
        return [(f"{head}  {placeholders}\n);", None)]
    return [(head, None), *concatenated_values(row), (");", None)]


def _bound_params(db: Db, row: CustomerIn) -> list[BoundParam]:
    return [
        BoundParam(
            placeholder=f"${index}" if db == "postgres" else f"@{column}",
            column=column,
            type="text" if db == "postgres" else "STRING",
            value=getattr(row, column),
        )
        for index, column in enumerate(COLUMNS, start=1)
    ]
