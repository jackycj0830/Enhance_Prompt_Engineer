"""
数据库配置和连接管理
"""

import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('.env.dev')

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./enhance_prompt_engineer.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# SQLAlchemy 配置
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL配置
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
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None

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
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def check_redis_connection() -> bool:
    """
    检查Redis连接
    """
    if redis_client is None:
        print("Redis未配置，将使用内存缓存")
        return True

    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis连接失败: {e}")
        return True  # Redis失败不影响应用启动
