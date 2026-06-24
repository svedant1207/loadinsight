import asyncio
from app.worker.celery_app import celery_app
from app.engine.scenario_runner import run_auth_scenario


@celery_app.task(bind=True, name="run_auth_scenario_task")
def run_auth_scenario_task(
    self,
    base_url: str,
    virtual_users: int,
    duration_seconds: int,
    ramp_up_seconds: int,
    max_concurrent: int,
):
    """
    Celery task that runs a slice of virtual users.
    Each worker runs this independently.
    """
    self.update_state(state="STARTED", meta={"status": "running"})

    # run the async scenario in a sync celery task
    result = asyncio.run(
        run_auth_scenario(
            base_url=base_url,
            virtual_users=virtual_users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=ramp_up_seconds,
            max_concurrent=max_concurrent,
        )
    )

    return result