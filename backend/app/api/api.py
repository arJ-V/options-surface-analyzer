from fastapi import APIRouter
from app.api.endpoints import surface

api_router = APIRouter()
api_router.include_router(surface.router, prefix="/surface", tags=["surface"])