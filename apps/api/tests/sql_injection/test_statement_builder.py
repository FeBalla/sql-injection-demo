"""Unit tests for the statement builder: the SQL text and bound params (no database needed)."""

import pytest

from app.modules.sql_injection.schemas import CustomerIn, Db

from .samples import APOSTROPHE, PLAIN_ROW, build, malicious, segments


def test_postgres_parameterized_shape() -> None:
    statement = build("postgres", APOSTROPHE, parameterized=True)
    assert statement.sql == (
        "INSERT INTO customers (name, email, country, plan)\nVALUES ($1, $2, $3, $4);"
    )
    assert [(p.placeholder, p.column, p.type, p.value) for p in statement.params] == [
        ("$1", "name", "text", "Bernardo O'Higgins"),
        ("$2", "email", "text", "bohiggins@example.cl"),
        ("$3", "country", "text", "CL"),
        ("$4", "plan", "text", "pro"),
    ]
    assert segments(statement, 1) == [
        ("VALUES", "keyword"),
        (" (", "plain"),
        ("$1", "param"),
        (", ", "plain"),
        ("$2", "param"),
        (", ", "plain"),
        ("$3", "param"),
        (", ", "plain"),
        ("$4", "param"),
        (");", "plain"),
    ]


def test_bigquery_parameterized_shape() -> None:
    statement = build("bigquery", APOSTROPHE, parameterized=True)
    assert statement.sql == (
        "INSERT INTO `injection_lab.customers` (id, name, email, country, plan)\n"
        "VALUES (\n"
        "  (SELECT COALESCE(MAX(id), 0) + 1 FROM `injection_lab.customers`),\n"
        "  @name, @email, @country, @plan\n"
        ");"
    )
    assert [p.placeholder for p in statement.params] == ["@name", "@email", "@country", "@plan"]
    assert {p.type for p in statement.params} == {"STRING"}
    assert segments(statement, 2) == [
        ("  (", "plain"),
        ("SELECT", "keyword"),
        (" COALESCE(MAX(id), 0) + 1 ", "plain"),
        ("FROM", "keyword"),
        (" `injection_lab.customers`),", "plain"),
    ]


def test_concatenated_shapes() -> None:
    values = "  'Ana Pérez',\n  'aperez@example.cl',\n  'CL',\n  'free'\n);"
    assert build("postgres", PLAIN_ROW, parameterized=False).sql == (
        "INSERT INTO customers (name, email, country, plan)\nVALUES (\n" + values
    )
    assert build("bigquery", PLAIN_ROW, parameterized=False).sql == (
        "INSERT INTO `injection_lab.customers` (id, name, email, country, plan)\n"
        "VALUES (\n"
        "  (SELECT COALESCE(MAX(id), 0) + 1 FROM `injection_lab.customers`),\n" + values
    )


@pytest.mark.parametrize("db", ["postgres", "bigquery"])
@pytest.mark.parametrize("row", [APOSTROPHE, malicious("public.customers")])
def test_parameterized_sql_contains_no_user_text(db: Db, row: CustomerIn) -> None:
    statement = build(db, row, parameterized=True)
    for value in (row.name, row.email, row.country, row.plan):
        assert value not in statement.sql
    assert statement.statement_count == 1
    assert statement.escaped_fields == []
    kinds = {segment.kind for line in statement.lines for segment in line}
    assert not kinds & {"input", "escaped"}


@pytest.mark.parametrize("db", ["postgres", "bigquery"])
def test_harmless_input_stays_inside_its_literal(db: Db) -> None:
    statement = build(db, PLAIN_ROW, parameterized=False)
    assert statement.statement_count == 1
    assert statement.escaped_fields == []
    assert statement.params == []
