import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.pipeline import PipelineCreate, PipelineResponse, PipelineStepResponse
from app.models.pipeline import Pipeline, PipelineStep

class PipelineService:

    def __init__(self, db: AsyncSession):
        self.repository = PipelineRepository(db)

    async def create(self, project_id: str, data: PipelineCreate) -> PipelineResponse:
        pipeline = Pipeline(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=data.name,
        )
        pipeline = await self.repository.create_pipeline(pipeline)

        steps = []
        for step_data in sorted(data.steps, key=lambda x: x.step_order):
            step = PipelineStep(
                id=str(uuid.uuid4()),
                pipeline_id=pipeline.id,
                step_order=step_data.step_order,
                name=step_data.name,
                url=step_data.url,
                http_method=step_data.http_method,
                request_headers=json.dumps(step_data.request_headers) if step_data.request_headers else None,
                request_body=json.dumps(step_data.request_body) if step_data.request_body else None,
            )
            step = await self.repository.create_step(step)
            steps.append(PipelineStepResponse.model_validate(step))

        return PipelineResponse(
            id=pipeline.id,
            project_id=pipeline.project_id,
            name=pipeline.name,
            created_at=pipeline.created_at,
            steps=steps,
        )

    async def get(self, pipeline_id: str) -> PipelineResponse | None:
        pipeline = await self.repository.get_by_id(pipeline_id)
        if not pipeline:
            return None
        steps = await self.repository.get_steps(pipeline_id)
        return PipelineResponse(
            id=pipeline.id,
            project_id=pipeline.project_id,
            name=pipeline.name,
            created_at=pipeline.created_at,
            steps=[PipelineStepResponse.model_validate(s) for s in steps],
        )

    async def get_all(self, project_id: str) -> list[PipelineResponse]:
        pipelines = await self.repository.get_all_by_project(project_id)
        result = []
        for pipeline in pipelines:
            steps = await self.repository.get_steps(pipeline.id)
            result.append(PipelineResponse(
                id=pipeline.id,
                project_id=pipeline.project_id,
                name=pipeline.name,
                created_at=pipeline.created_at,
                steps=[PipelineStepResponse.model_validate(s) for s in steps],
            ))
        return result