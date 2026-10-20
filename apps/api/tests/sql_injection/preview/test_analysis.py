"""Unit tests for the SQL analysis behind the preview: highlighting, escapes, statement count."""

import pytest

from app.sql_injection.models import CustomerIn, Db
from app.sql_injection.preview import StatementPreview
from app.sql_injection.preview.analysis import analyze
from app.sql_injection.preview.sql_syntax import DIALECTS, count_statements, tokenize

from ..samples import APOSTROPHE, PLAIN_ROW, build, malicious, segments

DELETE_TARGETS: dict[Db, str] = {
    "postgres": "public.customers",
    "bigquery": "injection_lab.customers",
}


def rebuild(statement: StatementPreview) -> str:
    return "\n".join("".join(segment.text for segment in line) for line in statement.lines)


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
        CustomerIn(name="$$;'$$", email="$tag$ x';$tag$", country="/* /* */ ; */", plan="$1 $a"),
        CustomerIn(name="r'\\'", email='R"""x"""', country="E'\\''", plan="rb'; br\"'"),
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
        # Postgres dollar quoting (no escapes inside; other tags and `$1` are plain text).
        ("postgres", "SELECT $$a;b$$; SELECT 2", 2),
        ("postgres", "SELECT $tag$ it's; $$ $other$ ; $tag$; SELECT 2", 2),
        ("postgres", "SELECT $_t1$ \\$_t1$; SELECT 2", 2),
        ("postgres", "SELECT $$unterminated; DELETE FROM t", 1),
        ("postgres", "SELECT $1; SELECT $2", 2),
        ("postgres", "SELECT a$$b; SELECT 2", 2),  # `$` inside an identifier quotes nothing
        # Postgres block comments nest; BigQuery's do not.
        ("postgres", "/* outer /* inner */ still a comment; */ SELECT 1", 1),
        ("postgres", "SELECT 1 /* /* */ ; */; SELECT 2", 2),
        ("postgres", "SELECT 1 /* /* */ unterminated; SELECT 2", 1),
        ("bigquery", "SELECT 1 /* /* */ ; */", 2),
        # Postgres E'' strings accept backslash escapes; standard strings do not.
        ("postgres", "SELECT E'it\\'s; fine'; SELECT 2", 2),
        ("postgres", "SELECT e'a\\\\'; SELECT 2", 2),
        ("postgres", "SELECT 'a\\'; SELECT 2", 2),
        # BigQuery raw/bytes prefixes: backslashes are kept, but an escaped quote still does not
        # close the literal (GoogleSQL lexes raw and non-raw strings the same way).
        ("bigquery", "SELECT r'a\\'; b'; SELECT 2", 2),
        ("bigquery", 'SELECT R"a\\"; b"; SELECT 2', 2),
        ("bigquery", "SELECT r'''a;\n'; ''' ; SELECT 2", 2),
        ("bigquery", 'SELECT Rb"""x"; """; SELECT 2', 2),
        ("bigquery", "SELECT bR'a;b' FROM t", 1),
        ("bigquery", "SELECT r'unterminated; SELECT 2", 1),
    ],
)
def test_count_statements(db: Db, sql: str, expected: int) -> None:
    assert count_statements(tokenize(sql, DIALECTS[db])) == expected
    lines = analyze([(sql, None)], db).lines
    assert "\n".join("".join(segment.text for segment in line) for line in lines) == sql


@pytest.mark.parametrize(
    ("db", "sql", "expected"),
    [
        (
            "postgres",
            "$1 $$a$$ $t$b$t$ E'c'",
            [("$1", "param"), ("$$a$$", "string"), ("$t$b$t$", "string"), ("E'c'", "string")],
        ),
        (
            "bigquery",
            "@p r'a' RB\"b\" r'''c'''",
            [("@p", "param"), ("r'a'", "string"), ('RB"b"', "string"), ("r'''c'''", "string")],
        ),
    ],
)
def test_prefixed_and_dollar_quoted_strings_are_single_tokens(
    db: Db, sql: str, expected: list[tuple[str, str]]
) -> None:
    tokens = [token for token in tokenize(sql, DIALECTS[db]) if token.kind != "space"]
    assert [(sql[token.start : token.end], token.kind) for token in tokens] == expected


def test_keywords_exclude_function_names() -> None:
    statement = build("bigquery", PLAIN_ROW, parameterized=True)
    keywords = {s.text for line in statement.lines for s in line if s.kind == "keyword"}
    assert keywords == {"INSERT", "INTO", "VALUES", "SELECT", "FROM"}
