import asyncio
import time
import statistics
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import httpx

@dataclass
class RequestResult:
    success: bool
    response_time: float
    status_code: int | None = None
    error: str | None = None
    timed_out: bool = False

@dataclass
class TestResult:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_count: int = 0
    response_times: List[float] = field(default_factory=list)
    status_codes: dict = field(default_factory=dict)

    def calculate_metrics(self, duration_seconds: int) -> dict:
        total = self.total_requests
        success = self.successful_requests
        failed = self.failed_requests
        times = sorted(self.response_times)

        avg = statistics.mean(times) if times else 0
        min_rt = min(times) if times else 0
        max_rt = max(times) if times else 0

        def percentile(data, p):
            if not data:
                return 0
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]

        return {
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": failed,
            "timeout_count": self.timeout_count,
            "error_rate": round((failed / total * 100), 2) if total else 0,
            "avg_response_time": round(avg, 2),
            "min_response_time": round(min_rt, 2),
            "max_response_time": round(max_rt, 2),
            "p50": round(percentile(times, 50), 2),
            "p90": round(percentile(times, 90), 2),
            "p95": round(percentile(times, 95), 2),
            "p99": round(percentile(times, 99), 2),
            "throughput": round(total / duration_seconds, 2) if duration_seconds else 0,
            "status_codes": self.status_codes,
        }


async def make_request(
    client: httpx.AsyncClient,
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> RequestResult:
    start = time.monotonic()
    try:
        response = await client.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            json=body if body else None,
            timeout=10,
        )
        elapsed = (time.monotonic() - start) * 1000
        return RequestResult(
            success=response.status_code < 400,
            response_time=elapsed,
            status_code=response.status_code,
        )
    except httpx.TimeoutException:
        elapsed = (time.monotonic() - start) * 1000
        return RequestResult(success=False, response_time=elapsed, timed_out=True)
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return RequestResult(success=False, response_time=elapsed, error=str(e))


async def virtual_user(
    url: str,
    duration_seconds: int,
    result: TestResult,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
):
    end_time = time.monotonic() + duration_seconds
    async with httpx.AsyncClient() as client:
        while time.monotonic() < end_time:
            req_result = await make_request(client, url, method, headers, body)
            result.total_requests += 1
            result.response_times.append(req_result.response_time)

            if req_result.success:
                result.successful_requests += 1
            else:
                result.failed_requests += 1

            if req_result.timed_out:
                result.timeout_count += 1

            if req_result.status_code:
                code = str(req_result.status_code)
                result.status_codes[code] = result.status_codes.get(code, 0) + 1


async def run_load_test(
    url: str,
    virtual_users: int,
    duration_seconds: int,
    ramp_up_seconds: int = 0,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> dict:
    result = TestResult()

    if ramp_up_seconds > 0:
        delay = ramp_up_seconds / virtual_users
        tasks = []
        for i in range(virtual_users):
            await asyncio.sleep(delay)
            task = asyncio.create_task(
                virtual_user(url, duration_seconds, result, method, headers, body)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)
    else:
        tasks = [
            asyncio.create_task(
                virtual_user(url, duration_seconds, result, method, headers, body)
            )
            for _ in range(virtual_users)
        ]
        await asyncio.gather(*tasks)

    return result.calculate_metrics(duration_seconds)