import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate
from app.models.project import Project

class ProjectService:

    def __init__(self, db: AsyncSession):
        self.repository = ProjectRepository(db)

    async def create(self, user_id: str, data: ProjectCreate) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.name,
            description=data.description,
            url=data.url,
        )
        return await self.repository.create(project)

    async def get_all(self, user_id: str) -> list[Project]:
        return await self.repository.get_all_by_user(user_id)

    async def get_by_id(self, project_id: str, user_id: str) -> Project:
        project = await self.repository.get_by_id(project_id)
        if not project or project.user_id != user_id:
            raise ValueError("Project not found")
        return project

    async def delete(self, project_id: str, user_id: str) -> None:
        project = await self.get_by_id(project_id, user_id)
        await self.repository.delete(project)