from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.worker.tasks import run_auth_scenario_task
from celery import group

router = APIRouter()

class ScenarioRequest(BaseModel):
    virtual_users: int
    duration_seconds: int
    ramp_up_seconds: int = 0
    base_url: str = "http://localhost:8000"
    cleanup: bool = True
    max_concurrent: int = 50
    workers: int = 4  # how many celery workers to split load across

@router.post("/auth")
async def run_auth_load_scenario(
    data: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # split virtual users across workers
    users_per_worker = data.virtual_users // data.workers
    remaining = data.virtual_users % data.workers

    # create a group of celery tasks
    tasks = []
    for i in range(data.workers):
        # give remaining users to last worker
        users = users_per_worker + (remaining if i == data.workers - 1 else 0)
        tasks.append(
            run_auth_scenario_task.s(
                base_url=data.base_url,
                virtual_users=users,
                duration_seconds=data.duration_seconds,
                ramp_up_seconds=data.ramp_up_seconds,
                max_concurrent=data.max_concurrent // data.workers,
            )
        )

    # dispatch all tasks and wait for results
    job = group(tasks)
    result = job.apply_async()

    # wait for all workers to finish
    results = result.get(timeout=data.duration_seconds + 60)

    # merge results from all workers
    merged = merge_results(results, data.duration_seconds)

    # cleanup fake users
    cleaned_up = 0
    if data.cleanup and merged.get("registered_emails"):
        from app.models.user import User as UserModel
        stmt = delete(UserModel).where(
            UserModel.email.in_(merged["registered_emails"])
        )
        res = await db.execute(stmt)
        cleaned_up = res.rowcount
        await db.commit()

    return {
        "scenario": "auth",
        "virtual_users": data.virtual_users,
        "workers_used": data.workers,
        "duration_seconds": data.duration_seconds,
        "metrics": merged,
        "cleanup": {
            "fake_users_created": len(merged.get("registered_emails", [])),
            "fake_users_deleted": cleaned_up,
        }
    }


def merge_results(results: list, duration_seconds: int) -> dict:
    """Merge metrics from all workers into one result."""
    import statistics

    total_requests = 0
    successful = 0
    failed = 0
    timeout_count = 0
    all_response_times = []
    all_emails = []
    status_codes = {}

    for r in results:
        total_requests += r.get("total_requests", 0)
        successful += r.get("successful_requests", 0)
        failed += r.get("failed_requests", 0)
        timeout_count += r.get("timeout_count", 0)
        all_response_times.extend(r.get("response_times", []))
        all_emails.extend(r.get("registered_emails", []))
        for code, count in r.get("status_codes", {}).items():
            status_codes[code] = status_codes.get(code, 0) + count

    times = sorted(all_response_times)
    avg = statistics.mean(times) if times else 0

    def percentile(data, p):
        if not data:
            return 0
        index = int(len(data) * p / 100)
        return data[min(index, len(data) - 1)]

    return {
        "total_requests": total_requests,
        "successful_requests": successful,
        "failed_requests": failed,
        "timeout_count": timeout_count,
        "error_rate": round((failed / total_requests * 100), 2) if total_requests else 0,
        "avg_response_time": round(avg, 2),
        "min_response_time": round(min(times), 2) if times else 0,
        "max_response_time": round(max(times), 2) if times else 0,
        "p50": round(percentile(times, 50), 2),
        "p90": round(percentile(times, 90), 2),
        "p95": round(percentile(times, 95), 2),
        "p99": round(percentile(times, 99), 2),
        "throughput": round(total_requests / duration_seconds, 2) if duration_seconds else 0,
        "status_codes": status_codes,
        "registered_emails": all_emails,
    }