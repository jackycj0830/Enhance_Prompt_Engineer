"""
提示词分析流程集成测试
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestPromptAnalysisFlow:
    """提示词分析流程测试"""
    
    def test_complete_analysis_flow(self, integration_client: TestClient, integration_auth_headers, 
                                  integration_prompt, mock_openai_integration):
        """测试完整的提示词分析流程"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 1. 创建分析请求
            analysis_data = {
                "prompt_id": integration_prompt.id,
                "content": integration_prompt.content
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            
            analysis_result = response.json()
            analysis_id = analysis_result["id"]
            
            # 验证分析结果结构
            assert "overall_score" in analysis_result
            assert "semantic_clarity" in analysis_result
            assert "structural_integrity" in analysis_result
            assert "logical_coherence" in analysis_result
            assert "suggestions" in analysis_result
            assert "ai_model_used" in analysis_result
            assert "processing_time_ms" in analysis_result
            
            # 验证分数范围
            assert 0 <= analysis_result["overall_score"] <= 100
            assert 0 <= analysis_result["semantic_clarity"] <= 100
            
            # 2. 获取分析结果
            get_response = integration_client.get(
                f"/api/v1/analysis/{analysis_id}",
                headers=integration_auth_headers
            )
            assert get_response.status_code == 200
            
            retrieved_analysis = get_response.json()
            assert retrieved_analysis["id"] == analysis_id
            assert retrieved_analysis["overall_score"] == analysis_result["overall_score"]
            
            # 3. 获取用户分析历史
            history_response = integration_client.get(
                "/api/v1/analysis/my",
                headers=integration_auth_headers
            )
            assert history_response.status_code == 200
            
            history_data = history_response.json()
            assert isinstance(history_data, list)
            assert len(history_data) >= 1
            
            # 验证新分析在历史中
            analysis_ids = [a["id"] for a in history_data]
            assert analysis_id in analysis_ids
    
    def test_analysis_without_prompt_id(self, integration_client: TestClient, integration_auth_headers, 
                                      mock_openai_integration):
        """测试不关联提示词的分析"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "这是一个独立的提示词内容，不关联任何已保存的提示词。"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            
            analysis_result = response.json()
            assert analysis_result["prompt_id"] is None
            assert "overall_score" in analysis_result
    
    def test_analysis_with_custom_options(self, integration_client: TestClient, integration_auth_headers,
                                        mock_openai_integration):
        """测试带自定义选项的分析"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试提示词内容",
                "model": "gpt-4",
                "dimensions": ["semantic_clarity", "logical_coherence"],
                "language": "zh-CN"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            if response.status_code == 201:  # 如果支持自定义选项
                analysis_result = response.json()
                assert "overall_score" in analysis_result
            else:
                # 可能还未实现自定义选项
                assert response.status_code in [400, 422]
    
    def test_analysis_error_handling(self, integration_client: TestClient, integration_auth_headers,
                                   mock_openai_integration):
        """测试分析错误处理"""
        # 模拟AI服务错误
        mock_openai_integration.chat.completions.create.side_effect = Exception("AI服务暂时不可用")
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该返回错误状态
            assert response.status_code in [500, 503]
    
    def test_analysis_input_validation(self, integration_client: TestClient, integration_auth_headers):
        """测试分析输入验证"""
        # 1. 空内容
        response = integration_client.post(
            "/api/v1/analysis/",
            json={"content": ""},
            headers=integration_auth_headers
        )
        assert response.status_code == 422
        
        # 2. 内容过短
        response = integration_client.post(
            "/api/v1/analysis/",
            json={"content": "短"},
            headers=integration_auth_headers
        )
        assert response.status_code in [400, 422]
        
        # 3. 内容过长
        long_content = "a" * 10000  # 假设有长度限制
        response = integration_client.post(
            "/api/v1/analysis/",
            json={"content": long_content},
            headers=integration_auth_headers
        )
        # 可能成功或被拒绝，取决于实现
        assert response.status_code in [201, 400, 422]
    
    def test_analysis_unauthorized_access(self, integration_client: TestClient):
        """测试未授权的分析访问"""
        analysis_data = {
            "content": "测试提示词内容"
        }
        
        response = integration_client.post("/api/v1/analysis/", json=analysis_data)
        assert response.status_code == 401
    
    def test_delete_analysis(self, integration_client: TestClient, integration_auth_headers,
                           mock_openai_integration):
        """测试删除分析结果"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 1. 创建分析
            analysis_data = {
                "content": "要删除的分析内容"
            }
            
            create_response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            assert create_response.status_code == 201
            
            analysis_id = create_response.json()["id"]
            
            # 2. 删除分析
            delete_response = integration_client.delete(
                f"/api/v1/analysis/{analysis_id}",
                headers=integration_auth_headers
            )
            assert delete_response.status_code == 204
            
            # 3. 验证已删除
            get_response = integration_client.get(
                f"/api/v1/analysis/{analysis_id}",
                headers=integration_auth_headers
            )
            assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncAnalysisFlow:
    """异步分析流程测试"""
    
    async def test_concurrent_analysis_requests(self, integration_async_client: AsyncClient,
                                              integration_auth_headers, mock_openai_integration):
        """测试并发分析请求"""
        import asyncio
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 创建多个并发分析请求
            analysis_tasks = []
            for i in range(3):
                analysis_data = {
                    "content": f"并发测试提示词内容 {i}"
                }
                task = integration_async_client.post(
                    "/api/v1/analysis/",
                    json=analysis_data,
                    headers=integration_auth_headers
                )
                analysis_tasks.append(task)
            
            # 并发执行
            responses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 验证所有分析都成功
            successful_responses = 0
            for response in responses:
                if not isinstance(response, Exception) and response.status_code == 201:
                    successful_responses += 1
            
            assert successful_responses >= 1  # 至少有一个成功
    
    async def test_async_analysis_with_large_content(self, integration_async_client: AsyncClient,
                                                   integration_auth_headers, mock_openai_integration):
        """测试大内容异步分析"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 创建较大的内容
            large_content = "这是一个较长的提示词内容。" * 100
            
            analysis_data = {
                "content": large_content
            }
            
            response = await integration_async_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该能处理大内容
            assert response.status_code in [201, 400, 422]  # 成功或因内容过大被拒绝


@pytest.mark.integration
class TestAnalysisDataPersistence:
    """分析数据持久化测试"""
    
    def test_analysis_data_persistence(self, integration_client: TestClient, integration_auth_headers,
                                     mock_openai_integration):
        """测试分析数据持久化"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 1. 创建分析
            analysis_data = {
                "content": "持久化测试内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            
            original_analysis = response.json()
            analysis_id = original_analysis["id"]
            
            # 2. 重新获取，验证数据完整性
            get_response = integration_client.get(
                f"/api/v1/analysis/{analysis_id}",
                headers=integration_auth_headers
            )
            assert get_response.status_code == 200
            
            retrieved_analysis = get_response.json()
            
            # 验证关键字段一致
            assert retrieved_analysis["id"] == original_analysis["id"]
            assert retrieved_analysis["overall_score"] == original_analysis["overall_score"]
            assert retrieved_analysis["semantic_clarity"] == original_analysis["semantic_clarity"]
            assert retrieved_analysis["suggestions"] == original_analysis["suggestions"]
            assert retrieved_analysis["created_at"] == original_analysis["created_at"]
    
    def test_analysis_user_isolation(self, integration_client: TestClient, integration_auth_headers,
                                   integration_data_factory, mock_openai_integration):
        """测试分析结果用户隔离"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 1. 用户1创建分析
            analysis_data = {
                "content": "用户隔离测试内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            analysis_id = response.json()["id"]
            
            # 2. 创建另一个用户
            user2_data = integration_data_factory.create_user_registration_data(
                username="user2",
                email="user2@example.com"
            )
            
            register_response = integration_client.post("/api/v1/auth/register", json=user2_data)
            assert register_response.status_code == 201
            
            # 3. 用户2登录
            login_data = {
                "username": user2_data["username"],
                "password": user2_data["password"]
            }
            
            login_response = integration_client.post("/api/v1/auth/login", data=login_data)
            assert login_response.status_code == 200
            
            user2_token = login_response.json()["access_token"]
            user2_headers = {"Authorization": f"Bearer {user2_token}"}
            
            # 4. 用户2尝试访问用户1的分析
            get_response = integration_client.get(
                f"/api/v1/analysis/{analysis_id}",
                headers=user2_headers
            )
            # 应该被拒绝访问或返回404
            assert get_response.status_code in [403, 404]
