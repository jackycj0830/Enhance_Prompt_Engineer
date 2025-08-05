"""
提示词分析API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import time
import random

from config.database import get_db
from app.models.user import User
from app.models.prompt import Prompt, AnalysisResult, OptimizationSuggestion
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

def mock_analyze_prompt(content: str) -> dict:
    """模拟提示词分析（后续会替换为真实的AI分析）"""
    word_count = len(content.split())
    sentence_count = content.count('.') + content.count('!') + content.count('?')
    
    # 基于内容长度和结构的简单评分算法
    base_score = min(90, max(60, word_count * 2))
    
    # 添加一些随机性来模拟真实分析
    semantic_clarity = min(100, max(50, base_score + random.randint(-10, 10)))
    structural_integrity = min(100, max(50, base_score + random.randint(-15, 15)))
    logical_coherence = min(100, max(50, base_score + random.randint(-5, 20)))
    
    overall_score = int((semantic_clarity + structural_integrity + logical_coherence) / 3)
    
    return {
        "overall_score": overall_score,
        "semantic_clarity": semantic_clarity,
        "structural_integrity": structural_integrity,
        "logical_coherence": logical_coherence,
        "analysis_details": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "complexity_score": min(10, word_count / 10),
            "clarity_issues": [],
            "structure_suggestions": [],
            "coherence_notes": []
        }
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
    
    # 执行分析（目前使用模拟分析）
    analysis_data = mock_analyze_prompt(content)
    
    # 计算处理时间
    processing_time = int((time.time() - start_time) * 1000)
    
    # 保存分析结果
    analysis = AnalysisResult(
        prompt_id=prompt.id,
        overall_score=analysis_data["overall_score"],
        semantic_clarity=analysis_data["semantic_clarity"],
        structural_integrity=analysis_data["structural_integrity"],
        logical_coherence=analysis_data["logical_coherence"],
        analysis_details=analysis_data["analysis_details"],
        processing_time_ms=processing_time,
        ai_model_used=ai_model
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
