"""
优化建议API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import random

from config.database import get_db
from app.models.user import User
from app.models.prompt import AnalysisResult, OptimizationSuggestion
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

def generate_mock_suggestions(analysis: AnalysisResult) -> List[dict]:
    """生成模拟优化建议（后续会替换为真实的AI建议）"""
    suggestions = []
    
    # 基于分析结果生成建议
    if analysis.semantic_clarity < 80:
        suggestions.append({
            "type": "clarity",
            "priority": 1,
            "description": "建议使用更具体和明确的词汇来提高语义清晰度",
            "plan": "将模糊的词汇如'一些'、'可能'替换为更精确的表达",
            "impact": "high"
        })
    
    if analysis.structural_integrity < 75:
        suggestions.append({
            "type": "structure",
            "priority": 2,
            "description": "优化提示词的结构组织，使逻辑更清晰",
            "plan": "使用编号列表或分段来组织不同的指令要求",
            "impact": "medium"
        })
    
    if analysis.logical_coherence < 85:
        suggestions.append({
            "type": "coherence",
            "priority": 1,
            "description": "增强指令之间的逻辑连贯性",
            "plan": "添加过渡词和连接词来改善指令流程",
            "impact": "high"
        })
    
    # 通用建议
    if analysis.overall_score < 90:
        suggestions.append({
            "type": "enhancement",
            "priority": 3,
            "description": "添加更多上下文信息来提高指令的完整性",
            "plan": "在提示词开头添加角色设定和背景信息",
            "impact": "medium"
        })
        
        suggestions.append({
            "type": "format",
            "priority": 4,
            "description": "改进提示词的格式和可读性",
            "plan": "使用标题、分点和强调来提高视觉层次",
            "impact": "low"
        })
    
    return suggestions[:3]  # 最多返回3个建议

@router.post("/suggest")
async def generate_suggestions(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为分析结果生成优化建议"""
    analysis_id = request.get("analysis_id")
    if not analysis_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分析ID不能为空"
        )
    
    # 验证分析结果存在且属于当前用户
    analysis = db.query(AnalysisResult).join(
        AnalysisResult.prompt
    ).filter(
        AnalysisResult.id == analysis_id,
        AnalysisResult.prompt.has(user_id=current_user.id)
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    # 检查是否已有建议
    existing_suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.analysis_id == analysis_id
    ).all()
    
    if existing_suggestions:
        return {
            "suggestions": [s.to_dict() for s in existing_suggestions],
            "message": "返回已有的优化建议"
        }
    
    # 生成新建议
    suggestions_data = generate_mock_suggestions(analysis)
    
    created_suggestions = []
    for i, sugg_data in enumerate(suggestions_data):
        suggestion = OptimizationSuggestion(
            analysis_id=analysis_id,
            suggestion_type=sugg_data["type"],
            priority=sugg_data["priority"],
            description=sugg_data["description"],
            improvement_plan=sugg_data["plan"],
            expected_impact=sugg_data["impact"],
            is_applied=False
        )
        db.add(suggestion)
        created_suggestions.append(suggestion)
    
    db.commit()
    
    for suggestion in created_suggestions:
        db.refresh(suggestion)
    
    return {
        "suggestions": [s.to_dict() for s in created_suggestions],
        "message": "成功生成优化建议"
    }

@router.get("/{analysis_id}/suggestions")
async def get_suggestions(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定分析的优化建议"""
    # 验证分析结果存在且属于当前用户
    analysis = db.query(AnalysisResult).join(
        AnalysisResult.prompt
    ).filter(
        AnalysisResult.id == analysis_id,
        AnalysisResult.prompt.has(user_id=current_user.id)
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析结果不存在"
        )
    
    suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.analysis_id == analysis_id
    ).order_by(OptimizationSuggestion.priority).all()
    
    return [s.to_dict() for s in suggestions]

@router.put("/{suggestion_id}/apply")
async def apply_suggestion(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """应用优化建议"""
    suggestion = db.query(OptimizationSuggestion).join(
        OptimizationSuggestion.analysis
    ).join(
        AnalysisResult.prompt
    ).filter(
        OptimizationSuggestion.id == suggestion_id,
        AnalysisResult.prompt.has(user_id=current_user.id)
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="优化建议不存在"
        )
    
    suggestion.is_applied = True
    db.commit()
    db.refresh(suggestion)
    
    return {
        "message": "优化建议已应用",
        "suggestion": suggestion.to_dict()
    }

@router.delete("/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除优化建议"""
    suggestion = db.query(OptimizationSuggestion).join(
        OptimizationSuggestion.analysis
    ).join(
        AnalysisResult.prompt
    ).filter(
        OptimizationSuggestion.id == suggestion_id,
        AnalysisResult.prompt.has(user_id=current_user.id)
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="优化建议不存在"
        )
    
    db.delete(suggestion)
    db.commit()
    
    return {"message": "优化建议已删除"}
