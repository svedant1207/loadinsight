from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class LoadTestCreate(BaseModel):
    virtual_users: int
    duration_seconds: int
    ramp_up_seconds: int = 0
    request_rate: Optional[int] = None
    http_method: str = "GET"
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None

class LoadTestResponse(BaseModel):
    id: str
    project_id: str
    virtual_users: int
    duration_seconds: int
    ramp_up_seconds: int
    status: str
    http_method: str
    total_requests: Optional[int] = None
    successful_requests: Optional[int] = None
    failed_requests: Optional[int] = None
    avg_response_time: Optional[float] = None
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None
    p50: Optional[float] = None
    p90: Optional[float] = None
    p95: Optional[float] = None
    p99: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    timeout_count: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}