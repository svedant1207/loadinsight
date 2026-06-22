from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.load_test import LoadTestCreate, LoadTestResponse
from app.services.load_test_service import LoadTestService
from app.services.project_service import ProjectService
from app.engine.load_tester import run_pipeline_load_test
from app.repositories.pipeline_repository import PipelineRepository
import json

router = APIRouter()

@router.post("/{project_id}/run", response_model=LoadTestResponse)
async def run_load_test(
    project_id: str,
    data: LoadTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

@router.post("/pipeline/{pipeline_id}/run")
async def run_pipeline_test(
    pipeline_id: str,
    data: LoadTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pipeline_repo = PipelineRepository(db)
    pipeline = await pipeline_repo.get_by_id(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(pipeline.project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    steps_raw = await pipeline_repo.get_steps(pipeline_id)
    steps = [
        {
            "url": step.url,
            "method": step.http_method,
            "headers": json.loads(step.request_headers) if step.request_headers else None,
            "body": json.loads(step.request_body) if step.request_body else None,
        }
        for step in steps_raw
    ]

    metrics = await run_pipeline_load_test(
        steps=steps,
        virtual_users=data.virtual_users,
        duration_seconds=data.duration_seconds,
        ramp_up_seconds=data.ramp_up_seconds,
    )

    return {
        "pipeline_id": pipeline_id,
        "pipeline_name": pipeline.name,
        "virtual_users": data.virtual_users,
        "duration_seconds": data.duration_seconds,
        "steps_count": len(steps),
        "metrics": metrics,
    }