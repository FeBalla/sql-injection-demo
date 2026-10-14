"""The demo's customers: their columns, the rows read and written, and the Postgres table."""

from typing import Annotated, Literal

import sqlalchemy as sa
from pydantic import BaseModel, Field

Db = Literal["postgres", "bigquery"]
"""Identifies a database in URLs (``/api/sql-injection/{db}/...``) and responses."""

ColumnName = Literal["name", "email", "country", "plan"]

COLUMNS: tuple[ColumnName, ...] = ("name", "email", "country", "plan")
"""The user-editable columns, in the order the INSERT lists them."""

FieldValue = Annotated[str, Field(max_length=500)]


class CustomerIn(BaseModel):
    name: FieldValue
    email: FieldValue
    country: FieldValue
    plan: FieldValue


class Customer(BaseModel):
    id: int
    name: str
    email: str
    country: str
    plan: str


metadata = sa.MetaData()

customers = sa.Table(
    "customers",
    metadata,
    sa.Column("id", sa.Integer, sa.Identity(), primary_key=True),
    sa.Column("name", sa.Text, nullable=False),
    sa.Column("email", sa.Text, nullable=False),
    sa.Column("country", sa.Text, nullable=False),
    sa.Column("plan", sa.Text, nullable=False),
    schema="public",
)
"""The Postgres table. It is created by infra/postgres/init/01-schema.sh, owned by another role
(so the app role cannot DROP or ALTER it), and never by the app."""
