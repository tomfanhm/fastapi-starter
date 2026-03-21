.PHONY: install run test lint format migrate migration docker-up docker-down

install:
	poetry install

run:
	poetry run uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest --cov=app --cov-report=term-missing

lint:
	poetry run ruff check .
	poetry run ruff format --check .
	poetry run mypy app/

format:
	poetry run ruff format .
	poetry run ruff check --fix .

migrate:
	poetry run alembic upgrade head

migration:
	poetry run alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v
