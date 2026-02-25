.PHONY: install lint test up down

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
	docker compose down -v
