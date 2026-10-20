"""FastAPI entry point: mounts each lab's router under /api and seeds the demo tables on startup."""

import logging
from collections.abc import AsyncGenerator, Iterable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.errors import DatabaseUnavailableError
from app.sql_injection.api.dependencies import create_customer_services
from app.sql_injection.api.router import router as sql_injection_router
from app.sql_injection.services.customer_service import CustomerService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    services = create_customer_services(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        seed_empty_tables(services.values())
        yield

    app = FastAPI(title="Injection Lab API", lifespan=lifespan)
    app.state.sql_injection_services = services

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable(_: Request, exc: DatabaseUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(sql_injection_router, prefix="/api")
    return app


def seed_empty_tables(services: Iterable[CustomerService]) -> None:
    """Load the seed rows into every available database whose table is empty or missing.

    Failures are logged, not raised: the API still starts and reports the error per request.
    """
    for service in services:
        reason = service.unavailable_reason()
        if reason is not None:
            logger.info("%s skipped: %s", service.label, reason)
            continue
        try:
            service.seed_if_empty()
        except Exception:
            logger.exception("Could not seed %s", service.label)


app = create_app()
