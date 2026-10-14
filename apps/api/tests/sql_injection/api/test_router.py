"""HTTP-level tests through FastAPI's TestClient, backed by the Postgres test database."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from ..samples import APOSTROPHE, malicious


def body(row: Any, parameterized: bool) -> dict[str, Any]:
    return {"row": row.model_dump(), "parameterized": parameterized}


def test_databases(client: TestClient) -> None:
    response = client.get("/api/sql-injection/databases")
    assert response.status_code == 200
    postgres, bigquery = response.json()
    assert postgres == {
        "id": "postgres",
        "label": "Postgres",
        "table": "public.customers",
        "available": True,
        "reason": None,
    }
    assert bigquery["id"] == "bigquery"
    assert bigquery["table"] == "injection_lab.customers"
    assert bigquery["available"] is False
    assert bigquery["reason"]


def test_unavailable_database_returns_503(client: TestClient) -> None:
    response = client.get("/api/sql-injection/bigquery/customers")
    assert response.status_code == 503
    assert "detail" in response.json()
    response = client.post("/api/sql-injection/bigquery/preview", json=body(APOSTROPHE, True))
    assert response.status_code == 503


def test_customers_pagination(client: TestClient) -> None:
    response = client.get("/api/sql-injection/postgres/customers?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 12
    assert (data["page"], data["page_size"]) == (2, 5)
    assert [row["id"] for row in data["rows"]] == [6, 7, 8, 9, 10]
    assert set(data["rows"][0]) == {"id", "name", "email", "country", "plan"}


def test_last_allowed_page_is_empty(client: TestClient) -> None:
    response = client.get("/api/sql-injection/postgres/customers?page=100000&page_size=50")
    assert response.status_code == 200
    assert response.json()["rows"] == []


@pytest.mark.parametrize(
    "url",
    [
        "/api/sql-injection/postgres/customers?page_size=51",
        "/api/sql-injection/postgres/customers?page=0",
        "/api/sql-injection/postgres/customers?page=100001",
        "/api/sql-injection/postgres/customers?page=99999999999999999999",
        "/api/sql-injection/mysql/customers",
    ],
)
def test_invalid_queries_return_422(client: TestClient, url: str) -> None:
    assert client.get(url).status_code == 422


def test_field_longer_than_500_chars_returns_422(client: TestClient) -> None:
    row = APOSTROPHE.model_copy(update={"name": "x" * 501})
    response = client.post("/api/sql-injection/postgres/preview", json=body(row, False))
    assert response.status_code == 422


def test_reset(client: TestClient) -> None:
    client.post("/api/sql-injection/postgres/insert", json=body(APOSTROPHE, True))
    assert client.post("/api/sql-injection/postgres/reset").json() == {"total": 12}


@pytest.mark.parametrize("parameterized", [True, False])
def test_insert_returns_the_previewed_statement(client: TestClient, parameterized: bool) -> None:
    request = body(malicious("public.customers"), parameterized)
    preview = client.post("/api/sql-injection/postgres/preview", json=request).json()
    result = client.post("/api/sql-injection/postgres/insert", json=request).json()
    assert result["statement"] == preview
    assert result["ok"] is True
    assert result["error"] is None
    assert result["total_rows"] == (13 if parameterized else 0)


def test_database_error_is_not_an_http_error(client: TestClient) -> None:
    response = client.post("/api/sql-injection/postgres/insert", json=body(APOSTROPHE, False))
    assert response.status_code == 200
    result = response.json()
    assert result["ok"] is False
    assert "syntax error" in result["error"]
    assert result["rows_affected"] is None
    assert result["total_rows"] == 12
    assert result["statement"]["escaped_fields"] == ["name"]
