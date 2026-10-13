"""Turning BigQuery failures into what the demo shows: HTTP 503 or a redacted error message.

Failing to authenticate or to reach the API means the database is unavailable (HTTP 503), as
opposed to a query error, which is the database's answer to the demo SQL and is shown to the
user without anything that identifies the GCP project (this is a public demo).
"""

import re
from collections.abc import Iterator
from contextlib import contextmanager

import requests
from google.api_core.exceptions import RetryError
from google.auth.exceptions import GoogleAuthError

from ..protocol import DatabaseUnavailableError

UNAVAILABLE_ERRORS = (GoogleAuthError, requests.exceptions.RequestException, RetryError)
"""Authentication and transport failures. RetryError is what api_core raises once retries of a
connection failure run out."""

_SERVICE_ACCOUNT = re.compile(r"[\w.+-]+@[\w.-]+\.iam\.gserviceaccount\.com")


@contextmanager
def unavailable_on_transport_errors() -> Iterator[None]:
    """Re-raise :data:`UNAVAILABLE_ERRORS` as :class:`DatabaseUnavailableError`."""
    try:
        yield
    except UNAVAILABLE_ERRORS as exc:
        # The original message is not passed on: it can name the project or service account.
        raise DatabaseUnavailableError(
            "BigQuery is unavailable: could not authenticate or reach the API."
        ) from exc


def redacted_error_message(exc: Exception, project: str) -> str:
    """The database's own message, without the job id, location, query dump, project id or
    service account email."""
    errors = getattr(exc, "errors", None)
    if errors and isinstance(errors[0], dict) and errors[0].get("message"):
        message = str(errors[0]["message"])
    else:
        message = getattr(exc, "message", None) or str(exc)
    message = _SERVICE_ACCOUNT.sub("<service-account>", message)
    return message.replace(project, "<project>") if project else message
