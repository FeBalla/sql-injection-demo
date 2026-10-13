"""Unit tests for the statement builder and the preview highlighter (no database needed)."""

import pytest

from app.modules.sql_injection.highlight import count_statements, tokenize
from app.modules.sql_injection.schemas import CustomerIn, Db, StatementPreview
from app.modules.sql_injection.statements import build_statement

from .samples import APOSTROPHE, malicious

TABLES: dict[Db, str] = {"postgres": "customers", "bigquery": "injection_lab.customers"}
DELETE_TARGETS: dict[Db, str] = {
    "postgres": "public.customers",
    "bigquery": "injection_lab.customers",
}
PLAIN_ROW = CustomerIn(name="Ana Pérez", email="aperez@example.cl", country="CL", plan="free")


def build(db: Db, row: CustomerIn, parameterized: bool) -> StatementPreview:
    return build_statement(db, row, parameterized, TABLES[db])


def segments(statement: StatementPreview, line: int) -> list[tuple[str, str]]:
    return [(segment.text, segment.kind) for segment in statement.lines[line]]


def rebuild(statement: StatementPreview) -> str:
    return "\n".join("".join(segment.text for segment in line) for line in statement.lines)


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


@pytest.mark.parametrize("db", ["postgres", "bigquery"])
def test_apostrophe_escapes_the_name_literal(db: Db) -> None:
    statement = build(db, APOSTROPHE, parameterized=False)
    assert statement.statement_count == 1
    assert statement.escaped_fields == ["name"]
    name_line = 3 if db == "bigquery" else 2
    assert segments(statement, name_line) == [
        ("  ", "plain"),
        ("'", "string"),
        ("Bernardo O", "input"),
        ("'Higgins", "escaped"),
        ("',", "string"),
    ]


@pytest.mark.parametrize("db", ["postgres", "bigquery"])
def test_malicious_plan_injects_two_statements(db: Db) -> None:
    statement = build(db, malicious(DELETE_TARGETS[db]), parameterized=False)
    assert statement.statement_count == 3
    assert statement.escaped_fields == ["plan"]
    plan_line = segments(statement, len(statement.lines) - 2)
    assert plan_line[:3] == [("  ", "plain"), ("'", "string"), ("free", "input")]
    assert plan_line[3] == (
        f"'); DELETE FROM {DELETE_TARGETS[db]} WHERE TRUE; SELECT ('",
        "escaped",
    )
    assert plan_line[4:] == [("'", "string")]
    assert segments(statement, len(statement.lines) - 1) == [(");", "plain")]


def test_bigquery_trailing_backslash_swallows_the_closing_quote() -> None:
    row = PLAIN_ROW.model_copy(update={"name": "Ana\\"})
    statement = build("bigquery", row, parameterized=False)
    assert statement.escaped_fields == ["name"]
    assert segments(statement, 3) == [
        ("  ", "plain"),
        ("'", "string"),
        ("Ana", "input"),
        ("\\", "escaped"),
        ("',", "string"),
    ]
    # The backslash is a plain character in Postgres strings.
    assert build("postgres", row, parameterized=False).escaped_fields == []


def test_postgres_trailing_quote_swallows_the_closing_quote() -> None:
    row = PLAIN_ROW.model_copy(update={"name": "Ana'"})
    statement = build("postgres", row, parameterized=False)
    assert statement.escaped_fields == ["name"]
    assert ("'", "escaped") in segments(statement, 2)


@pytest.mark.parametrize(("db", "name"), [("postgres", "O''Higgins"), ("bigquery", "O\\'Higgins")])
def test_correctly_escaped_quotes_stay_inside_the_literal(db: Db, name: str) -> None:
    statement = build(db, PLAIN_ROW.model_copy(update={"name": name}), parameterized=False)
    assert statement.escaped_fields == []
    assert statement.statement_count == 1


def test_bigquery_leading_quotes_open_a_triple_quoted_string() -> None:
    row = PLAIN_ROW.model_copy(update={"name": "''Ana"})
    assert build("bigquery", row, parameterized=False).escaped_fields == ["name"]


@pytest.mark.parametrize("db", ["postgres", "bigquery"])
@pytest.mark.parametrize("parameterized", [True, False])
@pytest.mark.parametrize(
    "row",
    [
        PLAIN_ROW,
        APOSTROPHE,
        malicious("public.customers"),
        CustomerIn(name="multi\nline", email="", country="--", plan="/* x"),
    ],
)
def test_segments_rebuild_the_exact_sql(db: Db, parameterized: bool, row: CustomerIn) -> None:
    statement = build(db, row, parameterized)
    assert rebuild(statement) == statement.sql
    assert all(segment.text for line in statement.lines for segment in line)


@pytest.mark.parametrize(
    ("db", "sql", "expected"),
    [
        ("postgres", "SELECT 1; SELECT ';'", 2),
        ("postgres", "SELECT 1;;  ; -- just a comment ;\n", 1),
        ("postgres", "SELECT 'it''s; fine'", 1),
        ("postgres", 'SELECT "a;b" FROM t; /* ; */ SELECT 2;', 2),
        ("postgres", "SELECT 'unterminated; DELETE FROM t", 1),
        ("bigquery", "SELECT 'it\\'s; fine'; SELECT 2", 2),
        ("bigquery", "SELECT '''a;\n';b''' # ; comment", 1),
        ("bigquery", 'SELECT 1 FROM `a;b`; SELECT "x;"', 2),
        ("bigquery", "", 0),
    ],
)
def test_count_statements(db: Db, sql: str, expected: int) -> None:
    assert count_statements(tokenize(sql, db)) == expected


def test_keywords_exclude_function_names() -> None:
    statement = build("bigquery", PLAIN_ROW, parameterized=True)
    keywords = {s.text for line in statement.lines for s in line if s.kind == "keyword"}
    assert keywords == {"INSERT", "INTO", "VALUES", "SELECT", "FROM"}
