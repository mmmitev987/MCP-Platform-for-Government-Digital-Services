from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from backend.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service = Column(String, nullable=False)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)     # "completed" | "pending" | "failed"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Covers: filter by user → order by date (most common query)
        Index("ix_activity_user_created", "user_id", "created_at"),
        # Covers: filter by user + status → order by date (filtered tab queries)
        Index("ix_activity_user_status_created", "user_id", "status", "created_at"),
    )
