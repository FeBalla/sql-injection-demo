"""SQL injection demo: the same INSERT, concatenated vs parameterized, on Postgres and BigQuery.

This is the module's public surface, used by ``app.main``: the router, the databases it needs
on the app state, the error served as HTTP 503 and the startup seeding.
"""

import logging

from .databases.protocol import Database, DatabaseUnavailableError
from .databases.registry import create_databases
from .routes import router
from .schemas import Db

__all__ = ["DatabaseUnavailableError", "create_databases", "router", "seed_empty_tables"]

logger = logging.getLogger(__name__)


def seed_empty_tables(databases: dict[Db, Database]) -> None:
    """Load the seed rows into every available database whose table is empty or missing.

    Failures are logged, not raised: the API still starts and reports the error per request.
    """
    for database in databases.values():
        available, reason = database.availability()
        if not available:
            logger.info("%s skipped: %s", database.label, reason)
            continue
        try:
            database.seed_if_empty()
        except Exception:
            logger.exception("Could not seed %s", database.label)
