"""Creates the databases behind the demo from the app settings."""

from app.config import Settings

from ..schemas import Db
from .bigquery.database import BigQueryDatabase
from .postgres import PostgresDatabase
from .protocol import Database


def create_databases(settings: Settings) -> dict[Db, Database]:
    return {"postgres": PostgresDatabase(settings), "bigquery": BigQueryDatabase(settings)}
