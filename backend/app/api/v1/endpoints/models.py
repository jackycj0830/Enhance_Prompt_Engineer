"""
AI模型管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.services.ai_client import get_ai_client
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/available")
async def get_available_models(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """获取可用的AI模型列表"""
    ai_client = get_ai_client()
    available_models = ai_client.get_available_models()
    
    # 获取模型详细信息
    model_details = {}
    
    for provider, models in ai_client.supported_models.items():
        for model_name, config in models.items():
            if model_name in available_models:
                model_details[model_name] = {
                    "provider": provider,
                    "max_tokens": config["max_tokens"],
                    "cost_per_1k_tokens": config["cost_per_1k"],
                    "available": True
                }
    
    # 添加不可用的模型信息
    for provider, models in ai_client.supported_models.items():
        for model_name, config in models.items():
            if model_name not in available_models:
                model_details[model_name] = {
                    "provider": provider,
                    "max_tokens": config["max_tokens"],
                    "cost_per_1k_tokens": config["cost_per_1k"],
                    "available": False,
                    "reason": f"{provider.upper()} API key not configured"
                }
    
    return {
        "available_models": available_models,
        "model_details": model_details,
        "total_available": len(available_models),
        "configuration_status": {
            "openai_configured": ai_client.openai_client is not None,
            "anthropic_configured": ai_client.anthropic_client is not None
        }
    }

@router.get("/test/{model_name}")
async def test_model(
    model_name: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """测试特定AI模型的连接和响应"""
    ai_client = get_ai_client()
    
    if model_name not in ai_client.get_available_models():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model_name} is not available"
        )
    
    test_prompt = "请简单回复'测试成功'来确认连接正常。"
    
    try:
        response = await ai_client.generate_completion(
            prompt=test_prompt,
            model=model_name,
            temperature=0.1,
            max_tokens=50
        )
        
        return {
            "model": model_name,
            "status": "success",
            "response": response.content,
            "response_time": response.response_time,
            "token_usage": response.usage,
            "finish_reason": response.finish_reason
        }
    
    except Exception as e:
        return {
            "model": model_name,
            "status": "error",
            "error": str(e),
            "response_time": 0
        }

@router.post("/analyze-cost")
async def analyze_cost(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """分析使用不同模型的成本估算"""
    text = request.get("text", "")
    models = request.get("models", [])
    
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is required for cost analysis"
        )
    
    ai_client = get_ai_client()
    cost_analysis = {}
    
    for model in models:
        if model in ai_client.supported_models.get("openai", {}) or model in ai_client.supported_models.get("anthropic", {}):
            # 计算token数量
            token_count = ai_client.count_tokens(text, model)
            
            # 获取成本信息
            cost_per_1k = 0
            provider = ""
            
            if model in ai_client.supported_models.get("openai", {}):
                cost_per_1k = ai_client.supported_models["openai"][model]["cost_per_1k"]
                provider = "openai"
            elif model in ai_client.supported_models.get("anthropic", {}):
                cost_per_1k = ai_client.supported_models["anthropic"][model]["cost_per_1k"]
                provider = "anthropic"
            
            # 估算成本（输入 + 预估输出）
            estimated_output_tokens = min(token_count, 500)  # 假设输出不超过500 tokens
            total_tokens = token_count + estimated_output_tokens
            estimated_cost = (total_tokens / 1000) * cost_per_1k
            
            cost_analysis[model] = {
                "provider": provider,
                "input_tokens": token_count,
                "estimated_output_tokens": estimated_output_tokens,
                "total_tokens": total_tokens,
                "cost_per_1k_tokens": cost_per_1k,
                "estimated_cost_usd": round(estimated_cost, 6),
                "available": model in ai_client.get_available_models()
            }
    
    return {
        "text_length": len(text),
        "cost_analysis": cost_analysis,
        "recommendations": _get_cost_recommendations(cost_analysis)
    }

def _get_cost_recommendations(cost_analysis: Dict[str, Any]) -> List[str]:
    """生成成本优化建议"""
    recommendations = []
    
    if not cost_analysis:
        return ["No models analyzed"]
    
    # 找到最便宜的可用模型
    available_models = {k: v for k, v in cost_analysis.items() if v["available"]}
    
    if available_models:
        cheapest = min(available_models.items(), key=lambda x: x[1]["estimated_cost_usd"])
        most_expensive = max(available_models.items(), key=lambda x: x[1]["estimated_cost_usd"])
        
        if cheapest[1]["estimated_cost_usd"] < most_expensive[1]["estimated_cost_usd"]:
            savings = most_expensive[1]["estimated_cost_usd"] - cheapest[1]["estimated_cost_usd"]
            recommendations.append(
                f"使用 {cheapest[0]} 替代 {most_expensive[0]} 可节省约 ${savings:.6f} USD"
            )
        
        # 基于成本给出建议
        if cheapest[1]["estimated_cost_usd"] < 0.001:
            recommendations.append("当前分析成本很低，可以频繁使用")
        elif cheapest[1]["estimated_cost_usd"] > 0.01:
            recommendations.append("建议优化提示词长度以降低成本")
    
    return recommendations

@router.get("/usage-stats")
async def get_usage_stats(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """获取用户的AI模型使用统计"""
    # 这里可以从数据库查询用户的使用历史
    # 目前返回模拟数据
    return {
        "total_analyses": 0,
        "models_used": {},
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "most_used_model": None,
        "average_response_time": 0.0
    }
