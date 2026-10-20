"""HTTP endpoints of the SQL injection demo (mounted under /api): parse, call the service, reply."""

from typing import Annotated

from fastapi import APIRouter, Query

from ..preview import StatementPreview
from .dependencies import AvailableService, CustomerServices
from .schemas import CustomerPage, DatabaseInfo, InsertResult, ResetResult, StatementRequest

router = APIRouter(prefix="/sql-injection", tags=["sql-injection"])


@router.get("/databases")
def list_databases(services: CustomerServices) -> list[DatabaseInfo]:
    infos = []
    for service in services.values():
        reason = service.unavailable_reason()
        infos.append(
            DatabaseInfo(
                id=service.db,
                label=service.label,
                table=service.table,
                available=reason is None,
                reason=reason,
            )
        )
    return infos


@router.get("/{db}/customers")
def list_customers(
    service: AvailableService,
    # Bounded so (page - 1) * page_size always fits the databases' 64-bit OFFSET.
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
) -> CustomerPage:
    rows, total = service.list_page(page, page_size)
    return CustomerPage(rows=rows, total=total, page=page, page_size=page_size)


@router.post("/{db}/reset")
def reset(service: AvailableService) -> ResetResult:
    return ResetResult(total=service.reset())


@router.post("/{db}/preview")
def preview(service: AvailableService, body: StatementRequest) -> StatementPreview:
    return service.preview(body.row, body.parameterized)


@router.post("/{db}/insert")
def insert(service: AvailableService, body: StatementRequest) -> InsertResult:
    statement, execution = service.insert(body.row, body.parameterized)
    return InsertResult(
        ok=execution.ok,
        statement=statement,
        rows_affected=execution.rows_affected,
        total_rows=execution.total_rows,
        error=execution.error,
    )
