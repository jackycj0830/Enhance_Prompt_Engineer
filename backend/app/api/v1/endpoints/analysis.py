"""
提示词分析API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import time
import asyncio

from config.database import get_db
from app.models.user import User
from app.models.prompt import Prompt, AnalysisResult, OptimizationSuggestion
from app.api.v1.endpoints.auth import get_current_user
from app.services.ai_client import get_ai_client
from app.services.prompt_analyzer import get_prompt_analyzer

router = APIRouter()

async def analyze_prompt_with_ai(content: str, model: str = "gpt-3.5-turbo") -> dict:
    """使用真实AI服务分析提示词"""
    try:
        ai_client = get_ai_client()
        analyzer = get_prompt_analyzer(ai_client)

        # 执行完整分析
        analysis_result = await analyzer.analyze_prompt(
            text=content,
            model=model,
            use_ai_analysis=True
        )

        return {
            "overall_score": analysis_result.metrics.overall_score,
            "semantic_clarity": analysis_result.metrics.semantic_clarity,
            "structural_integrity": analysis_result.metrics.structural_integrity,
            "logical_coherence": analysis_result.metrics.logical_coherence,
            "specificity_score": analysis_result.metrics.specificity_score,
            "instruction_clarity": analysis_result.metrics.instruction_clarity,
            "context_completeness": analysis_result.metrics.context_completeness,
            "readability_score": analysis_result.metrics.readability_score,
            "complexity_score": analysis_result.metrics.complexity_score,
            "analysis_details": analysis_result.analysis_details,
            "strengths": analysis_result.strengths,
            "weaknesses": analysis_result.weaknesses,
            "suggestions": analysis_result.suggestions,
            "processing_time": analysis_result.processing_time,
            "model_used": analysis_result.model_used
        }

    except Exception as e:
        # 如果AI分析失败，回退到基础分析
        print(f"AI分析失败，使用基础分析: {str(e)}")
        return await fallback_analysis(content)

async def fallback_analysis(content: str) -> dict:
    """基础分析（当AI服务不可用时的回退方案）"""
    word_count = len(content.split())
    sentence_count = content.count('.') + content.count('!') + content.count('?')

    # 基于内容长度和结构的评分算法
    base_score = min(90, max(60, word_count * 2))

    # 简单的启发式评分
    semantic_clarity = min(100, max(50, base_score + (10 if '?' in content else 0)))
    structural_integrity = min(100, max(50, base_score + (15 if any(word in content.lower() for word in ['format', 'structure', 'example']) else 0)))
    logical_coherence = min(100, max(50, base_score + (10 if sentence_count > 1 else -10)))

    overall_score = int((semantic_clarity + structural_integrity + logical_coherence) / 3)

    return {
        "overall_score": overall_score,
        "semantic_clarity": semantic_clarity,
        "structural_integrity": structural_integrity,
        "logical_coherence": logical_coherence,
        "specificity_score": 70,
        "instruction_clarity": 65,
        "context_completeness": min(100, word_count * 2),
        "readability_score": 75,
        "complexity_score": min(10, word_count / 10),
        "analysis_details": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "basic_analysis": True,
            "ai_analysis_failed": True
        },
        "strengths": ["基础结构完整"],
        "weaknesses": ["需要更详细的分析"],
        "suggestions": ["建议配置AI服务以获得更准确的分析结果"],
        "processing_time": 0.1,
        "model_used": "rule-based"
    }

@router.post("/analyze")
async def analyze_prompt(
    analysis_request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分析提示词"""
    content = analysis_request.get("content")
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="提示词内容不能为空"
        )
    
    prompt_id = analysis_request.get("prompt_id")
    ai_model = analysis_request.get("ai_model", "gpt-3.5-turbo")
    
    # 如果提供了prompt_id，验证用户权限
    if prompt_id:
        prompt = db.query(Prompt).filter(
            Prompt.id == prompt_id,
            Prompt.user_id == current_user.id
        ).first()
        
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词不存在"
            )
    else:
        # 创建临时提示词记录
        prompt = Prompt(
            user_id=current_user.id,
            title="临时分析",
            content=content,
            is_template=False,
            is_public=False
        )
        db.add(prompt)
        db.flush()
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行AI分析
    analysis_data = await analyze_prompt_with_ai(content, ai_model)
    
    # 计算处理时间
    processing_time = int((time.time() - start_time) * 1000)
    
    # 保存分析结果
    analysis = AnalysisResult(
        prompt_id=prompt.id,
        overall_score=analysis_data["overall_score"],
        semantic_clarity=analysis_data["semantic_clarity"],
        structural_integrity=analysis_data["structural_integrity"],
        logical_coherence=analysis_data["logical_coherence"],
        analysis_details={
            **analysis_data.get("analysis_details", {}),
            "specificity_score": analysis_data.get("specificity_score", 0),
            "instruction_clarity": analysis_data.get("instruction_clarity", 0),
            "context_completeness": analysis_data.get("context_completeness", 0),
            "readability_score": analysis_data.get("readability_score", 0),
            "strengths": analysis_data.get("strengths", []),
            "weaknesses": analysis_data.get("weaknesses", []),
            "suggestions": analysis_data.get("suggestions", [])
        },
        processing_time_ms=int(analysis_data.get("processing_time", processing_time) * 1000),
        ai_model_used=analysis_data.get("model_used", ai_model)
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    return analysis.to_dict()

@router.get("/{analysis_id}")
async def get_analysis_result(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取分析结果"""
    analysis = db.query(AnalysisResult).join(Prompt).filter(
        AnalysisResult.id == analysis_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    return analysis.to_dict()

@router.get("/")
async def get_analysis_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的分析历史"""
    analyses = db.query(AnalysisResult).join(Prompt).filter(
        Prompt.user_id == current_user.id
    ).order_by(AnalysisResult.created_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(AnalysisResult).join(Prompt).filter(
        Prompt.user_id == current_user.id
    ).count()
    
    return {
        "items": [analysis.to_dict() for analysis in analyses],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除分析结果"""
    analysis = db.query(AnalysisResult).join(Prompt).filter(
        AnalysisResult.id == analysis_id,
        Prompt.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "分析结果已删除"}
