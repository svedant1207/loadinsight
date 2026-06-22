from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.domain_verification_service import DomainVerificationService
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/{project_id}/generate-token")
async def generate_token(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # make sure project belongs to user
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = DomainVerificationService(db)
    verification = await service.generate_token(project_id)
    return {
        "token": verification.token,
        "instruction": f"Create a file at: {'{your_domain}'}/loadinsight-verify/{verification.token}.txt"
    }

@router.post("/{project_id}/verify")
async def verify_domain(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service = ProjectService(db)
    try:
        await project_service.get_by_id(project_id, current_user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    service = DomainVerificationService(db)
    try:
        verified = await service.verify(project_id)
        if verified:
            return {"message": "Domain verified successfully"}
        return {"message": "Verification failed. Make sure the file exists on your domain."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))