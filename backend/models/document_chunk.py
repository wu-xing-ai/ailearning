"""Document chunk model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func

from core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(LONGTEXT, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    meta = Column(LONGTEXT, nullable=True)
    embedding_id = Column(String(100), nullable=True)
    embedding_status = Column(String(20), default="pending")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "meta": self.meta,
            "embedding_id": self.embedding_id,
            "embedding_status": self.embedding_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
