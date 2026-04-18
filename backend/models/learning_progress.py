"""Learning progress model - tracks per-user per-document progress."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from core.database import Base


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    progress_percent = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    last_chunk_index = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="not_started")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
