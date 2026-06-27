from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.worker.tasks import run_auth_scenario_task, merge_scenario_results
from celery import chord

router = APIRouter()


class ScenarioRequest(BaseModel):
    virtual_users: int
    duration_seconds: int
    ramp_up_seconds: int = 0
    base_url: str = "http://localhost:8000"
    cleanup: bool = True
    max_concurrent: int = 50
    workers: int = 4


@router.post("/auth")
async def run_auth_load_scenario(
        data: ScenarioRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Trigger distributed auth load test. Returns task_id immediately.
    """
    users_per_worker = data.virtual_users // data.workers
    remaining = data.virtual_users % data.workers

    # Create tasks for each worker
    callback_tasks = []
    for i in range(data.workers):
        users = users_per_worker + (remaining if i == data.workers - 1 else 0)
        callback_tasks.append(
            run_auth_scenario_task.s(
                base_url=data.base_url,
                virtual_users=users,
                duration_seconds=data.duration_seconds,
                ramp_up_seconds=data.ramp_up_seconds,
                max_concurrent=data.max_concurrent // data.workers,
            )
        )

    # Use chord to merge results
    workflow = chord(callback_tasks)(merge_scenario_results.s(data.duration_seconds))

    return {
        "task_id": workflow.id,
        "status": "queued",
        "message": f"Load test queued with {data.workers} workers. Poll /scenarios/status/{workflow.id} for updates."
    }


@router.get("/status/{task_id}")
async def check_task_status(
        task_id: str,
        current_user: User = Depends(get_current_user)
):
    """Check status of running load test."""
    from app.worker.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "progress": result.info if isinstance(result.info, (int, float)) else None,
    }


@router.get("/result/{task_id}")
async def get_task_result(
        task_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    """Get final results when test completes."""
    from app.worker.celery_app import celery_app
    from app.models.user import User as UserModel

    result = celery_app.AsyncResult(task_id)

    if result.status == "PENDING":
        raise HTTPException(status_code=404, detail="Task not found")

    if result.status == "FAILED":
        raise HTTPException(status_code=400, detail=f"Task failed: {result.info}")

    if result.status != "SUCCESS":
        raise HTTPException(status_code=202, detail=f"Still running. Status: {result.status}")

    # Get merged results
    metrics = result.result

    # Cleanup fake users
    if metrics.get("registered_emails"):
        stmt = delete(UserModel).where(
            UserModel.email.in_(metrics["registered_emails"])
        )
        res = await db.execute(stmt)
        await db.commit()
        cleaned_up = res.rowcount
    else:
        cleaned_up = 0

    return {
        "task_id": task_id,
        "status": "completed",
        "metrics": metrics,
        "cleanup": {
            "fake_users_created": len(metrics.get("registered_emails", [])),
            "fake_users_deleted": cleaned_up,
        }
    }