from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def read_health():
    return {"status": "ok"}


@router.get("/version")
def read_version():
    settings = get_settings()
    return {"app": settings.app_name, "version": settings.app_version}
