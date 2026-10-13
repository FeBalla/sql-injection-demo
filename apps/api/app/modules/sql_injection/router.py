"""HTTP endpoints of the SQL injection demo (mounted under /api)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .backends import Backend
from .schemas import (
    CustomerPage,
    DatabaseInfo,
    Db,
    InsertResult,
    ResetResult,
    StatementPreview,
    StatementRequest,
)
from .statements import build_statement

router = APIRouter(prefix="/sql-injection", tags=["sql-injection"])


def _backends(request: Request) -> dict[Db, Backend]:
    return request.app.state.sql_injection_backends


def _available_backend(
    db: Db, backends: Annotated[dict[Db, Backend], Depends(_backends)]
) -> Backend:
    backend = backends[db]
    available, reason = backend.availability()
    if not available:
        raise HTTPException(status_code=503, detail=f"{backend.label} is unavailable: {reason}")
    return backend


AvailableBackend = Annotated[Backend, Depends(_available_backend)]


@router.get("/databases")
def list_databases(
    backends: Annotated[dict[Db, Backend], Depends(_backends)],
) -> list[DatabaseInfo]:
    infos = []
    for backend in backends.values():
        available, reason = backend.availability()
        infos.append(
            DatabaseInfo(
                id=backend.id,
                label=backend.label,
                table=backend.table,
                available=available,
                reason=reason,
            )
        )
    return infos


@router.get("/{db}/customers")
def list_customers(
    backend: AvailableBackend,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
) -> CustomerPage:
    return CustomerPage(
        rows=backend.page(limit=page_size, offset=(page - 1) * page_size),
        total=backend.count(),
        page=page,
        page_size=page_size,
    )


@router.post("/{db}/reset")
def reset(backend: AvailableBackend) -> ResetResult:
    return ResetResult(total=backend.reset())


@router.post("/{db}/preview")
def preview(backend: AvailableBackend, body: StatementRequest) -> StatementPreview:
    return _build(backend, body)


@router.post("/{db}/insert")
def insert(backend: AvailableBackend, body: StatementRequest) -> InsertResult:
    statement = _build(backend, body)
    result = backend.execute(statement)
    return InsertResult(
        ok=result.ok,
        statement=statement,
        rows_affected=result.rows_affected,
        total_rows=result.total_rows,
        error=result.error,
    )


def _build(backend: Backend, body: StatementRequest) -> StatementPreview:
    return build_statement(backend.id, body.row, body.parameterized, backend.statement_table)
