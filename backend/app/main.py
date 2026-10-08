from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.db.database import create_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database()
    yield


app = FastAPI(
    title="CareerTwin AI API",
    description="API foundation for the CareerTwin AI academic prototype.",
    version="0.1.0",
    lifespan=lifespan,
)


def _cors_origins() -> list[str]:
    configured = os.getenv("CORS_ORIGINS")
    if configured is None:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    origins = [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ORIGINS must contain explicit origins when credentialed requests are enabled.")
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/health", tags=["health"])
def root_health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def safe_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    # FastAPI's default validation payload can echo submitted values, including passwords.
    detail = [
        {"loc": list(item.get("loc", ())), "msg": item.get("msg", "Invalid input."), "type": item.get("type", "value_error")}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})
