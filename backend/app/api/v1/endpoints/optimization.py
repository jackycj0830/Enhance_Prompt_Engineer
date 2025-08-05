"""
优化建议API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio

from config.database import get_db
from app.models.user import User, UserPreference
from app.models.prompt import AnalysisResult, OptimizationSuggestion
from app.api.v1.endpoints.auth import get_current_user
from app.services.ai_client import get_ai_client
from app.services.optimization_engine import get_optimization_engine
from app.services.prompt_analyzer import get_prompt_analyzer

router = APIRouter()

async def generate_intelligent_suggestions(
    analysis: AnalysisResult,
    user_preferences: Dict[str, Any],
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """使用智能引擎生成优化建议"""
    try:
        ai_client = get_ai_client()
        analyzer = get_prompt_analyzer(ai_client)
        optimization_engine = get_optimization_engine(ai_client)

        # 重构分析结果为DetailedAnalysis格式
        from app.services.prompt_analyzer import AnalysisMetrics, DetailedAnalysis

        metrics = AnalysisMetrics(
            overall_score=analysis.overall_score,
            semantic_clarity=analysis.semantic_clarity,
            structural_integrity=analysis.structural_integrity,
            logical_coherence=analysis.logical_coherence,
            specificity_score=analysis.analysis_details.get('specificity_score', 70),
            complexity_score=analysis.analysis_details.get('complexity_score', 5.0),
            readability_score=analysis.analysis_details.get('readability_score', 75),
            instruction_clarity=analysis.analysis_details.get('instruction_clarity', 70),
            context_completeness=analysis.analysis_details.get('context_completeness', 70)
        )

        detailed_analysis = DetailedAnalysis(
            metrics=metrics,
            analysis_details=analysis.analysis_details,
            suggestions=analysis.analysis_details.get('suggestions', []),
            strengths=analysis.analysis_details.get('strengths', []),
            weaknesses=analysis.analysis_details.get('weaknesses', []),
            processing_time=analysis.processing_time_ms / 1000.0,
            model_used=analysis.ai_model_used
        )

        # 生成优化结果
        optimization_result = await optimization_engine.generate_optimization_result(
            analysis=detailed_analysis,
            user_preferences=user_preferences,
            model=model,
            use_ai_suggestions=True
        )

        return {
            "suggestions": [
                {
                    "id": sugg.id,
                    "type": sugg.type.value,
                    "priority": sugg.priority.value,
                    "impact": sugg.impact.value,
                    "title": sugg.title,
                    "description": sugg.description,
                    "improvement_plan": sugg.improvement_plan,
                    "expected_improvement": sugg.expected_improvement,
                    "examples": sugg.examples,
                    "reasoning": sugg.reasoning,
                    "confidence": sugg.confidence
                }
                for sugg in optimization_result.suggestions
            ],
            "personalized_recommendations": optimization_result.personalized_recommendations,
            "improvement_roadmap": optimization_result.improvement_roadmap,
            "estimated_score_improvement": optimization_result.estimated_score_improvement,
            "processing_time": optimization_result.processing_time,
            "model_used": optimization_result.model_used
        }

    except Exception as e:
        print(f"智能建议生成失败: {e}")
        return await fallback_suggestions(analysis)

async def fallback_suggestions(analysis: AnalysisResult) -> Dict[str, Any]:
    """回退建议生成（当智能引擎不可用时）"""
    suggestions = []

    # 基于分析结果生成基础建议
    if analysis.semantic_clarity < 80:
        suggestions.append({
            "id": "fallback_1",
            "type": "clarity",
            "priority": 1,
            "impact": "high",
            "title": "提升语义清晰度",
            "description": "使用更具体和明确的词汇来提高语义清晰度",
            "improvement_plan": "将模糊的词汇如'一些'、'可能'替换为更精确的表达",
            "expected_improvement": {"semantic_clarity": 15, "overall_score": 8},
            "examples": ["模糊：'写一些内容' → 清晰：'写3个要点，每个100字'"],
            "reasoning": "语义清晰度低会导致AI理解偏差",
            "confidence": 0.8
        })

    if analysis.structural_integrity < 75:
        suggestions.append({
            "id": "fallback_2",
            "type": "structure",
            "priority": 2,
            "impact": "medium",
            "title": "优化结构组织",
            "description": "改进提示词的结构组织，使逻辑更清晰",
            "improvement_plan": "使用编号列表或分段来组织不同的指令要求",
            "expected_improvement": {"structural_integrity": 20, "overall_score": 10},
            "examples": ["使用：1. 背景 2. 任务 3. 要求 4. 输出格式"],
            "reasoning": "良好的结构有助于AI理解任务层次",
            "confidence": 0.75
        })

    if analysis.logical_coherence < 85:
        suggestions.append({
            "id": "fallback_3",
            "type": "coherence",
            "priority": 1,
            "impact": "high",
            "title": "增强逻辑连贯性",
            "description": "增强指令之间的逻辑连贯性",
            "improvement_plan": "添加过渡词和连接词来改善指令流程",
            "expected_improvement": {"logical_coherence": 15, "overall_score": 8},
            "examples": ["使用连接词：'首先...然后...最后...'"],
            "reasoning": "逻辑连贯性影响AI对任务的整体理解",
            "confidence": 0.7
        })

    return {
        "suggestions": suggestions[:3],
        "personalized_recommendations": [
            "建议根据您的使用场景调整提示词风格",
            "考虑添加更多具体示例来说明期望输出"
        ],
        "improvement_roadmap": [
            "🎯 立即执行：修复关键问题",
            "📈 短期优化：完善结构和格式",
            "🔧 长期完善：添加高级特性"
        ],
        "estimated_score_improvement": 15,
        "processing_time": 0.1,
        "model_used": "rule-based"
    }

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
    
    # 获取用户偏好设置
    user_preferences = {}
    preference = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    if preference:
        user_preferences = {
            "preferred_ai_model": preference.preferred_ai_model,
            "analysis_depth": preference.analysis_depth,
            "use_case": request.get("scenario", "通用")
        }

    # 检查是否已有建议
    existing_suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.analysis_id == analysis_id
    ).all()

    if existing_suggestions and not request.get("regenerate", False):
        return {
            "suggestions": [s.to_dict() for s in existing_suggestions],
            "message": "返回已有的优化建议",
            "regenerate_available": True
        }

    # 生成新建议
    model = request.get("ai_model", user_preferences.get("preferred_ai_model", "gpt-3.5-turbo"))
    suggestions_result = await generate_intelligent_suggestions(analysis, user_preferences, model)
    
    # 清除旧建议（如果重新生成）
    if request.get("regenerate", False):
        db.query(OptimizationSuggestion).filter(
            OptimizationSuggestion.analysis_id == analysis_id
        ).delete()

    # 保存新建议到数据库
    created_suggestions = []
    for sugg_data in suggestions_result["suggestions"]:
        suggestion = OptimizationSuggestion(
            analysis_id=analysis_id,
            suggestion_type=sugg_data["type"],
            priority=sugg_data["priority"],
            description=sugg_data["description"],
            improvement_plan=sugg_data["improvement_plan"],
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
        "personalized_recommendations": suggestions_result.get("personalized_recommendations", []),
        "improvement_roadmap": suggestions_result.get("improvement_roadmap", []),
        "estimated_score_improvement": suggestions_result.get("estimated_score_improvement", 0),
        "processing_time": suggestions_result.get("processing_time", 0),
        "model_used": suggestions_result.get("model_used", "unknown"),
        "message": "成功生成智能优化建议"
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

@router.post("/apply-suggestions")
async def apply_multiple_suggestions(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量应用优化建议"""
    suggestion_ids = request.get("suggestion_ids", [])
    original_prompt = request.get("original_prompt", "")

    if not suggestion_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要应用的建议"
        )

    # 验证建议存在且属于当前用户
    suggestions = []
    for suggestion_id in suggestion_ids:
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
                detail=f"优化建议 {suggestion_id} 不存在"
            )
        suggestions.append(suggestion)

    # 生成优化后的提示词
    try:
        ai_client = get_ai_client()

        # 构建优化指令
        optimization_instructions = []
        for sugg in suggestions:
            optimization_instructions.append(f"- {sugg.description}: {sugg.improvement_plan}")

        optimization_prompt = f"""请根据以下优化建议改进这个提示词：

原始提示词：
{original_prompt}

优化建议：
{chr(10).join(optimization_instructions)}

请返回优化后的提示词，保持原意的同时应用这些改进建议。只返回优化后的提示词内容，不要添加额外说明。"""

        if ai_client.get_available_models():
            response = await ai_client.generate_completion(
                prompt=optimization_prompt,
                model="gpt-3.5-turbo",
                temperature=0.3
            )
            optimized_prompt = response.content.strip()
        else:
            optimized_prompt = original_prompt + "\n\n[建议：请手动应用优化建议]"

        # 标记建议为已应用
        for suggestion in suggestions:
            suggestion.is_applied = True

        db.commit()

        return {
            "optimized_prompt": optimized_prompt,
            "applied_suggestions": [s.to_dict() for s in suggestions],
            "message": f"成功应用 {len(suggestions)} 个优化建议"
        }

    except Exception as e:
        return {
            "optimized_prompt": original_prompt,
            "applied_suggestions": [],
            "error": str(e),
            "message": "自动优化失败，请手动应用建议"
        }

