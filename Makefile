.PHONY: install lint test run fmt

install:
	poetry install

fmt:
	poetry run ruff format .

lint:
	poetry run ruff check .
	poetry run mypy app tests

test:
	poetry run pytest

up:
	docker compose up --build

down:
	docker compose down -v
