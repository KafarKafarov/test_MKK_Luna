# Orgs API (тестовое)

API для поиска организаций по названию, зданию, виду деятельности (с дочерними до 3 уровней) и геопоиска (радиус/прямоугольник).

Стек: FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + Postgres. Авторизация - статический API key.

---

## Возможности

- GET /health - проверка работоспособности сервиса
- Поиск организаций по названию
- Получение организации по id
- Организации в здании
- Организации по виду деятельности (включая дочерние до глубины 3)
- Геопоиск:
  - по радиусу
  - по прямоугольнику

---

## Требования

- Docker + Docker Compose
- (локально) Poetry 1.7+ - опционально, если запускать не в docker

---

## Конфигурация

Создай `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://orgs:1234@localhost:5432/orgs
API_KEY=supersecret
```

Для `docker compose` адрес БД внутри контейнера переопределяется на `db:5432`,
поэтому этот `.env` подходит и для локальных `poetry`/`make` команд, и для docker-сценария.
---

## Поднять окружение для тестов через Docker

```
make up
```
После запуска API доступно:

 - Swagger: http://localhost:8000/docs
 - Health: http://localhost:8000/health
 - Prometheus metrics: http://localhost:8000/metrics
 - Prometheus UI: http://localhost:9090
 - Grafana: http://localhost:3001

---

# Тестовые данные

```
make up
make seed
```

Скрипт создаёт:
- 6 зданий
- 14 видов деятельности
- 8 организаций
- телефоны организаций
- связи организаций с деятельностями
---

## Тесты

```
 make test
```
---

## Авторизация

Все запросы требуют заголовок:
```
X-API-Key: supersecret
```

## Миграции

```
 make migrate
```

## Observability

Ветка наблюдаемости теперь поднимает два контура:

- `Loki + Alloy` для структурированных логов контейнеров
- `Prometheus + Grafana` для HTTP-метрик приложения

Что настроено:

- `/metrics` в FastAPI без `X-API-Key`, чтобы Prometheus мог скрапить сервис внутри docker network
- Счётчик запросов `orgs_api_http_requests_total`
- Гистограмма latency `orgs_api_http_request_duration_seconds`
- Автопровижининг datasource и dashboard в Grafana

Готовый dashboard появляется автоматически в Grafana в папке `Observability`.

Доступы по умолчанию:

- Grafana: `admin` / `admin`

Подробное объяснение схемы и метрик: `observability/README.md`
