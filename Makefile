# Thin wrappers around docker compose. Nothing runs on the host directly.
.PHONY: up down logs check lint-api test-api test-api-bigquery lint-web typecheck-web build-web format gitleaks

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

check: lint-api test-api lint-web typecheck-web build-web

lint-api:
	docker compose run --rm --no-deps api sh -c "uv run ruff check . && uv run ruff format --check ."

test-api:
	docker compose run --rm api uv run pytest

lint-web:
	docker compose run --rm --no-deps web sh -c "npm run lint && npm run format:check"

typecheck-web:
	docker compose run --rm --no-deps web npm run typecheck

build-web:
	docker compose run --rm --no-deps web npm run build

format:
	docker compose run --rm --no-deps api uv run ruff format .
	docker compose run --rm --no-deps web npm run format

gitleaks:
	scripts/gitleaks.sh git
