from fastapi import FastAPI

from app.api import router

app = FastAPI(
    title="Organizations API",
    description="API для организаций/зданий/деятельностей. Авторизация: X-API-Key.",
)
app.include_router(router)


@app.get("/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
