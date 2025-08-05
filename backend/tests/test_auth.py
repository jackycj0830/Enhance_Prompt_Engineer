"""
用户认证模块测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt

from app.services.auth_service import AuthService
from app.models.user import User
from app.core.config import get_settings
from app.core.security import verify_password, get_password_hash


class TestAuthService:
    """认证服务测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.auth_service = AuthService()
        self.settings = get_settings()
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "testuser"}
        token = self.auth_service.create_access_token(data)
        
        # 验证令牌格式
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT格式
        
        # 解码验证
        payload = jwt.decode(
            token, 
            self.settings.SECRET_KEY, 
            algorithms=[self.settings.ALGORITHM]
        )
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_create_access_token_with_expires_delta(self):
        """测试创建带过期时间的访问令牌"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = self.auth_service.create_access_token(data, expires_delta)
        
        payload = jwt.decode(
            token, 
            self.settings.SECRET_KEY, 
            algorithms=[self.settings.ALGORITHM]
        )
        
        # 验证过期时间
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + expires_delta
        
        # 允许1秒的误差
        assert abs((exp_datetime - expected_exp).total_seconds()) < 1
    
    def test_verify_token_valid(self):
        """测试验证有效令牌"""
        data = {"sub": "testuser"}
        token = self.auth_service.create_access_token(data)
        
        payload = self.auth_service.verify_token(token)
        assert payload["sub"] == "testuser"
    
    def test_verify_token_invalid(self):
        """测试验证无效令牌"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.verify_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    def test_verify_token_expired(self):
        """测试验证过期令牌"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=-1)  # 已过期
        token = self.auth_service.create_access_token(data, expires_delta)
        
        with pytest.raises(HTTPException) as exc_info:
            self.auth_service.verify_token(token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session, test_user):
        """测试用户认证成功"""
        # 设置正确的密码哈希
        test_user.hashed_password = get_password_hash("secret")
        await db_session.commit()
        
        authenticated_user = await self.auth_service.authenticate_user(
            db_session, "testuser", "secret"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"
        assert authenticated_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session, test_user):
        """测试用户认证密码错误"""
        authenticated_user = await self.auth_service.authenticate_user(
            db_session, "testuser", "wrongpassword"
        )
        
        assert authenticated_user is False
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session):
        """测试用户认证用户不存在"""
        authenticated_user = await self.auth_service.authenticate_user(
            db_session, "nonexistent", "password"
        )
        
        assert authenticated_user is False
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session, test_user):
        """测试获取当前用户成功"""
        data = {"sub": test_user.username}
        token = self.auth_service.create_access_token(data)
        
        current_user = await self.auth_service.get_current_user(token, db_session)
        
        assert current_user is not None
        assert current_user.username == test_user.username
        assert current_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """测试获取当前用户令牌无效"""
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.get_current_user("invalid_token", db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session):
        """测试获取当前用户用户不存在"""
        data = {"sub": "nonexistent"}
        token = self.auth_service.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.get_current_user(token, db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_success(self, db_session, test_user):
        """测试获取当前活跃用户成功"""
        data = {"sub": test_user.username}
        token = self.auth_service.create_access_token(data)
        
        current_user = await self.auth_service.get_current_active_user(token, db_session)
        
        assert current_user is not None
        assert current_user.username == test_user.username
        assert current_user.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self, db_session, test_user):
        """测试获取当前活跃用户用户未激活"""
        # 设置用户为未激活状态
        test_user.is_active = False
        await db_session.commit()
        
        data = {"sub": test_user.username}
        token = self.auth_service.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            await self.auth_service.get_current_active_user(token, db_session)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # 验证哈希格式
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt哈希长度
        
        # 验证密码验证
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_verification(self):
        """测试密码验证"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """测试不同密码产生不同哈希"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """测试相同密码产生不同哈希（盐值不同）"""
        password = "testpassword123"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # 由于盐值不同，哈希应该不同
        assert hash1 != hash2
        
        # 但都应该能验证原密码
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.asyncio
class TestAuthEndpoints:
    """认证端点测试"""
    
    async def test_login_success(self, async_client, test_user):
        """测试登录成功"""
        login_data = {
            "username": "testuser",
            "password": "secret"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    async def test_login_invalid_credentials(self, async_client, test_user):
        """测试登录凭据无效"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_login_user_not_found(self, async_client):
        """测试登录用户不存在"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = await async_client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    async def test_get_current_user_success(self, async_client, auth_headers):
        """测试获取当前用户信息成功"""
        response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "id" in data
    
    async def test_get_current_user_unauthorized(self, async_client):
        """测试获取当前用户信息未授权"""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(self, async_client):
        """测试获取当前用户信息令牌无效"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