@router.get("/effectiveness/{analysis_id}")
async def get_optimization_effectiveness(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取优化效果统计"""
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

    # 获取相关建议
    suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.analysis_id == analysis_id
    ).all()

    # 统计应用情况
    total_suggestions = len(suggestions)
    applied_suggestions = len([s for s in suggestions if s.is_applied])

    # 按类型统计
    type_stats = {}
    for suggestion in suggestions:
        suggestion_type = suggestion.suggestion_type
        if suggestion_type not in type_stats:
            type_stats[suggestion_type] = {"total": 0, "applied": 0}
        type_stats[suggestion_type]["total"] += 1
        if suggestion.is_applied:
            type_stats[suggestion_type]["applied"] += 1

    # 按优先级统计
    priority_stats = {}
    for suggestion in suggestions:
        priority = suggestion.priority
        if priority not in priority_stats:
            priority_stats[priority] = {"total": 0, "applied": 0}
        priority_stats[priority]["total"] += 1
        if suggestion.is_applied:
            priority_stats[priority]["applied"] += 1

    return {
        "analysis_id": str(analysis_id),
        "original_score": analysis.overall_score,
        "total_suggestions": total_suggestions,
        "applied_suggestions": applied_suggestions,
        "application_rate": round(applied_suggestions / max(total_suggestions, 1) * 100, 1),
        "type_statistics": type_stats,
        "priority_statistics": priority_stats,
        "suggestions_detail": [s.to_dict() for s in suggestions]
    }

@router.get("/user-stats")
async def get_user_optimization_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的优化统计信息"""
    # 获取用户的所有分析结果
    user_analyses = db.query(AnalysisResult).join(
        AnalysisResult.prompt
    ).filter(
        AnalysisResult.prompt.has(user_id=current_user.id)
    ).all()

    # 获取所有相关的优化建议
    analysis_ids = [a.id for a in user_analyses]
    all_suggestions = db.query(OptimizationSuggestion).filter(
        OptimizationSuggestion.analysis_id.in_(analysis_ids)
    ).all()

    # 统计数据
    total_analyses = len(user_analyses)
    total_suggestions = len(all_suggestions)
    applied_suggestions = len([s for s in all_suggestions if s.is_applied])

    # 平均分数
    avg_score = np.mean([a.overall_score for a in user_analyses]) if user_analyses else 0

    # 最常见的建议类型
    type_counts = {}
    for suggestion in all_suggestions:
        suggestion_type = suggestion.suggestion_type
        type_counts[suggestion_type] = type_counts.get(suggestion_type, 0) + 1

    most_common_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None

    # 改进趋势（简化版）
    recent_analyses = sorted(user_analyses, key=lambda x: x.created_at)[-10:]
    improvement_trend = "stable"
    if len(recent_analyses) >= 2:
        recent_avg = np.mean([a.overall_score for a in recent_analyses[-5:]])
        earlier_avg = np.mean([a.overall_score for a in recent_analyses[:5]])
        if recent_avg > earlier_avg + 5:
            improvement_trend = "improving"
        elif recent_avg < earlier_avg - 5:
            improvement_trend = "declining"

    return {
        "user_id": str(current_user.id),
        "total_analyses": total_analyses,
        "total_suggestions": total_suggestions,
        "applied_suggestions": applied_suggestions,
        "application_rate": round(applied_suggestions / max(total_suggestions, 1) * 100, 1),
        "average_score": round(avg_score, 1),
        "most_common_suggestion_type": most_common_type,
        "improvement_trend": improvement_trend,
        "type_distribution": type_counts
    }
