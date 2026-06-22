from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pipeline import Pipeline, PipelineStep

class PipelineRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_pipeline(self, pipeline: Pipeline) -> Pipeline:
        self.db.add(pipeline)
        await self.db.flush()
        await self.db.refresh(pipeline)
        return pipeline

    async def create_step(self, step: PipelineStep) -> PipelineStep:
        self.db.add(step)
        await self.db.flush()
        await self.db.refresh(step)
        return step

    async def get_by_id(self, pipeline_id: str) -> Pipeline | None:
        result = await self.db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        return result.scalar_one_or_none()

    async def get_steps(self, pipeline_id: str) -> list[PipelineStep]:
        result = await self.db.execute(
            select(PipelineStep)
            .where(PipelineStep.pipeline_id == pipeline_id)
            .order_by(PipelineStep.step_order)
        )
        return list(result.scalars().all())

    async def get_all_by_project(self, project_id: str) -> list[Pipeline]:
        result = await self.db.execute(
            select(Pipeline).where(Pipeline.project_id == project_id)
        )
        return list(result.scalars().all())