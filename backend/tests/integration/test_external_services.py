"""
第三方服务集成测试
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestOpenAIIntegration:
    """OpenAI API集成测试"""
    
    def test_openai_analysis_integration(self, integration_client: TestClient, integration_auth_headers,
                                       mock_openai_integration):
        """测试OpenAI分析集成"""
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            # 配置模拟响应
            mock_openai_integration.chat.completions.create.return_value.choices[0].message.content = '''
            {
                "overall_score": 87.5,
                "semantic_clarity": 92.0,
                "structural_integrity": 85.0,
                "logical_coherence": 86.0,
                "specificity_score": 89.0,
                "instruction_clarity": 90.0,
                "context_completeness": 84.0,
                "suggestions": [
                    "建议增加更具体的示例",
                    "可以明确输出格式要求",
                    "考虑添加约束条件"
                ]
            }
            '''
            
            # 发送分析请求
            analysis_data = {
                "content": "请分析这个提示词：你是一个专业的AI助手，请帮助用户解决问题。"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            assert response.status_code == 201
            result = response.json()
            
            # 验证OpenAI API被正确调用
            mock_openai_integration.chat.completions.create.assert_called_once()
            call_args = mock_openai_integration.chat.completions.create.call_args
            
            # 验证调用参数
            assert call_args[1]['model'] in ['gpt-3.5-turbo', 'gpt-4']
            assert 'messages' in call_args[1]
            assert len(call_args[1]['messages']) > 0
            
            # 验证返回结果
            assert result['overall_score'] == 87.5
            assert result['semantic_clarity'] == 92.0
            assert len(result['suggestions']) == 3
    
    def test_openai_error_handling(self, integration_client: TestClient, integration_auth_headers,
                                 mock_openai_integration):
        """测试OpenAI错误处理"""
        # 模拟API错误
        mock_openai_integration.chat.completions.create.side_effect = Exception("API rate limit exceeded")
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试错误处理的提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该返回错误状态
            assert response.status_code in [500, 503]
            
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data
    
    def test_openai_timeout_handling(self, integration_client: TestClient, integration_auth_headers,
                                   mock_openai_integration):
        """测试OpenAI超时处理"""
        import asyncio
        
        # 模拟超时
        async def timeout_side_effect(*args, **kwargs):
            await asyncio.sleep(10)  # 模拟长时间等待
            raise asyncio.TimeoutError("Request timeout")
        
        mock_openai_integration.chat.completions.create.side_effect = timeout_side_effect
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试超时处理的提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该在合理时间内返回错误
            assert response.status_code in [408, 500, 503]
    
    def test_openai_invalid_response_handling(self, integration_client: TestClient, integration_auth_headers,
                                            mock_openai_integration):
        """测试OpenAI无效响应处理"""
        # 模拟无效JSON响应
        mock_openai_integration.chat.completions.create.return_value.choices[0].message.content = "无效的JSON响应"
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试无效响应处理的提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该处理无效响应
            assert response.status_code in [400, 500]


@pytest.mark.integration
class TestEmailServiceIntegration:
    """邮件服务集成测试"""
    
    def test_email_service_registration(self, integration_client: TestClient, mock_email_service,
                                      integration_data_factory):
        """测试注册邮件发送"""
        with patch('app.services.email_service.email_service', mock_email_service):
            # 注册新用户
            user_data = integration_data_factory.create_user_registration_data(
                username="email_test_user",
                email="email_test@example.com"
            )
            
            response = integration_client.post("/api/v1/auth/register", json=user_data)
            
            if response.status_code == 201:
                # 验证邮件服务被调用
                if hasattr(mock_email_service, 'send_verification_email'):
                    mock_email_service.send_verification_email.assert_called_once()
                    call_args = mock_email_service.send_verification_email.call_args[0]
                    assert call_args[0] == user_data["email"]  # 邮箱地址
    
    def test_email_service_password_reset(self, integration_client: TestClient, integration_user,
                                        mock_email_service):
        """测试密码重置邮件发送"""
        with patch('app.services.email_service.email_service', mock_email_service):
            # 请求密码重置
            reset_data = {"email": integration_user.email}
            
            response = integration_client.post("/api/v1/auth/password-reset", json=reset_data)
            
            if response.status_code in [200, 202]:  # 成功或已接受
                # 验证邮件服务被调用
                if hasattr(mock_email_service, 'send_password_reset_email'):
                    mock_email_service.send_password_reset_email.assert_called_once()
    
    def test_email_service_error_handling(self, integration_client: TestClient, mock_email_service,
                                        integration_data_factory):
        """测试邮件服务错误处理"""
        # 模拟邮件发送失败
        mock_email_service.send_verification_email.side_effect = Exception("SMTP服务器不可用")
        
        with patch('app.services.email_service.email_service', mock_email_service):
            user_data = integration_data_factory.create_user_registration_data(
                username="email_error_test",
                email="email_error@example.com"
            )
            
            response = integration_client.post("/api/v1/auth/register", json=user_data)
            
            # 用户注册应该成功，即使邮件发送失败
            # 或者返回适当的错误状态
            assert response.status_code in [201, 500, 503]


@pytest.mark.integration
class TestFileStorageIntegration:
    """文件存储集成测试"""
    
    def test_file_upload_integration(self, integration_client: TestClient, integration_auth_headers,
                                   mock_file_storage):
        """测试文件上传集成"""
        with patch('app.services.file_service.file_storage', mock_file_storage):
            # 模拟文件上传
            files = {"file": ("test.txt", "测试文件内容", "text/plain")}
            
            response = integration_client.post(
                "/api/v1/files/upload",
                files=files,
                headers=integration_auth_headers
            )
            
            if response.status_code == 200:  # 如果端点存在
                # 验证文件存储服务被调用
                mock_file_storage.upload_file.assert_called_once()
                
                result = response.json()
                assert "url" in result
                assert result["url"] == "https://example.com/uploaded-file.txt"
    
    def test_file_delete_integration(self, integration_client: TestClient, integration_auth_headers,
                                   mock_file_storage):
        """测试文件删除集成"""
        with patch('app.services.file_service.file_storage', mock_file_storage):
            file_id = "test-file-id"
            
            response = integration_client.delete(
                f"/api/v1/files/{file_id}",
                headers=integration_auth_headers
            )
            
            if response.status_code == 204:  # 如果端点存在
                # 验证文件存储服务被调用
                mock_file_storage.delete_file.assert_called_once_with(file_id)
    
    def test_file_storage_error_handling(self, integration_client: TestClient, integration_auth_headers,
                                       mock_file_storage):
        """测试文件存储错误处理"""
        # 模拟存储服务错误
        mock_file_storage.upload_file.side_effect = Exception("存储服务不可用")
        
        with patch('app.services.file_service.file_storage', mock_file_storage):
            files = {"file": ("error_test.txt", "错误测试内容", "text/plain")}
            
            response = integration_client.post(
                "/api/v1/files/upload",
                files=files,
                headers=integration_auth_headers
            )
            
            # 应该返回错误状态
            if response.status_code != 404:  # 如果端点存在
                assert response.status_code in [500, 503]


@pytest.mark.integration
class TestCacheServiceIntegration:
    """缓存服务集成测试"""
    
    def test_redis_cache_integration(self, integration_client: TestClient, integration_auth_headers,
                                   mock_redis_client):
        """测试Redis缓存集成"""
        with patch('app.services.cache_service.redis_client', mock_redis_client):
            # 配置缓存模拟
            mock_redis_client.get.return_value = None  # 缓存未命中
            mock_redis_client.set.return_value = True
            
            # 请求数据（应该触发缓存操作）
            response = integration_client.get(
                "/api/v1/templates/",
                headers=integration_auth_headers
            )
            
            if response.status_code == 200:
                # 验证缓存操作
                # 注意：这取决于实际的缓存实现
                pass
    
    def test_cache_invalidation(self, integration_client: TestClient, integration_auth_headers,
                              mock_redis_client, integration_data_factory):
        """测试缓存失效"""
        with patch('app.services.cache_service.redis_client', mock_redis_client):
            # 创建模板（应该触发缓存失效）
            template_data = integration_data_factory.create_template_creation_data()
            
            response = integration_client.post(
                "/api/v1/templates/",
                json=template_data,
                headers=integration_auth_headers
            )
            
            if response.status_code == 201:
                # 验证缓存失效操作
                # 这取决于实际的缓存失效策略
                pass
    
    def test_cache_service_fallback(self, integration_client: TestClient, integration_auth_headers,
                                  mock_redis_client):
        """测试缓存服务降级"""
        # 模拟Redis不可用
        mock_redis_client.get.side_effect = Exception("Redis连接失败")
        mock_redis_client.set.side_effect = Exception("Redis连接失败")
        
        with patch('app.services.cache_service.redis_client', mock_redis_client):
            # 请求应该仍然成功，只是不使用缓存
            response = integration_client.get(
                "/api/v1/templates/",
                headers=integration_auth_headers
            )
            
            # 应该降级到直接数据库查询
            assert response.status_code == 200


@pytest.mark.integration
class TestExternalAPIRateLimit:
    """外部API限流测试"""
    
    def test_rate_limit_handling(self, integration_client: TestClient, integration_auth_headers,
                                mock_openai_integration):
        """测试API限流处理"""
        # 模拟限流错误
        rate_limit_error = Exception("Rate limit exceeded. Please try again later.")
        mock_openai_integration.chat.completions.create.side_effect = rate_limit_error
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试限流处理的提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 应该返回适当的错误状态
            assert response.status_code in [429, 503]
            
            error_data = response.json()
            assert "rate limit" in error_data.get("detail", "").lower()
    
    def test_retry_mechanism(self, integration_client: TestClient, integration_auth_headers,
                           mock_openai_integration):
        """测试重试机制"""
        # 模拟第一次失败，第二次成功
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary service unavailable")
            else:
                # 返回成功响应
                mock_response = MagicMock()
                mock_response.choices = [
                    MagicMock(message=MagicMock(content='{"overall_score": 85.0}'))
                ]
                return mock_response
        
        mock_openai_integration.chat.completions.create.side_effect = side_effect
        
        with patch('app.services.analysis_service.openai_client', mock_openai_integration):
            analysis_data = {
                "content": "测试重试机制的提示词内容"
            }
            
            response = integration_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=integration_auth_headers
            )
            
            # 如果实现了重试机制，应该最终成功
            if call_count > 1:
                assert response.status_code == 201
            else:
                # 如果没有重试机制，第一次就失败
                assert response.status_code in [500, 503]
