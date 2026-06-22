from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Project

class ProjectRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: str) -> list[Project]:
        result = await self.db.execute(select(Project).where(Project.user_id == user_id))
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)