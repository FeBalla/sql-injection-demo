"""Request and response models of the SQL injection API: the contract shared with the web app."""

from pydantic import BaseModel

from ..models import Customer, CustomerIn, Db
from ..preview import StatementPreview


class StatementRequest(BaseModel):
    row: CustomerIn
    parameterized: bool


class CustomerPage(BaseModel):
    rows: list[Customer]
    total: int
    page: int
    page_size: int


class DatabaseInfo(BaseModel):
    id: Db
    label: str
    table: str
    available: bool
    reason: str | None


class ResetResult(BaseModel):
    total: int


class InsertResult(BaseModel):
    ok: bool
    statement: StatementPreview
    rows_affected: int | None
    total_rows: int | None
    error: str | None
