import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class DomainVerification(Base):
    __tablename__ = "domain_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_verified: Mapped[bool] = mapped_column(String(10), default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)