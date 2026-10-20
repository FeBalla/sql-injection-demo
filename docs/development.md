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

## Secret hygiene

This repo is public, so secrets are kept out mechanically:

- Configuration comes from environment variables, and `.env` files and credential JSON are git-ignored.
- A pre-commit hook runs [gitleaks](https://github.com/gitleaks/gitleaks) in Docker on staged changes. Enable it once per clone:

  ```bash
  git config core.hooksPath .githooks
  ```
