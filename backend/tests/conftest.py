"""
测试配置和共享fixtures
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.prompt import Prompt
from app.models.template import Template
from app.models.analysis import Analysis
from app.services.auth_service import AuthService


# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db(db_session):
    """覆盖数据库依赖"""
    async def _override_get_db():
        yield db_session
    
    return _override_get_db


@pytest.fixture
def test_client(override_get_db) -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """创建异步测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "is_active": True,
        "is_verified": True
    }
    
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    user_data = {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "is_active": True,
        "is_verified": True,
        "is_superuser": True
    }
    
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """创建认证头"""
    auth_service = AuthService()
    token = auth_service.create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: User) -> dict:
    """创建管理员认证头"""
    auth_service = AuthService()
    token = auth_service.create_access_token(data={"sub": test_admin_user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_prompt(db_session: AsyncSession, test_user: User) -> Prompt:
    """创建测试提示词"""
    prompt_data = {
        "title": "测试提示词",
        "content": "这是一个用于测试的提示词内容",
        "description": "测试描述",
        "category": "测试分类",
        "tags": ["测试", "单元测试"],
        "user_id": test_user.id,
        "is_public": True
    }
    
    prompt = Prompt(**prompt_data)
    db_session.add(prompt)
    await db_session.commit()
    await db_session.refresh(prompt)
    
    return prompt


@pytest.fixture
async def test_template(db_session: AsyncSession, test_user: User) -> Template:
    """创建测试模板"""
    template_data = {
        "name": "测试模板",
        "content": "这是一个测试模板：{variable}",
        "description": "测试模板描述",
        "category": "测试分类",
        "tags": ["测试", "模板"],
        "variables": ["variable"],
        "user_id": test_user.id,
        "is_public": True,
        "is_featured": False
    }
    
    template = Template(**template_data)
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    
    return template


@pytest.fixture
async def test_analysis(db_session: AsyncSession, test_user: User, test_prompt: Prompt) -> Analysis:
    """创建测试分析结果"""
    analysis_data = {
        "prompt_id": test_prompt.id,
        "user_id": test_user.id,
        "overall_score": 85.5,
        "semantic_clarity": 90.0,
        "structural_integrity": 85.0,
        "logical_coherence": 80.0,
        "specificity_score": 88.0,
        "instruction_clarity": 92.0,
        "context_completeness": 85.0,
        "analysis_details": {
            "word_count": 50,
            "sentence_count": 3,
            "avg_sentence_length": 16.7,
            "complexity_score": 0.6,
            "readability_score": 0.8
        },
        "suggestions": [
            "建议增加更多具体的示例",
            "可以进一步明确输出格式要求"
        ],
        "ai_model_used": "gpt-3.5-turbo",
        "processing_time_ms": 1500
    }
    
    analysis = Analysis(**analysis_data)
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    
    return analysis


@pytest.fixture
def mock_openai_client():
    """模拟OpenAI客户端"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"overall_score": 85.5, "semantic_clarity": 90.0}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False
    return mock_client


@pytest.fixture
def temp_file():
    """创建临时文件"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


# 测试数据工厂
class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_user_data(**kwargs):
        """创建用户数据"""
        default_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_prompt_data(**kwargs):
        """创建提示词数据"""
        default_data = {
            "title": "测试提示词",
            "content": "这是一个测试提示词",
            "description": "测试描述",
            "category": "测试",
            "tags": ["测试"]
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_template_data(**kwargs):
        """创建模板数据"""
        default_data = {
            "name": "测试模板",
            "content": "测试模板内容：{variable}",
            "description": "测试模板描述",
            "category": "测试",
            "tags": ["测试"],
            "variables": ["variable"]
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def test_data_factory():
    """测试数据工厂fixture"""
    return TestDataFactory
