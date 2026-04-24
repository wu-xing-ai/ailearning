"""
数据库配置
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库连接配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:wjx1314520@localhost:3306/ailearning?charset=utf8mb4"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动检测连接是否有效
    pool_recycle=3600,   # 连接回收时间
    echo=False           # 不打印 SQL 语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建表 + 迁移列类型）"""
    Base.metadata.create_all(bind=engine)
    # 迁移：确保 documents.content 列为 LONGTEXT，避免大文件写入失败
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'documents' AND COLUMN_NAME = 'content'"
                )
            )
            row = result.fetchone()
            if row and row[0].lower() != 'longtext':
                conn.execute(text(
                    "ALTER TABLE documents MODIFY COLUMN content LONGTEXT NULL"
                ))
                conn.commit()
                print("[数据库迁移] documents.content 已升级为 LONGTEXT")
    except Exception as e:
        print(f"[数据库迁移] 检查/升级 content 列类型时出错（可忽略）: {e}")

    # 迁移：确保 document_structures.outline_json / knowledge_points_json 为 LONGTEXT
    try:
        with engine.connect() as conn:
            for col_name in ("outline_json", "knowledge_points_json"):
                result = conn.execute(
                    text(
                        "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'document_structures' AND COLUMN_NAME = :col"
                    ),
                    {"col": col_name}
                )
                row = result.fetchone()
                if row and row[0].lower() != 'longtext':
                    conn.execute(text(
                        f"ALTER TABLE document_structures MODIFY COLUMN {col_name} LONGTEXT NOT NULL"
                    ))
                    conn.commit()
                    print(f"[数据库迁移] document_structures.{col_name} 已升级为 LONGTEXT")
    except Exception as e:
        print(f"[数据库迁移] 检查/升级 document_structures 列类型时出错（可忽略）: {e}")

    # 迁移：确保 document_chunks.text / meta 为 LONGTEXT
    try:
        with engine.connect() as conn:
            for col_name, nullable in (("text", "NOT NULL"), ("meta", "NULL")):
                result = conn.execute(
                    text(
                        "SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'document_chunks' AND COLUMN_NAME = :col"
                    ),
                    {"col": col_name}
                )
                row = result.fetchone()
                if row and row[0].lower() != 'longtext':
                    conn.execute(text(
                        f"ALTER TABLE document_chunks MODIFY COLUMN {col_name} LONGTEXT {nullable}"
                    ))
                    conn.commit()
                    print(f"[数据库迁移] document_chunks.{col_name} 已升级为 LONGTEXT")
    except Exception as e:
        print(f"[数据库迁移] 检查/升级 document_chunks 列类型时出错（可忽略）: {e}")
