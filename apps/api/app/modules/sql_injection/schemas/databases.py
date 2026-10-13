"""The databases behind the demo, as listed and reset by the API."""

from typing import Literal

from pydantic import BaseModel

Db = Literal["postgres", "bigquery"]
"""Identifies a database in URLs (``/api/sql-injection/{db}/...``) and responses."""


class DatabaseInfo(BaseModel):
    id: Db
    label: str
    table: str
    available: bool
    reason: str | None


class ResetResult(BaseModel):
    total: int
