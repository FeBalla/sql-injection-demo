"""FastAPI dependencies: the demo's services, and the one a ``{db}`` URL asks for."""

from functools import partial
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from app.core.config import Settings

from ..models import Db
from ..preview import bigquery_preview, postgres_preview
from ..repositories.bigquery import BigQueryCustomerRepository
from ..repositories.postgres import PostgresCustomerRepository
from ..services.customer_service import CustomerService


def create_customer_services(settings: Settings) -> dict[Db, CustomerService]:
    """One service per database, wired to its repository and preview (no connection yet)."""
    postgres = PostgresCustomerRepository(settings)
    bigquery = BigQueryCustomerRepository(settings)
    return {
        "postgres": CustomerService("postgres", "Postgres", postgres, postgres_preview),
        "bigquery": CustomerService(
            "bigquery", "BigQuery", bigquery, partial(bigquery_preview, table=bigquery.table)
        ),
    }


def get_customer_services(request: Request) -> dict[Db, CustomerService]:
    """The services created by ``create_app`` (stored on the app state)."""
    return request.app.state.sql_injection_services


CustomerServices = Annotated[dict[Db, CustomerService], Depends(get_customer_services)]


def get_available_service(db: Db, services: CustomerServices) -> CustomerService:
    """The service for the ``{db}`` path parameter, or HTTP 503 if its database is unavailable."""
    service = services[db]
    reason = service.unavailable_reason()
    if reason is not None:
        raise HTTPException(status_code=503, detail=f"{service.label} is unavailable: {reason}")
    return service


AvailableService = Annotated[CustomerService, Depends(get_available_service)]
