import asyncio
import time
import statistics
import httpx
from dataclasses import dataclass, field
from typing import List
from app.engine.data_generator import generate_user_data


@dataclass
class ScenarioResult:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: dict = field(default_factory=dict)
    registered_emails: List[str] = field(default_factory=list)

    def calculate_metrics(self, duration_seconds: int) -> dict:
        times = sorted(self.response_times)
        avg = statistics.mean(times) if times else 0

        def percentile(data, p):
            if not data:
                return 0
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "error_rate": round((self.failed_requests / self.total_requests * 100), 2) if self.total_requests else 0,
            "avg_response_time": round(avg, 2),
            "min_response_time": round(min(times), 2) if times else 0,
            "max_response_time": round(max(times), 2) if times else 0,
            "p50": round(percentile(times, 50), 2),
            "p90": round(percentile(times, 90), 2),
            "p95": round(percentile(times, 95), 2),
            "p99": round(percentile(times, 99), 2),
            "throughput": round(self.total_requests / duration_seconds, 2) if duration_seconds else 0,
            "status_codes": self.status_codes,
            "registered_emails": self.registered_emails,
        }


async def record(result: ScenarioResult, response: httpx.Response, elapsed: float):
    result.total_requests += 1
    result.response_times.append(elapsed)
    code = str(response.status_code)
    result.status_codes[code] = result.status_codes.get(code, 0) + 1
    if response.status_code < 400:
        result.successful_requests += 1
    else:
        result.failed_requests += 1


async def record_failed(result: ScenarioResult, elapsed: float):
    result.total_requests += 1
    result.response_times.append(elapsed)
    result.failed_requests += 1


async def auth_scenario(base_url: str, result: ScenarioResult):
    """
    One full auth scenario per virtual user:
    1. Generate fake user data
    2. Register
    3. Login → get token
    4. Hit /me with token
    """
    user_data = generate_user_data()
    token = None

    async with httpx.AsyncClient() as client:

        # ── Step 1: Register ───────────────────────────────────────
        start = time.monotonic()
        try:
            response = await client.post(
                f"{base_url}/api/v1/auth/register",
                json={
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "password": user_data["password"],
                },
                timeout=10,
            )
            elapsed = (time.monotonic() - start) * 1000
            await record(result, response, elapsed)
            if response.status_code == 200:
                result.registered_emails.append(user_data["email"])
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            await record_failed(result, elapsed)
            return  # stop this user's scenario if register fails

        # ── Step 2: Login ──────────────────────────────────────────
        start = time.monotonic()
        try:
            response = await client.post(
                f"{base_url}/api/v1/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
                timeout=10,
            )
            elapsed = (time.monotonic() - start) * 1000
            await record(result, response, elapsed)
            if response.status_code == 200:
                token = response.json().get("access_token")
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            await record_failed(result, elapsed)
            return  # stop if login fails

        # ── Step 3: Hit protected route ────────────────────────────
        if token:
            start = time.monotonic()
            try:
                response = await client.get(
                    f"{base_url}/api/v1/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                elapsed = (time.monotonic() - start) * 1000
                await record(result, response, elapsed)
            except Exception:
                elapsed = (time.monotonic() - start) * 1000
                await record_failed(result, elapsed)


async def run_auth_scenario(
    base_url: str,
    virtual_users: int,
    duration_seconds: int,
    ramp_up_seconds: int = 0,
    max_concurrent: int = 50,
) -> dict:
    """
    Spawn virtual users each running the full auth scenario.
    Each user runs the scenario repeatedly until time runs out.
    """
    result = ScenarioResult()
    end_time = time.monotonic() + duration_seconds

    async def user_loop():
        while time.monotonic() < end_time:
            await auth_scenario(base_url, result)

    if ramp_up_seconds > 0:
        delay = ramp_up_seconds / virtual_users
        tasks = []
        for _ in range(virtual_users):
            await asyncio.sleep(delay)
            tasks.append(asyncio.create_task(user_loop()))
        await asyncio.gather(*tasks)
    else:
        tasks = [
            asyncio.create_task(user_loop())
            for _ in range(virtual_users)
        ]
        await asyncio.gather(*tasks)

    return result.calculate_metrics(duration_seconds)