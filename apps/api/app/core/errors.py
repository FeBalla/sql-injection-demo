"""Errors shared by both databases."""


class DatabaseUnavailableError(Exception):
    """The database is not configured or cannot be reached (served as HTTP 503)."""
