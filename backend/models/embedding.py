"""嵌入向量数据库模型"""
from sqlalchemy import Column, String, Integer, Text
from core.database import Base


class EmbeddingVector(Base):
    """嵌入向量表 - 替代 ChromaDB"""
    __tablename__ = "embedding_vectors"

    id = Column(String(200), primary_key=True)
    doc_id = Column(String(100), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    embedding = Column(Text, nullable=False)  # JSON 存储向量
