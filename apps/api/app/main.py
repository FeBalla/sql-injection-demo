"""FastAPI entry point. Feature modules live in ``app.modules`` and are mounted under /api."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.modules import sql_injection

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    databases = sql_injection.create_databases(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        sql_injection.seed_empty_tables(databases)
        yield

    app = FastAPI(title="Injection Lab API", lifespan=lifespan)
    app.state.sql_injection_databases = databases

    @app.exception_handler(sql_injection.DatabaseUnavailableError)
    async def database_unavailable(
        _: Request, exc: sql_injection.DatabaseUnavailableError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(sql_injection.router, prefix="/api")
    return app


app = create_app()
