"""Customer rows: the demo table's columns and the models used to write and page through it."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

Column = Literal["name", "email", "country", "plan"]

COLUMNS: tuple[Column, ...] = ("name", "email", "country", "plan")
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


class CustomerPage(BaseModel):
    rows: list[Customer]
    total: int
    page: int
    page_size: int
