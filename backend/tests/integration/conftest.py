"""
集成测试配置
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


# 集成测试数据库配置
INTEGRATION_DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def integration_engine():
    """创建集成测试数据库引擎"""
    engine = create_async_engine(
        INTEGRATION_DATABASE_URL,
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
async def integration_db_session(integration_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建集成测试数据库会话"""
    async_session = sessionmaker(
        integration_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        # 不回滚，保持数据用于集成测试
        await session.commit()


@pytest.fixture
def override_integration_db(integration_db_session):
    """覆盖数据库依赖用于集成测试"""
    async def _override_get_db():
        yield integration_db_session
    
    return _override_get_db


@pytest.fixture
def integration_client(override_integration_db) -> Generator[TestClient, None, None]:
    """创建集成测试客户端"""
    app.dependency_overrides[get_db] = override_integration_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def integration_async_client(override_integration_db) -> AsyncGenerator[AsyncClient, None]:
    """创建异步集成测试客户端"""
    app.dependency_overrides[get_db] = override_integration_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def integration_user(integration_db_session: AsyncSession) -> User:
    """创建集成测试用户"""
    user_data = {
        "username": "integration_user",
        "email": "integration@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "is_active": True,
        "is_verified": True
    }
    
    user = User(**user_data)
    integration_db_session.add(user)
    await integration_db_session.commit()
    await integration_db_session.refresh(user)
    
    return user


@pytest.fixture
async def integration_admin_user(integration_db_session: AsyncSession) -> User:
    """创建集成测试管理员用户"""
    user_data = {
        "username": "integration_admin",
        "email": "admin@integration.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "is_active": True,
        "is_verified": True,
        "is_superuser": True
    }
    
    user = User(**user_data)
    integration_db_session.add(user)
    await integration_db_session.commit()
    await integration_db_session.refresh(user)
    
    return user


@pytest.fixture
def integration_auth_headers(integration_client: TestClient, integration_user: User) -> dict:
    """创建集成测试认证头"""
    # 通过API登录获取真实token
    login_data = {
        "username": integration_user.username,
        "password": "secret"
    }
    
    response = integration_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def integration_admin_auth_headers(integration_client: TestClient, integration_admin_user: User) -> dict:
    """创建集成测试管理员认证头"""
    login_data = {
        "username": integration_admin_user.username,
        "password": "secret"
    }
    
    response = integration_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def integration_prompt(integration_db_session: AsyncSession, integration_user: User) -> Prompt:
    """创建集成测试提示词"""
    prompt_data = {
        "title": "集成测试提示词",
        "content": "这是一个用于集成测试的提示词内容，包含足够的文本用于分析。",
        "description": "集成测试描述",
        "category": "集成测试分类",
        "tags": ["集成测试", "API测试"],
        "user_id": integration_user.id,
        "is_public": True
    }
    
    prompt = Prompt(**prompt_data)
    integration_db_session.add(prompt)
    await integration_db_session.commit()
    await integration_db_session.refresh(prompt)
    
    return prompt


@pytest.fixture
async def integration_template(integration_db_session: AsyncSession, integration_user: User) -> Template:
    """创建集成测试模板"""
    template_data = {
        "name": "集成测试模板",
        "content": "这是一个集成测试模板：{variable1}，{variable2}",
        "description": "集成测试模板描述",
        "category": "集成测试分类",
        "tags": ["集成测试", "模板测试"],
        "variables": ["variable1", "variable2"],
        "user_id": integration_user.id,
        "is_public": True,
        "is_featured": False
    }
    
    template = Template(**template_data)
    integration_db_session.add(template)
    await integration_db_session.commit()
    await integration_db_session.refresh(template)
    
    return template


@pytest.fixture
def mock_openai_integration():
    """模拟OpenAI客户端用于集成测试"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='''
        {
            "overall_score": 88.5,
            "semantic_clarity": 92.0,
            "structural_integrity": 87.0,
            "logical_coherence": 85.0,
            "specificity_score": 90.0,
            "instruction_clarity": 89.0,
            "context_completeness": 86.0,
            "suggestions": [
                "建议增加更多具体的示例来提高清晰度",
                "可以进一步明确期望的输出格式",
                "考虑添加约束条件以提高准确性"
            ]
        }
        '''))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_email_service():
    """模拟邮件服务"""
    mock_service = AsyncMock()
    mock_service.send_email.return_value = True
    mock_service.send_verification_email.return_value = True
    mock_service.send_password_reset_email.return_value = True
    return mock_service


@pytest.fixture
def mock_file_storage():
    """模拟文件存储服务"""
    mock_storage = MagicMock()
    mock_storage.upload_file.return_value = "https://example.com/uploaded-file.txt"
    mock_storage.delete_file.return_value = True
    mock_storage.get_file_url.return_value = "https://example.com/file.txt"
    return mock_storage


# 集成测试数据工厂
class IntegrationTestDataFactory:
    """集成测试数据工厂"""
    
    @staticmethod
    def create_user_registration_data(**kwargs):
        """创建用户注册数据"""
        default_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_prompt_creation_data(**kwargs):
        """创建提示词创建数据"""
        default_data = {
            "title": "新提示词",
            "content": "这是一个新的提示词内容，用于测试创建功能。",
            "description": "新提示词描述",
            "category": "测试分类",
            "tags": ["新建", "测试"]
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_template_creation_data(**kwargs):
        """创建模板创建数据"""
        default_data = {
            "name": "新模板",
            "content": "新模板内容：{param1}，{param2}",
            "description": "新模板描述",
            "category": "测试分类",
            "tags": ["新建", "模板"],
            "variables": ["param1", "param2"]
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_analysis_request_data(**kwargs):
        """创建分析请求数据"""
        default_data = {
            "content": "请分析这个提示词的质量和效果，提供详细的评分和改进建议。"
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def integration_data_factory():
    """集成测试数据工厂fixture"""
    return IntegrationTestDataFactory
