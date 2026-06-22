import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.load_test import LoadTest, TestStatus
from app.models.project import Project
from app.schemas.load_test import LoadTestCreate
from app.engine.load_tester import run_load_test

class LoadTestService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_run(self, project_id: str, data: LoadTestCreate) -> LoadTest:
        # get project url
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        if not project.is_verified:
            raise ValueError("Domain is not verified. Verify your domain first.")

        # create load test record
        load_test = LoadTest(
            id=str(uuid.uuid4()),
            project_id=project_id,
            virtual_users=data.virtual_users,
            duration_seconds=data.duration_seconds,
            ramp_up_seconds=data.ramp_up_seconds,
            request_rate=data.request_rate,
            status=TestStatus.running,
            started_at=datetime.utcnow(),
        )
        self.db.add(load_test)
        await self.db.flush()

        # run the test
        metrics = await run_load_test(
            url=project.url,
            virtual_users=data.virtual_users,
            duration_seconds=data.duration_seconds,
            ramp_up_seconds=data.ramp_up_seconds,
        )

        # save results
        load_test.status = TestStatus.completed
        load_test.completed_at = datetime.utcnow()
        load_test.total_requests = metrics["total_requests"]
        load_test.successful_requests = metrics["successful_requests"]
        load_test.failed_requests = metrics["failed_requests"]
        load_test.avg_response_time = metrics["avg_response_time"]
        load_test.min_response_time = metrics["min_response_time"]
        load_test.max_response_time = metrics["max_response_time"]
        load_test.p50 = metrics["p50"]
        load_test.p90 = metrics["p90"]
        load_test.p95 = metrics["p95"]
        load_test.p99 = metrics["p99"]
        load_test.throughput = metrics["throughput"]
        load_test.error_rate = metrics["error_rate"]
        load_test.timeout_count = metrics["timeout_count"]

        return load_test

    async def get_all_by_project(self, project_id: str) -> list[LoadTest]:
        result = await self.db.execute(
            select(LoadTest).where(LoadTest.project_id == project_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, test_id: str) -> LoadTest | None:
        result = await self.db.execute(select(LoadTest).where(LoadTest.id == test_id))
        return result.scalar_one_or_none()