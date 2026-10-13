"""FastAPI dependencies of the routes: the configured databases and the one a URL asks for."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from .databases.protocol import Database
from .schemas import Db


def get_databases(request: Request) -> dict[Db, Database]:
    """The databases created by ``create_app`` (stored on the app state)."""
    return request.app.state.sql_injection_databases


Databases = Annotated[dict[Db, Database], Depends(get_databases)]


def get_available_database(db: Db, databases: Databases) -> Database:
    """The database named by the ``{db}`` path parameter, or HTTP 503 if it is unavailable."""
    database = databases[db]
    available, reason = database.availability()
    if not available:
        raise HTTPException(status_code=503, detail=f"{database.label} is unavailable: {reason}")
    return database


AvailableDatabase = Annotated[Database, Depends(get_available_database)]
