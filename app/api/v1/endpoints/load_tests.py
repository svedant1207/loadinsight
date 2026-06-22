from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.load_test import LoadTestCreate, LoadTestResponse
from app.services.load_test_service import LoadTestService
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/{project_id}/run", response_model=LoadTestResponse)
async def run_load_test(
    project_id: str,
    data: LoadTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # verify project belongs to user
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = LoadTestService(db)
    try:
        result = await service.create_and_run(project_id, data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/tests", response_model=list[LoadTestResponse])
async def get_tests(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = LoadTestService(db)
    return await service.get_all_by_project(project_id)

@router.get("/tests/{test_id}", response_model=LoadTestResponse)
async def get_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = LoadTestService(db)
    test = await service.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test