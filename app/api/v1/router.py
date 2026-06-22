from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, verification

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])