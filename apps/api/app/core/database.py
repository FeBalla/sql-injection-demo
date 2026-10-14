"""Connections to the two databases: a SQLAlchemy engine for Postgres, a client for BigQuery."""

import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.pool import NullPool

from .config import Settings

MAX_BYTES_BILLED = 100 * 1024 * 1024
"""Injected SQL runs with the project's job permissions, so cap what any single query may scan
(e.g. a public dataset). The demo table itself is tiny."""


class DatabaseUnavailableError(Exception):
    """The database is not configured or cannot be reached (served as HTTP 503)."""


def create_postgres_engine(settings: Settings) -> Engine | None:
    """The engine for the least-privilege app role, or None if DATABASE_URL is not set.

    DATABASE_URL is a plain libpq URL (``postgresql://...``, usable by psql too); only the engine
    needs to know the driver. NullPool gives every request a fresh session that is closed
    afterwards, so whatever the demo SQL changes in its session (``SET statement_timeout = 0``,
    ``search_path``...) never reaches the next request.
    """
    if not settings.database_url:
        return None
    return create_engine(
        make_url(settings.database_url).set(drivername="postgresql+psycopg"),
        poolclass=NullPool,
        connect_args={
            "connect_timeout": 5,
            # A session default only: the demo SQL can change it, hence the client-side
            # watchdog in the repository too.
            "options": f"-c statement_timeout={settings.statement_timeout_ms}",
        },
    )


def create_bigquery_client(settings: Settings) -> bigquery.Client | str:
    """The client, or the reason BigQuery is unavailable.

    Every query job it starts is capped (time and bytes billed) by its default job config,
    which ``client.query`` merges into the config of each call.
    """
    if not settings.gcp_project_id:
        return "GCP_PROJECT_ID is not set."
    try:
        credentials, _ = google.auth.default()
    except DefaultCredentialsError:
        return "No Google Cloud credentials found (Application Default Credentials)."
    return bigquery.Client(
        project=settings.gcp_project_id,
        location=settings.bq_location,
        credentials=credentials,
        default_query_job_config=bigquery.QueryJobConfig(
            maximum_bytes_billed=MAX_BYTES_BILLED,
            job_timeout_ms=settings.bq_job_timeout_ms,
        ),
    )
