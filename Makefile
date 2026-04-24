.PHONY: install lint test up down down-v seed migrate

install:
	poetry install

lint:
	poetry run ruff check .
	poetry run mypy app tests

test:
	poetry run pytest

up:
	docker compose up --build

down:
	docker compose down

down-v:
	docker compose down -v
seed: migrate
	poetry run python -m scripts.seed_data

migrate:
	poetry run alembic upgrade head
