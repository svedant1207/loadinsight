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
    """
    self.update_state(state="STARTED", meta={"status": "running"})

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


@celery_app.task(bind=True, name="merge_scenario_results")
def merge_scenario_results(self, results, duration_seconds):
    """Merge results from all worker tasks into one."""
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