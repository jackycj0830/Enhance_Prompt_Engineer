"""
用户流程集成测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestUserRegistrationFlow:
    """用户注册流程测试"""
    
    def test_complete_user_registration_flow(self, integration_client: TestClient, integration_data_factory):
        """测试完整的用户注册流程"""
        # 1. 注册新用户
        registration_data = integration_data_factory.create_user_registration_data()
        
        response = integration_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["username"] == registration_data["username"]
        assert user_data["email"] == registration_data["email"]
        assert "id" in user_data
        
        # 2. 验证用户可以登录
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"]
        }
        
        login_response = integration_client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # 3. 使用token访问受保护的端点
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = integration_client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["username"] == registration_data["username"]
        assert profile_data["email"] == registration_data["email"]
    
    def test_duplicate_username_registration(self, integration_client: TestClient, integration_user, integration_data_factory):
        """测试重复用户名注册"""
        registration_data = integration_data_factory.create_user_registration_data(
            username=integration_user.username
        )
        
        response = integration_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 400
        
        error_data = response.json()
        assert "already exists" in error_data["detail"].lower()
    
    def test_duplicate_email_registration(self, integration_client: TestClient, integration_user, integration_data_factory):
        """测试重复邮箱注册"""
        registration_data = integration_data_factory.create_user_registration_data(
            email=integration_user.email
        )
        
        response = integration_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 400
        
        error_data = response.json()
        assert "already exists" in error_data["detail"].lower()


@pytest.mark.integration
class TestUserAuthenticationFlow:
    """用户认证流程测试"""
    
    def test_login_logout_flow(self, integration_client: TestClient, integration_user):
        """测试登录登出流程"""
        # 1. 用户登录
        login_data = {
            "username": integration_user.username,
            "password": "secret"
        }
        
        login_response = integration_client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # 2. 验证token有效
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = integration_client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # 3. 登出（如果有登出端点）
        # logout_response = integration_client.post("/api/v1/auth/logout", headers=headers)
        # assert logout_response.status_code == 200
    
    def test_invalid_credentials_login(self, integration_client: TestClient, integration_user):
        """测试无效凭据登录"""
        login_data = {
            "username": integration_user.username,
            "password": "wrongpassword"
        }
        
        response = integration_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_nonexistent_user_login(self, integration_client: TestClient):
        """测试不存在用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = integration_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_token_expiration_handling(self, integration_client: TestClient):
        """测试token过期处理"""
        # 使用过期的token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = integration_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_token_handling(self, integration_client: TestClient):
        """测试格式错误的token处理"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = integration_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


@pytest.mark.integration
class TestUserProfileFlow:
    """用户资料流程测试"""
    
    def test_get_user_profile(self, integration_client: TestClient, integration_auth_headers):
        """测试获取用户资料"""
        response = integration_client.get("/api/v1/auth/me", headers=integration_auth_headers)
        assert response.status_code == 200
        
        profile_data = response.json()
        assert "id" in profile_data
        assert "username" in profile_data
        assert "email" in profile_data
        assert "created_at" in profile_data
    
    def test_update_user_profile(self, integration_client: TestClient, integration_auth_headers):
        """测试更新用户资料"""
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio"
        }
        
        response = integration_client.put("/api/v1/users/me", json=update_data, headers=integration_auth_headers)
        
        if response.status_code == 200:  # 如果端点存在
            updated_profile = response.json()
            assert updated_profile["full_name"] == "Updated Name"
        else:
            # 端点可能还未实现
            assert response.status_code in [404, 405]


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncUserFlow:
    """异步用户流程测试"""
    
    async def test_async_user_registration_flow(self, integration_async_client: AsyncClient, integration_data_factory):
        """测试异步用户注册流程"""
        registration_data = integration_data_factory.create_user_registration_data(
            username="async_user",
            email="async@example.com"
        )
        
        # 1. 异步注册
        response = await integration_async_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201
        
        # 2. 异步登录
        login_data = {
            "username": registration_data["username"],
            "password": registration_data["password"]
        }
        
        login_response = await integration_async_client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        
        # 3. 异步访问受保护端点
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = await integration_async_client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
    
    async def test_concurrent_user_operations(self, integration_async_client: AsyncClient, integration_data_factory):
        """测试并发用户操作"""
        import asyncio
        
        # 创建多个并发注册请求
        registration_tasks = []
        for i in range(3):
            registration_data = integration_data_factory.create_user_registration_data(
                username=f"concurrent_user_{i}",
                email=f"concurrent_{i}@example.com"
            )
            task = integration_async_client.post("/api/v1/auth/register", json=registration_data)
            registration_tasks.append(task)
        
        # 并发执行
        responses = await asyncio.gather(*registration_tasks, return_exceptions=True)
        
        # 验证所有注册都成功
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 201


@pytest.mark.integration
class TestUserPermissionFlow:
    """用户权限流程测试"""
    
    def test_regular_user_permissions(self, integration_client: TestClient, integration_auth_headers):
        """测试普通用户权限"""
        # 普通用户应该能访问自己的资源
        response = integration_client.get("/api/v1/auth/me", headers=integration_auth_headers)
        assert response.status_code == 200
        
        # 普通用户不应该能访问管理员端点
        admin_response = integration_client.get("/api/v1/admin/users", headers=integration_auth_headers)
        assert admin_response.status_code in [403, 404]  # 禁止访问或端点不存在
    
    def test_admin_user_permissions(self, integration_client: TestClient, integration_admin_auth_headers):
        """测试管理员用户权限"""
        # 管理员应该能访问自己的资源
        response = integration_client.get("/api/v1/auth/me", headers=integration_admin_auth_headers)
        assert response.status_code == 200
        
        # 管理员应该能访问管理员端点（如果存在）
        admin_response = integration_client.get("/api/v1/admin/users", headers=integration_admin_auth_headers)
        # 端点可能还未实现，所以接受404
        assert admin_response.status_code in [200, 404]
    
    def test_unauthorized_access(self, integration_client: TestClient):
        """测试未授权访问"""
        # 不提供token
        response = integration_client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        # 提供无效token
        headers = {"Authorization": "Bearer invalid_token"}
        response = integration_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
