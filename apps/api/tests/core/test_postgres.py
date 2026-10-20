"""Unit tests for the Postgres engine factory (no database needed)."""

from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.postgres import create_postgres_engine


def test_postgres_engine_uses_psycopg_and_a_fresh_session_per_request() -> None:
    settings = Settings(
        database_url="postgresql://app:secret@db:5432/lab", statement_timeout_ms=1234
    )
    engine = create_postgres_engine(settings)
    assert engine is not None
    assert engine.url.drivername == "postgresql+psycopg"
    assert (engine.url.host, engine.url.database) == ("db", "lab")
    assert isinstance(engine.pool, NullPool)
    assert create_postgres_engine(Settings(database_url="")) is None
