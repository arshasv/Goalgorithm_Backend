from collections.abc import Generator
from contextlib import asynccontextmanager


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.api.routes.presentation_round_routes import router as presentation_round_router
from app.api.judge_routes import router as judge_router
from app.api.health_routes import router as health_router
from app.config import settings
from app.database.base import Base
from app.database.connection import engine
import app.models  # noqa: F401 — register ORM models with Base.metadata

api_router.include_router(judge_router)
api_router.include_router(presentation_round_router)

from app.model_execution.routes.execution_routes import router as execution_router
api_router.include_router(execution_router)

from app.model_execution.routes.batch_execution_routes import router as batch_execution_router
api_router.include_router(batch_execution_router)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> Generator:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Organizer-side backend for evaluating AI prediction teams in the FIFA AI Match Prediction Challenge.",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, login, and profile management. All authenticated endpoints require a JWT Bearer token.",
        },
        {
            "name": "health",
            "description": "Health check and version endpoints.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_prefix)

