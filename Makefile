.PHONY: install dev lint format typecheck test security docker-up docker-down migrate quality frontend-install frontend-dev

install:
	poetry install --with dev

dev:
	poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

lint:
	poetry run ruff check backend
	poetry run ruff format --check backend

format:
	poetry run ruff check --fix backend
	poetry run ruff format backend

typecheck:
	poetry run mypy -p backend

test:
	poetry run pytest backend/tests --cov=backend --cov-report=xml -q

security:
	poetry run bandit -r backend -x backend/tests -ll
	poetry run pip-audit || true

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

migrate:
	poetry run alembic upgrade head

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

quality: lint typecheck test security
