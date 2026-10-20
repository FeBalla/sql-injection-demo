# Development

Every command runs through Docker Compose. The `Makefile` wraps the common ones:

| Command | What it does |
| --- | --- |
| `make up` / `make down` | Start or stop the stack (`up` rebuilds and renews `node_modules`) |
| `make check` | Everything below |
| `make lint-api` | `ruff check` + `ruff format --check` |
| `make test-api` | pytest against the Postgres container (separate `injection_lab_test` database) |
| `make lint-web` | ESLint + Prettier |
| `make typecheck-web` / `make build-web` | `tsc --noEmit` / `next build` |
| `make format` | Format both apps |
| `make gitleaks` | Scan the full git history for secrets |

BigQuery integration tests are marked `bigquery` and skip automatically without credentials. With BigQuery enabled, they run against a throwaway `customers_test` table.

## Connecting to Postgres

Postgres listens on `localhost:5432` (bound to localhost only), so psql or pgAdmin can connect to the `injection_lab` database with either role:

| Role | Password | Use it to |
| --- | --- | --- |
| `POSTGRES_USER` (`lab_owner`) | `POSTGRES_PASSWORD` (`lab_owner_local`) | Administer everything; it owns the `customers` table |
| `APP_DB_USER` (`lab_app`) | `APP_DB_PASSWORD` (`lab_app_local`) | See exactly what the API (and any injected SQL) can do |

The defaults are in parentheses. Postgres applies these values only when its volume is first created, so after changing them run `docker compose down -v`, which deletes the data.

## Secret hygiene

This repo is public, so secrets are kept out mechanically:

- Configuration comes from environment variables, and `.env` files and credential JSON are git-ignored.
- A pre-commit hook runs [gitleaks](https://github.com/gitleaks/gitleaks) in Docker on staged changes. Enable it once per clone:

  ```bash
  git config core.hooksPath .githooks
  ```
