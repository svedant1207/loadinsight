from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class PipelineStepCreate(BaseModel):
    name: str
    url: str
    http_method: str = "GET"
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None
    step_order: int

class PipelineCreate(BaseModel):
    name: str
    steps: List[PipelineStepCreate]

class PipelineStepResponse(BaseModel):
    id: str
    pipeline_id: str
    step_order: int
    name: str
    url: str
    http_method: str

    model_config = {"from_attributes": True}

class PipelineResponse(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: datetime
    steps: List[PipelineStepResponse] = []

    model_config = {"from_attributes": True}