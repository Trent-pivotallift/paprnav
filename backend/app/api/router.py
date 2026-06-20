from fastapi import APIRouter

from app.api.routes import ads, aircraft, auth, health, ingestion, logbook_entries, observability, root, uploads

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(aircraft.router)
api_router.include_router(logbook_entries.router)
api_router.include_router(uploads.router)
api_router.include_router(uploads.download_router)
api_router.include_router(ingestion.router)
api_router.include_router(ads.router)
api_router.include_router(observability.router)
