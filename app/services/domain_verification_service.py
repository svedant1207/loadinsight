import uuid
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain_verification import DomainVerification
from app.models.project import Project

class DomainVerificationService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_token(self, project_id: str) -> DomainVerification:
        # check if one already exists
        result = await self.db.execute(
            select(DomainVerification).where(DomainVerification.project_id == project_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        verification = DomainVerification(
            id=str(uuid.uuid4()),
            project_id=project_id,
            token=str(uuid.uuid4()),
        )
        self.db.add(verification)
        await self.db.flush()
        await self.db.refresh(verification)
        return verification

    async def verify(self, project_id: str) -> bool:
        # get the verification record
        result = await self.db.execute(
            select(DomainVerification).where(DomainVerification.project_id == project_id)
        )
        verification = result.scalar_one_or_none()
        if not verification:
            raise ValueError("No verification token found. Generate one first.")

        # get the project url
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found.")

        # check if token file exists on the domain
        check_url = f"{project.url}/loadinsight-verify/{verification.token}.txt"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(check_url)
                if response.status_code == 200:
                    verification.is_verified = True
                    verification.verified_at = datetime.utcnow()
                    project.is_verified = True
                    return True
        except Exception:
            pass

        return False