import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import enum


class TestStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class LoadTest(Base):
    __tablename__ = "load_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    # config
    virtual_users: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    ramp_up_seconds: Mapped[int] = mapped_column(Integer, default=0)
    request_rate: Mapped[int] = mapped_column(Integer, nullable=True)

    # request config
    http_method: Mapped[str] = mapped_column(String(10), default="GET")
    request_headers: Mapped[str] = mapped_column(Text, nullable=True)  # stored as JSON string
    request_body: Mapped[str] = mapped_column(Text, nullable=True)  # stored as JSON string

    # status
    status: Mapped[str] = mapped_column(String(20), default=TestStatus.pending)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # results
    total_requests: Mapped[int] = mapped_column(Integer, nullable=True)
    successful_requests: Mapped[int] = mapped_column(Integer, nullable=True)
    failed_requests: Mapped[int] = mapped_column(Integer, nullable=True)
    avg_response_time: Mapped[float] = mapped_column(Float, nullable=True)
    min_response_time: Mapped[float] = mapped_column(Float, nullable=True)
    max_response_time: Mapped[float] = mapped_column(Float, nullable=True)
    p50: Mapped[float] = mapped_column(Float, nullable=True)
    p90: Mapped[float] = mapped_column(Float, nullable=True)
    p95: Mapped[float] = mapped_column(Float, nullable=True)
    p99: Mapped[float] = mapped_column(Float, nullable=True)
    throughput: Mapped[float] = mapped_column(Float, nullable=True)
    error_rate: Mapped[float] = mapped_column(Float, nullable=True)
    timeout_count: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)