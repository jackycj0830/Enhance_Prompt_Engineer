"""
数据库配置和连接管理
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres123@localhost:5432/enhance_prompt_engineer"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# SQLAlchemy 配置
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 数据库元数据
metadata = MetaData()

# 声明式基类
Base = declarative_base(metadata=metadata)

# Redis 连接
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_db() -> Generator:
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """
    获取Redis客户端
    """
    return redis_client

def init_db():
    """
    初始化数据库
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

def check_db_connection() -> bool:
    """
    检查数据库连接
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def check_redis_connection() -> bool:
    """
    检查Redis连接
    """
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return False
