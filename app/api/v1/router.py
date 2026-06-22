from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, verification, load_tests, pipelines

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])
api_router.include_router(load_tests.router, prefix="/load-tests", tags=["Load Tests"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])