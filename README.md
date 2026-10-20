# Injection Lab

An interactive demo that shows what SQL injection is and why parameterized queries stop it.

| Concatenated: the apostrophe escapes the string literal | Parameterized: values travel separately |
| --- | --- |
| ![Unsafe preview](docs/screenshots/unsafe-preview.png) | ![Parameterized preview](docs/screenshots/parameterized-preview.png) |

> [!WARNING]
> This project contains **intentionally vulnerable code** (the concatenated queries in `apps/api/app/sql_injection/queries/`). Run it locally against the demo databases only, and never copy that pattern into real code.

## How it works

You fill in a form that inserts a customer row into **Postgres** (or, optionally, **BigQuery**). As you type, the app shows the exact statement the database will receive, built in one of two ways:

- **Concatenated (unsafe):** your input is pasted into the SQL text. The database parses it as SQL, so a quote ends the string early and a `;` starts a new statement.
- **Parameterized (safe):** the SQL text only has placeholders (`$1`, `@name`) and the values are sent separately. They are never parsed, so they can never become SQL.

Nothing is simulated. The preview comes from the same code that runs the INSERT, and the unsafe mode really runs what the concatenation produces. It highlights the input that escaped its string literal and counts how many statements will run. The app connects with a least-privilege role, so an injection can only affect the demo table.

Try these:

1. **`Bernardo O'Higgins`** as the name: the concatenated query fails with a syntax error, while the parameterized one stores the name correctly.
2. **The malicious example:** a `plan` value that turns one INSERT into three statements and deletes every row. Parameterized, it is stored as plain text.
3. **Reset demo data** to bring back the seed rows.

## Quickstart

You only need Docker with Compose v2.

```bash
git clone https://github.com/FeBalla/sql-injection-demo.git
cd sql-injection-demo
docker compose up --build
```

Open http://localhost:3000. The API docs are at http://localhost:8000/docs.

## More

- [Architecture](docs/architecture.md): code layout, API endpoints, how the preview works, the blast radius, and why parameterized queries work
- [BigQuery setup](docs/bigquery.md): adding BigQuery as a second database
- [Development](docs/development.md): `make` commands, tests, and secret hygiene
