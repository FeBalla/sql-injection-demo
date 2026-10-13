"""HTTP endpoints of the SQL injection demo (mounted under /api)."""

from typing import Annotated

from fastapi import APIRouter, Query

from .databases.protocol import Database
from .dependencies import AvailableDatabase, Databases
from .schemas import (
    CustomerPage,
    DatabaseInfo,
    InsertResult,
    ResetResult,
    StatementPreview,
    StatementRequest,
)
from .statements.builder import build_statement

router = APIRouter(prefix="/sql-injection", tags=["sql-injection"])


@router.get("/databases")
def list_databases(databases: Databases) -> list[DatabaseInfo]:
    infos = []
    for database in databases.values():
        available, reason = database.availability()
        infos.append(
            DatabaseInfo(
                id=database.id,
                label=database.label,
                table=database.table,
                available=available,
                reason=reason,
            )
        )
    return infos


@router.get("/{db}/customers")
def list_customers(
    database: AvailableDatabase,
    # Bounded so (page - 1) * page_size always fits the databases' 64-bit OFFSET.
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
) -> CustomerPage:
    return CustomerPage(
        rows=database.page(limit=page_size, offset=(page - 1) * page_size),
        total=database.count(),
        page=page,
        page_size=page_size,
    )


@router.post("/{db}/reset")
def reset(database: AvailableDatabase) -> ResetResult:
    return ResetResult(total=database.reset())


@router.post("/{db}/preview")
def preview(database: AvailableDatabase, body: StatementRequest) -> StatementPreview:
    return _build(database, body)


@router.post("/{db}/insert")
def insert(database: AvailableDatabase, body: StatementRequest) -> InsertResult:
    statement = _build(database, body)
    result = database.execute(statement)
    return InsertResult(
        ok=result.ok,
        statement=statement,
        rows_affected=result.rows_affected,
        total_rows=result.total_rows,
        error=result.error,
    )


def _build(database: Database, body: StatementRequest) -> StatementPreview:
    return build_statement(database.id, body.row, body.parameterized, database.statement_table)
