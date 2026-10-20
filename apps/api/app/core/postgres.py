"""The Postgres connection: a SQLAlchemy engine over psycopg 3."""

from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.pool import NullPool

from .config import Settings


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
