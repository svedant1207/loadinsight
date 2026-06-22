from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.pipeline import PipelineCreate, PipelineResponse
from app.services.pipeline_service import PipelineService
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/{project_id}/pipelines", response_model=PipelineResponse)
async def create_pipeline(
    project_id: str,
    data: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = PipelineService(db)
    return await service.create(project_id, data)

@router.get("/{project_id}/pipelines", response_model=list[PipelineResponse])
async def get_pipelines(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = PipelineService(db)
    return await service.get_all(project_id)

@router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PipelineService(db)
    pipeline = await service.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline