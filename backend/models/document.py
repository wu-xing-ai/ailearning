"""
数据库模型
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.sql import func
from core.database import Base


class Document(Base):
    """文档表"""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    content = Column(Text(4294967295), nullable=True)  # LONGTEXT - 支持大文件内容
    file_path = Column(String(500), nullable=True)  # 原始文件存储路径
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self, include_content=False):
        """转换为字典"""
        result = {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_path": self.file_path,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_content:
            content = self.content or ""
            content_error = None
            if content.strip().startswith("[处理失败"):
                content_error = "文档内容异常（上次上传时解析失败），请删除后重新上传"
            result["content"] = content
            result["content_error"] = content_error
        else:
            content = self.content or ""
            if content.strip().startswith("[处理失败"):
                result["content_error"] = "文档内容异常（上次上传时解析失败），请删除后重新上传"
            else:
                result["content_error"] = None
        return result