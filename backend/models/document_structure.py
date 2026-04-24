"""Document structure model.

Stores outline tree + knowledge points as JSON strings (rule-based v1).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func

from core.database import Base


class DocumentStructure(Base):
    __tablename__ = "document_structures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True, index=True)

    version = Column(String(50), nullable=False)
    outline_json = Column(LONGTEXT, nullable=False)
    knowledge_points_json = Column(LONGTEXT, nullable=False)

    source = Column(String(20), default="rule")
    ai_model = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version": self.version,
            "outline_json": self.outline_json,
            "knowledge_points_json": self.knowledge_points_json,
            "source": self.source,
            "ai_model": self.ai_model,
            "prompt_version": self.prompt_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
