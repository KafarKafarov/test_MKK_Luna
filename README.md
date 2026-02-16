# Orgs API (тестовое)

API для поиска организаций по названию, зданию, виду деятельности (с дочерними до 3 уровней) и геопоиска (радиус/прямоугольник).
Стек: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + Postgres. Авторизация — статический API key.

## Требования
- Docker + Docker Compose
- (локально) Poetry 1.7+ (по желанию, если запускать не в docker)

## Быстрый старт (Docker)
1) Создай `.env` в корне проекта:

```env
DATABASE_URL=postgresql+psycopg://orgs:1234@db:5432/orgs
API_KEY=supersecret
