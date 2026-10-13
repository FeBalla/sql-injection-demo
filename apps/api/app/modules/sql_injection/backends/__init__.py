"""The two databases behind the demo. Both implement :class:`base.Backend`."""

from app.config import Settings

from ..schemas import Db
from .base import Backend, DatabaseUnavailableError, Execution
from .bigquery import BigQueryBackend
from .postgres import PostgresBackend

__all__ = ["Backend", "DatabaseUnavailableError", "Execution", "create_backends"]


def create_backends(settings: Settings) -> dict[Db, Backend]:
    return {"postgres": PostgresBackend(settings), "bigquery": BigQueryBackend(settings)}
