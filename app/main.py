from fastapi import FastAPI

from app.api import router

app = FastAPI(title="Organizations API")
app.include_router(router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
