"""
提示词分析模块测试
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.analysis_service import AnalysisService
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisResponse


class TestAnalysisService:
    """分析服务测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.analysis_service = AnalysisService()
    
    @pytest.mark.asyncio
    async def test_analyze_prompt_success(self, db_session, test_user, test_prompt, mock_openai_client):
        """测试提示词分析成功"""
        with patch('app.services.analysis_service.openai_client', mock_openai_client):
            # 模拟AI分析响应
            mock_openai_client.chat.completions.create.return_value.choices[0].message.content = '''
            {
                "overall_score": 85.5,
                "semantic_clarity": 90.0,
                "structural_integrity": 85.0,
                "logical_coherence": 80.0,
                "specificity_score": 88.0,
                "instruction_clarity": 92.0,
                "context_completeness": 85.0,
                "suggestions": [
                    "建议增加更多具体的示例",
                    "可以进一步明确输出格式要求"
                ]
            }
            '''
            
            analysis_data = AnalysisCreate(
                prompt_id=test_prompt.id,
                content=test_prompt.content
            )
            
            result = await self.analysis_service.analyze_prompt(
                db_session, analysis_data, test_user.id
            )
            
            assert isinstance(result, Analysis)
            assert result.prompt_id == test_prompt.id
            assert result.user_id == test_user.id
            assert result.overall_score == 85.5
            assert result.semantic_clarity == 90.0
            assert len(result.suggestions) == 2
            assert result.ai_model_used is not None
            assert result.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_analyze_prompt_ai_error(self, db_session, test_user, test_prompt, mock_openai_client):
        """测试AI分析错误处理"""
        with patch('app.services.analysis_service.openai_client', mock_openai_client):
            # 模拟AI调用失败
            mock_openai_client.chat.completions.create.side_effect = Exception("API调用失败")
            
            analysis_data = AnalysisCreate(
                prompt_id=test_prompt.id,
                content=test_prompt.content
            )
            
            with pytest.raises(Exception) as exc_info:
                await self.analysis_service.analyze_prompt(
                    db_session, analysis_data, test_user.id
                )
            
            assert "API调用失败" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_success(self, db_session, test_analysis):
        """测试根据ID获取分析结果成功"""
        result = await self.analysis_service.get_analysis_by_id(
            db_session, test_analysis.id
        )
        
        assert result is not None
        assert result.id == test_analysis.id
        assert result.overall_score == test_analysis.overall_score
    
    @pytest.mark.asyncio
    async def test_get_analysis_by_id_not_found(self, db_session):
        """测试根据ID获取分析结果不存在"""
        result = await self.analysis_service.get_analysis_by_id(
            db_session, 99999
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_analyses(self, db_session, test_user, test_analysis):
        """测试获取用户分析历史"""
        results = await self.analysis_service.get_user_analyses(
            db_session, test_user.id, skip=0, limit=10
        )
        
        assert len(results) >= 1
        assert results[0].user_id == test_user.id
        assert results[0].id == test_analysis.id
    
    @pytest.mark.asyncio
    async def test_get_user_analyses_pagination(self, db_session, test_user):
        """测试用户分析历史分页"""
        # 创建多个分析记录
        for i in range(5):
            analysis = Analysis(
                prompt_id=1,
                user_id=test_user.id,
                overall_score=80.0 + i,
                semantic_clarity=85.0,
                structural_integrity=80.0,
                logical_coherence=75.0,
                analysis_details={"test": True},
                suggestions=["建议" + str(i)],
                ai_model_used="gpt-3.5-turbo",
                processing_time_ms=1000
            )
            db_session.add(analysis)
        
        await db_session.commit()
        
        # 测试分页
        page1 = await self.analysis_service.get_user_analyses(
            db_session, test_user.id, skip=0, limit=3
        )
        page2 = await self.analysis_service.get_user_analyses(
            db_session, test_user.id, skip=3, limit=3
        )
        
        assert len(page1) == 3
        assert len(page2) >= 2
        assert page1[0].id != page2[0].id
    
    @pytest.mark.asyncio
    async def test_delete_analysis_success(self, db_session, test_analysis, test_user):
        """测试删除分析结果成功"""
        result = await self.analysis_service.delete_analysis(
            db_session, test_analysis.id, test_user.id
        )
        
        assert result is True
        
        # 验证已删除
        deleted_analysis = await self.analysis_service.get_analysis_by_id(
            db_session, test_analysis.id
        )
        assert deleted_analysis is None
    
    @pytest.mark.asyncio
    async def test_delete_analysis_not_found(self, db_session, test_user):
        """测试删除不存在的分析结果"""
        result = await self.analysis_service.delete_analysis(
            db_session, 99999, test_user.id
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_analysis_unauthorized(self, db_session, test_analysis, test_admin_user):
        """测试删除他人的分析结果"""
        result = await self.analysis_service.delete_analysis(
            db_session, test_analysis.id, test_admin_user.id
        )
        
        assert result is False
    
    def test_calculate_text_metrics(self):
        """测试文本指标计算"""
        text = "这是一个测试文本。它包含多个句子。用于测试文本分析功能。"
        
        metrics = self.analysis_service._calculate_text_metrics(text)
        
        assert "word_count" in metrics
        assert "sentence_count" in metrics
        assert "avg_sentence_length" in metrics
        assert "complexity_score" in metrics
        assert "readability_score" in metrics
        
        assert metrics["sentence_count"] == 3
        assert metrics["word_count"] > 0
        assert 0 <= metrics["complexity_score"] <= 1
        assert 0 <= metrics["readability_score"] <= 1
    
    def test_calculate_text_metrics_empty(self):
        """测试空文本指标计算"""
        text = ""
        
        metrics = self.analysis_service._calculate_text_metrics(text)
        
        assert metrics["word_count"] == 0
        assert metrics["sentence_count"] == 0
        assert metrics["avg_sentence_length"] == 0
    
    def test_parse_ai_response_valid(self):
        """测试解析有效的AI响应"""
        ai_response = '''
        {
            "overall_score": 85.5,
            "semantic_clarity": 90.0,
            "structural_integrity": 85.0,
            "logical_coherence": 80.0,
            "suggestions": ["建议1", "建议2"]
        }
        '''
        
        result = self.analysis_service._parse_ai_response(ai_response)
        
        assert result["overall_score"] == 85.5
        assert result["semantic_clarity"] == 90.0
        assert len(result["suggestions"]) == 2
    
    def test_parse_ai_response_invalid_json(self):
        """测试解析无效JSON响应"""
        ai_response = "这不是一个有效的JSON"
        
        with pytest.raises(ValueError):
            self.analysis_service._parse_ai_response(ai_response)
    
    def test_parse_ai_response_missing_fields(self):
        """测试解析缺少字段的响应"""
        ai_response = '{"overall_score": 85.5}'
        
        result = self.analysis_service._parse_ai_response(ai_response)
        
        # 应该有默认值
        assert result["overall_score"] == 85.5
        assert "semantic_clarity" in result
        assert "suggestions" in result


@pytest.mark.asyncio
class TestAnalysisEndpoints:
    """分析端点测试"""
    
    async def test_create_analysis_success(self, async_client, auth_headers, test_prompt, mock_openai_client):
        """测试创建分析成功"""
        with patch('app.services.analysis_service.openai_client', mock_openai_client):
            mock_openai_client.chat.completions.create.return_value.choices[0].message.content = '''
            {
                "overall_score": 85.5,
                "semantic_clarity": 90.0,
                "structural_integrity": 85.0,
                "logical_coherence": 80.0,
                "suggestions": ["建议1"]
            }
            '''
            
            analysis_data = {
                "prompt_id": test_prompt.id,
                "content": "测试提示词内容"
            }
            
            response = await async_client.post(
                "/api/v1/analysis/",
                json=analysis_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["prompt_id"] == test_prompt.id
            assert data["overall_score"] == 85.5
            assert "id" in data
            assert "created_at" in data
    
    async def test_create_analysis_unauthorized(self, async_client, test_prompt):
        """测试创建分析未授权"""
        analysis_data = {
            "prompt_id": test_prompt.id,
            "content": "测试提示词内容"
        }
        
        response = await async_client.post("/api/v1/analysis/", json=analysis_data)
        
        assert response.status_code == 401
    
    async def test_get_analysis_success(self, async_client, auth_headers, test_analysis):
        """测试获取分析结果成功"""
        response = await async_client.get(
            f"/api/v1/analysis/{test_analysis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_analysis.id
        assert data["overall_score"] == test_analysis.overall_score
    
    async def test_get_analysis_not_found(self, async_client, auth_headers):
        """测试获取不存在的分析结果"""
        response = await async_client.get(
            "/api/v1/analysis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    async def test_get_user_analyses(self, async_client, auth_headers, test_analysis):
        """测试获取用户分析历史"""
        response = await async_client.get(
            "/api/v1/analysis/my",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == test_analysis.id
    
    async def test_delete_analysis_success(self, async_client, auth_headers, test_analysis):
        """测试删除分析结果成功"""
        response = await async_client.delete(
            f"/api/v1/analysis/{test_analysis.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    async def test_delete_analysis_not_found(self, async_client, auth_headers):
        """测试删除不存在的分析结果"""
        response = await async_client.delete(
            "/api/v1/analysis/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
