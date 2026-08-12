from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "running"}


@router.get("/version")
def version():
    return {"app": settings.app_name, "version": "0.1.0"}
