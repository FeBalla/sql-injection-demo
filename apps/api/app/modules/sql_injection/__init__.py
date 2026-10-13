"""SQL injection demo: the same INSERT, concatenated vs parameterized, on Postgres and BigQuery."""

import logging

from .backends import Backend, DatabaseUnavailableError, create_backends
from .router import router
from .schemas import Db

__all__ = ["DatabaseUnavailableError", "create_backends", "router", "seed_empty_tables"]

logger = logging.getLogger(__name__)


def seed_empty_tables(backends: dict[Db, Backend]) -> None:
    """Load the seed rows into every available database whose table is empty or missing.

    Failures are logged, not raised: the API still starts and reports the error per request.
    """
    for backend in backends.values():
        available, reason = backend.availability()
        if not available:
            logger.info("%s skipped: %s", backend.label, reason)
            continue
        try:
            backend.seed_if_empty()
        except Exception:
            logger.exception("Could not seed %s", backend.label)
