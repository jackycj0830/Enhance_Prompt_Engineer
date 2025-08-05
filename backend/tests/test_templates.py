"""
模板管理模块测试
"""

import pytest
from unittest.mock import patch
from sqlalchemy import select

from app.services.template_service import TemplateService
from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate


class TestTemplateService:
    """模板服务测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.template_service = TemplateService()
    
    @pytest.mark.asyncio
    async def test_create_template_success(self, db_session, test_user, test_data_factory):
        """测试创建模板成功"""
        template_data = TemplateCreate(**test_data_factory.create_template_data())
        
        result = await self.template_service.create_template(
            db_session, template_data, test_user.id
        )
        
        assert isinstance(result, Template)
        assert result.name == template_data.name
        assert result.content == template_data.content
        assert result.user_id == test_user.id
        assert result.is_public is False  # 默认私有
        assert result.is_featured is False  # 默认非精选
    
    @pytest.mark.asyncio
    async def test_create_template_with_variables(self, db_session, test_user):
        """测试创建带变量的模板"""
        template_data = TemplateCreate(
            name="变量模板",
            content="你好，{name}！今天是{date}。",
            description="带变量的测试模板",
            category="测试",
            tags=["变量", "测试"],
            variables=["name", "date"]
        )
        
        result = await self.template_service.create_template(
            db_session, template_data, test_user.id
        )
        
        assert result.variables == ["name", "date"]
        assert len(result.variables) == 2
    
    @pytest.mark.asyncio
    async def test_get_template_by_id_success(self, db_session, test_template):
        """测试根据ID获取模板成功"""
        result = await self.template_service.get_template_by_id(
            db_session, test_template.id
        )
        
        assert result is not None
        assert result.id == test_template.id
        assert result.name == test_template.name
    
    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, db_session):
        """测试根据ID获取模板不存在"""
        result = await self.template_service.get_template_by_id(
            db_session, 99999
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_templates_public_only(self, db_session, test_user):
        """测试获取公开模板"""
        # 创建公开和私有模板
        public_template = Template(
            name="公开模板",
            content="公开内容",
            user_id=test_user.id,
            is_public=True
        )
        private_template = Template(
            name="私有模板",
            content="私有内容",
            user_id=test_user.id,
            is_public=False
        )
        
        db_session.add(public_template)
        db_session.add(private_template)
        await db_session.commit()
        
        results = await self.template_service.get_templates(
            db_session, public_only=True, skip=0, limit=10
        )
        
        # 应该只返回公开模板
        public_results = [t for t in results if t.is_public]
        assert len(public_results) >= 1
        assert all(t.is_public for t in public_results)
    
    @pytest.mark.asyncio
    async def test_get_templates_by_category(self, db_session, test_user):
        """测试按分类获取模板"""
        # 创建不同分类的模板
        template1 = Template(
            name="分类1模板",
            content="内容1",
            category="分类1",
            user_id=test_user.id,
            is_public=True
        )
        template2 = Template(
            name="分类2模板",
            content="内容2",
            category="分类2",
            user_id=test_user.id,
            is_public=True
        )
        
        db_session.add(template1)
        db_session.add(template2)
        await db_session.commit()
        
        results = await self.template_service.get_templates(
            db_session, category="分类1", skip=0, limit=10
        )
        
        assert len(results) >= 1
        assert all(t.category == "分类1" for t in results)
    
    @pytest.mark.asyncio
    async def test_get_templates_by_tags(self, db_session, test_user):
        """测试按标签获取模板"""
        template = Template(
            name="标签模板",
            content="内容",
            tags=["标签1", "标签2"],
            user_id=test_user.id,
            is_public=True
        )
        
        db_session.add(template)
        await db_session.commit()
        
        results = await self.template_service.get_templates(
            db_session, tags=["标签1"], skip=0, limit=10
        )
        
        assert len(results) >= 1
        found_template = next((t for t in results if t.id == template.id), None)
        assert found_template is not None
        assert "标签1" in found_template.tags
    
    @pytest.mark.asyncio
    async def test_search_templates(self, db_session, test_user):
        """测试搜索模板"""
        template = Template(
            name="搜索测试模板",
            content="这是一个用于搜索测试的模板内容",
            description="搜索测试描述",
            user_id=test_user.id,
            is_public=True
        )
        
        db_session.add(template)
        await db_session.commit()
        
        # 按名称搜索
        results = await self.template_service.search_templates(
            db_session, query="搜索测试", skip=0, limit=10
        )
        
        assert len(results) >= 1
        found_template = next((t for t in results if t.id == template.id), None)
        assert found_template is not None
    
    @pytest.mark.asyncio
    async def test_update_template_success(self, db_session, test_template, test_user):
        """测试更新模板成功"""
        update_data = TemplateUpdate(
            name="更新后的模板名称",
            description="更新后的描述",
            tags=["更新", "测试"]
        )
        
        result = await self.template_service.update_template(
            db_session, test_template.id, update_data, test_user.id
        )
        
        assert result is not None
        assert result.name == "更新后的模板名称"
        assert result.description == "更新后的描述"
        assert "更新" in result.tags
    
    @pytest.mark.asyncio
    async def test_update_template_not_found(self, db_session, test_user):
        """测试更新不存在的模板"""
        update_data = TemplateUpdate(name="新名称")
        
        result = await self.template_service.update_template(
            db_session, 99999, update_data, test_user.id
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_template_unauthorized(self, db_session, test_template, test_admin_user):
        """测试更新他人的模板"""
        update_data = TemplateUpdate(name="新名称")
        
        result = await self.template_service.update_template(
            db_session, test_template.id, update_data, test_admin_user.id
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_template_success(self, db_session, test_template, test_user):
        """测试删除模板成功"""
        result = await self.template_service.delete_template(
            db_session, test_template.id, test_user.id
        )
        
        assert result is True
        
        # 验证已删除
        deleted_template = await self.template_service.get_template_by_id(
            db_session, test_template.id
        )
        assert deleted_template is None
    
    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, db_session, test_user):
        """测试删除不存在的模板"""
        result = await self.template_service.delete_template(
            db_session, 99999, test_user.id
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_user_templates(self, db_session, test_user, test_template):
        """测试获取用户模板"""
        results = await self.template_service.get_user_templates(
            db_session, test_user.id, skip=0, limit=10
        )
        
        assert len(results) >= 1
        assert all(t.user_id == test_user.id for t in results)
    
    @pytest.mark.asyncio
    async def test_get_featured_templates(self, db_session, test_user):
        """测试获取精选模板"""
        # 创建精选模板
        featured_template = Template(
            name="精选模板",
            content="精选内容",
            user_id=test_user.id,
            is_public=True,
            is_featured=True
        )
        
        db_session.add(featured_template)
        await db_session.commit()
        
        results = await self.template_service.get_featured_templates(
            db_session, limit=10
        )
        
        assert len(results) >= 1
        assert all(t.is_featured for t in results)
    
    @pytest.mark.asyncio
    async def test_get_template_categories(self, db_session, test_user):
        """测试获取模板分类"""
        # 创建不同分类的模板
        categories = ["分类A", "分类B", "分类C"]
        for category in categories:
            template = Template(
                name=f"{category}模板",
                content="内容",
                category=category,
                user_id=test_user.id,
                is_public=True
            )
            db_session.add(template)
        
        await db_session.commit()
        
        results = await self.template_service.get_template_categories(db_session)
        
        assert len(results) >= 3
        for category in categories:
            assert category in results
    
    @pytest.mark.asyncio
    async def test_get_template_tags(self, db_session, test_user):
        """测试获取模板标签"""
        # 创建带标签的模板
        template = Template(
            name="标签模板",
            content="内容",
            tags=["标签A", "标签B", "标签C"],
            user_id=test_user.id,
            is_public=True
        )
        
        db_session.add(template)
        await db_session.commit()
        
        results = await self.template_service.get_template_tags(db_session)
        
        assert len(results) >= 3
        assert "标签A" in results
        assert "标签B" in results
        assert "标签C" in results


@pytest.mark.asyncio
class TestTemplateEndpoints:
    """模板端点测试"""
    
    async def test_create_template_success(self, async_client, auth_headers, test_data_factory):
        """测试创建模板成功"""
        template_data = test_data_factory.create_template_data()
        
        response = await async_client.post(
            "/api/v1/templates/",
            json=template_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["content"] == template_data["content"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_template_unauthorized(self, async_client, test_data_factory):
        """测试创建模板未授权"""
        template_data = test_data_factory.create_template_data()
        
        response = await async_client.post("/api/v1/templates/", json=template_data)
        
        assert response.status_code == 401
    
    async def test_get_templates_success(self, async_client, test_template):
        """测试获取模板列表成功"""
        response = await async_client.get("/api/v1/templates/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_template_success(self, async_client, test_template):
        """测试获取单个模板成功"""
        response = await async_client.get(f"/api/v1/templates/{test_template.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_template.id
        assert data["name"] == test_template.name
    
    async def test_get_template_not_found(self, async_client):
        """测试获取不存在的模板"""
        response = await async_client.get("/api/v1/templates/99999")
        
        assert response.status_code == 404
    
    async def test_update_template_success(self, async_client, auth_headers, test_template):
        """测试更新模板成功"""
        update_data = {
            "name": "更新后的名称",
            "description": "更新后的描述"
        }
        
        response = await async_client.put(
            f"/api/v1/templates/{test_template.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["description"] == "更新后的描述"
    
    async def test_delete_template_success(self, async_client, auth_headers, test_template):
        """测试删除模板成功"""
        response = await async_client.delete(
            f"/api/v1/templates/{test_template.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    async def test_get_user_templates(self, async_client, auth_headers, test_template):
        """测试获取用户模板"""
        response = await async_client.get(
            "/api/v1/templates/my",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_featured_templates(self, async_client):
        """测试获取精选模板"""
        response = await async_client.get("/api/v1/templates/featured")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_search_templates(self, async_client):
        """测试搜索模板"""
        response = await async_client.get("/api/v1/templates/search?q=测试")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
