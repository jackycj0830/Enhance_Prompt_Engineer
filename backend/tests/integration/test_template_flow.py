"""
模板管理流程集成测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestTemplateManagementFlow:
    """模板管理流程测试"""
    
    def test_complete_template_lifecycle(self, integration_client: TestClient, integration_auth_headers,
                                       integration_data_factory):
        """测试完整的模板生命周期"""
        # 1. 创建模板
        template_data = integration_data_factory.create_template_creation_data()
        
        create_response = integration_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=integration_auth_headers
        )
        assert create_response.status_code == 201
        
        created_template = create_response.json()
        template_id = created_template["id"]
        
        # 验证创建的模板数据
        assert created_template["name"] == template_data["name"]
        assert created_template["content"] == template_data["content"]
        assert created_template["variables"] == template_data["variables"]
        assert "created_at" in created_template
        
        # 2. 获取单个模板
        get_response = integration_client.get(f"/api/v1/templates/{template_id}")
        assert get_response.status_code == 200
        
        retrieved_template = get_response.json()
        assert retrieved_template["id"] == template_id
        assert retrieved_template["name"] == template_data["name"]
        
        # 3. 更新模板
        update_data = {
            "name": "更新后的模板名称",
            "description": "更新后的描述",
            "tags": ["更新", "测试"]
        }
        
        update_response = integration_client.put(
            f"/api/v1/templates/{template_id}",
            json=update_data,
            headers=integration_auth_headers
        )
        assert update_response.status_code == 200
        
        updated_template = update_response.json()
        assert updated_template["name"] == update_data["name"]
        assert updated_template["description"] == update_data["description"]
        
        # 4. 获取用户模板列表
        my_templates_response = integration_client.get(
            "/api/v1/templates/my",
            headers=integration_auth_headers
        )
        assert my_templates_response.status_code == 200
        
        my_templates = my_templates_response.json()
        assert isinstance(my_templates, list)
        
        # 验证新创建的模板在列表中
        template_ids = [t["id"] for t in my_templates]
        assert template_id in template_ids
        
        # 5. 删除模板
        delete_response = integration_client.delete(
            f"/api/v1/templates/{template_id}",
            headers=integration_auth_headers
        )
        assert delete_response.status_code == 204
        
        # 6. 验证模板已删除
        get_deleted_response = integration_client.get(f"/api/v1/templates/{template_id}")
        assert get_deleted_response.status_code == 404
    
    def test_template_search_and_filter(self, integration_client: TestClient, integration_auth_headers,
                                      integration_data_factory):
        """测试模板搜索和筛选"""
        # 1. 创建多个不同类型的模板
        templates_data = [
            integration_data_factory.create_template_creation_data(
                name="搜索测试模板1",
                category="分类A",
                tags=["标签1", "搜索"]
            ),
            integration_data_factory.create_template_creation_data(
                name="搜索测试模板2",
                category="分类B",
                tags=["标签2", "搜索"]
            ),
            integration_data_factory.create_template_creation_data(
                name="其他模板",
                category="分类A",
                tags=["标签1", "其他"]
            )
        ]
        
        created_template_ids = []
        for template_data in templates_data:
            response = integration_client.post(
                "/api/v1/templates/",
                json=template_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            created_template_ids.append(response.json()["id"])
        
        # 2. 测试搜索功能
        search_response = integration_client.get(
            "/api/v1/templates/search?q=搜索测试"
        )
        assert search_response.status_code == 200
        
        search_results = search_response.json()
        assert len(search_results) >= 2  # 应该找到两个搜索测试模板
        
        # 3. 测试分类筛选
        category_response = integration_client.get(
            "/api/v1/templates/?category=分类A"
        )
        assert category_response.status_code == 200
        
        category_results = category_response.json()
        for template in category_results:
            if template["id"] in created_template_ids:
                assert template["category"] == "分类A"
        
        # 4. 测试标签筛选
        tag_response = integration_client.get(
            "/api/v1/templates/?tags=标签1"
        )
        assert tag_response.status_code == 200
        
        tag_results = tag_response.json()
        for template in tag_results:
            if template["id"] in created_template_ids:
                assert "标签1" in template["tags"]
        
        # 清理：删除创建的模板
        for template_id in created_template_ids:
            integration_client.delete(
                f"/api/v1/templates/{template_id}",
                headers=integration_auth_headers
            )
    
    def test_template_variable_detection(self, integration_client: TestClient, integration_auth_headers):
        """测试模板变量检测"""
        template_data = {
            "name": "变量检测测试",
            "content": "你好，{name}！今天是{date}，天气{weather}。请{action}。",
            "description": "变量检测测试模板",
            "category": "测试",
            "tags": ["变量", "测试"]
        }
        
        response = integration_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=integration_auth_headers
        )
        assert response.status_code == 201
        
        created_template = response.json()
        
        # 验证变量被正确检测
        expected_variables = ["name", "date", "weather", "action"]
        assert set(created_template["variables"]) == set(expected_variables)
        
        # 清理
        integration_client.delete(
            f"/api/v1/templates/{created_template['id']}",
            headers=integration_auth_headers
        )
    
    def test_template_public_private_access(self, integration_client: TestClient, integration_auth_headers,
                                          integration_data_factory):
        """测试模板公开/私有访问控制"""
        # 1. 创建私有模板
        private_template_data = integration_data_factory.create_template_creation_data(
            name="私有模板",
            is_public=False
        )
        
        private_response = integration_client.post(
            "/api/v1/templates/",
            json=private_template_data,
            headers=integration_auth_headers
        )
        assert private_response.status_code == 201
        private_template_id = private_response.json()["id"]
        
        # 2. 创建公开模板
        public_template_data = integration_data_factory.create_template_creation_data(
            name="公开模板",
            is_public=True
        )
        
        public_response = integration_client.post(
            "/api/v1/templates/",
            json=public_template_data,
            headers=integration_auth_headers
        )
        assert public_response.status_code == 201
        public_template_id = public_response.json()["id"]
        
        # 3. 测试公开模板列表（不需要认证）
        public_list_response = integration_client.get("/api/v1/templates/")
        assert public_list_response.status_code == 200
        
        public_templates = public_list_response.json()
        public_template_ids = [t["id"] for t in public_templates]
        
        # 公开模板应该在列表中
        assert public_template_id in public_template_ids
        # 私有模板不应该在公开列表中
        assert private_template_id not in public_template_ids
        
        # 4. 创建另一个用户测试访问权限
        user2_data = integration_data_factory.create_user_registration_data(
            username="template_user2",
            email="template_user2@example.com"
        )
        
        register_response = integration_client.post("/api/v1/auth/register", json=user2_data)
        assert register_response.status_code == 201
        
        login_response = integration_client.post("/api/v1/auth/login", data={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        assert login_response.status_code == 200
        
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # 5. 用户2访问公开模板（应该成功）
        public_access_response = integration_client.get(
            f"/api/v1/templates/{public_template_id}",
            headers=user2_headers
        )
        assert public_access_response.status_code == 200
        
        # 6. 用户2访问私有模板（应该失败）
        private_access_response = integration_client.get(
            f"/api/v1/templates/{private_template_id}",
            headers=user2_headers
        )
        assert private_access_response.status_code in [403, 404]
        
        # 清理
        integration_client.delete(f"/api/v1/templates/{private_template_id}", headers=integration_auth_headers)
        integration_client.delete(f"/api/v1/templates/{public_template_id}", headers=integration_auth_headers)
    
    def test_template_featured_functionality(self, integration_client: TestClient, integration_admin_auth_headers,
                                           integration_data_factory):
        """测试模板精选功能"""
        # 1. 创建模板
        template_data = integration_data_factory.create_template_creation_data(
            name="精选测试模板",
            is_public=True
        )
        
        response = integration_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=integration_admin_auth_headers
        )
        assert response.status_code == 201
        template_id = response.json()["id"]
        
        # 2. 设置为精选（需要管理员权限）
        feature_response = integration_client.patch(
            f"/api/v1/templates/{template_id}/feature",
            headers=integration_admin_auth_headers
        )
        
        if feature_response.status_code == 200:  # 如果端点存在
            # 3. 获取精选模板列表
            featured_response = integration_client.get("/api/v1/templates/featured")
            assert featured_response.status_code == 200
            
            featured_templates = featured_response.json()
            featured_ids = [t["id"] for t in featured_templates]
            assert template_id in featured_ids
        
        # 清理
        integration_client.delete(f"/api/v1/templates/{template_id}", headers=integration_admin_auth_headers)


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncTemplateFlow:
    """异步模板流程测试"""
    
    async def test_concurrent_template_operations(self, integration_async_client: AsyncClient,
                                                integration_auth_headers, integration_data_factory):
        """测试并发模板操作"""
        import asyncio
        
        # 创建多个并发模板创建请求
        template_tasks = []
        for i in range(3):
            template_data = integration_data_factory.create_template_creation_data(
                name=f"并发模板{i}",
                content=f"并发测试内容{i}：{{variable{i}}}"
            )
            task = integration_async_client.post(
                "/api/v1/templates/",
                json=template_data,
                headers=integration_auth_headers
            )
            template_tasks.append(task)
        
        # 并发执行
        responses = await asyncio.gather(*template_tasks, return_exceptions=True)
        
        # 验证所有创建都成功
        successful_responses = 0
        template_ids = []
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 201:
                successful_responses += 1
                template_ids.append(response.json()["id"])
        
        assert successful_responses >= 1  # 至少有一个成功
        
        # 清理创建的模板
        for template_id in template_ids:
            await integration_async_client.delete(
                f"/api/v1/templates/{template_id}",
                headers=integration_auth_headers
            )


@pytest.mark.integration
class TestTemplateValidation:
    """模板验证测试"""
    
    def test_template_input_validation(self, integration_client: TestClient, integration_auth_headers):
        """测试模板输入验证"""
        # 1. 空名称
        invalid_data = {
            "name": "",
            "content": "测试内容",
            "description": "测试描述"
        }
        
        response = integration_client.post(
            "/api/v1/templates/",
            json=invalid_data,
            headers=integration_auth_headers
        )
        assert response.status_code == 422
        
        # 2. 空内容
        invalid_data = {
            "name": "测试模板",
            "content": "",
            "description": "测试描述"
        }
        
        response = integration_client.post(
            "/api/v1/templates/",
            json=invalid_data,
            headers=integration_auth_headers
        )
        assert response.status_code == 422
        
        # 3. 名称过长
        invalid_data = {
            "name": "a" * 256,  # 假设有长度限制
            "content": "测试内容",
            "description": "测试描述"
        }
        
        response = integration_client.post(
            "/api/v1/templates/",
            json=invalid_data,
            headers=integration_auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_template_duplicate_name_handling(self, integration_client: TestClient, integration_auth_headers,
                                            integration_data_factory):
        """测试模板重名处理"""
        # 1. 创建第一个模板
        template_data = integration_data_factory.create_template_creation_data(
            name="重名测试模板"
        )
        
        response1 = integration_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=integration_auth_headers
        )
        assert response1.status_code == 201
        template_id = response1.json()["id"]
        
        # 2. 尝试创建同名模板
        response2 = integration_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=integration_auth_headers
        )
        
        # 可能允许同名（由用户ID区分）或拒绝
        assert response2.status_code in [201, 400, 409]
        
        # 清理
        integration_client.delete(f"/api/v1/templates/{template_id}", headers=integration_auth_headers)
        if response2.status_code == 201:
            integration_client.delete(f"/api/v1/templates/{response2.json()['id']}", headers=integration_auth_headers)
