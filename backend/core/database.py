"""
数据库配置
"""
import os
from sqlalchemy import create_engine
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
    """初始化数据库（创建表）"""
    Base.metadata.create_all(bind=engine)
