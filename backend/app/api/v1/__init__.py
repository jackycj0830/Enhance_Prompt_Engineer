"""
API v1 路由
"""

from fastapi import APIRouter

api_router = APIRouter()

# 简化版本，先导入基本路由
try:
    from .endpoints import auth, users, prompts, analysis, optimization, templates, models

    # 包含各个模块的路由
    api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
    api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
    api_router.include_router(prompts.router, prefix="/prompts", tags=["提示词管理"])
    api_router.include_router(analysis.router, prefix="/analysis", tags=["提示词分析"])
    api_router.include_router(optimization.router, prefix="/optimization", tags=["优化建议"])
    api_router.include_router(templates.router, prefix="/templates", tags=["模板管理"])
    api_router.include_router(models.router, prefix="/models", tags=["AI模型管理"])
except ImportError as e:
    print(f"警告: 部分API模块导入失败: {e}")
    # 创建基本的演示路由
    pass

# 添加基本的演示路由
@api_router.get("/demo/prompts")
async def demo_prompts():
    """演示提示词列表"""
    return {
        "prompts": [
            {
                "id": 1,
                "title": "写作助手提示词",
                "content": "你是一个专业的写作助手，请帮助用户改进文章质量...",
                "category": "写作",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "title": "代码审查提示词",
                "content": "请仔细审查以下代码，指出潜在问题和改进建议...",
                "category": "编程",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ]
    }

@api_router.get("/demo/analysis")
async def demo_analysis():
    """演示分析结果"""
    return {
        "analysis": {
            "overall_score": 85.5,
            "semantic_clarity": 90.0,
            "structural_integrity": 82.0,
            "logical_coherence": 84.0,
            "suggestions": [
                "建议增加更具体的示例",
                "可以明确输出格式要求",
                "考虑添加约束条件"
            ]
        }
    }

@api_router.get("/")
async def api_v1_info():
    """API v1 信息"""
    return {
        "version": "v1",
        "title": "Enhance Prompt Engineer API",
        "description": "专业的提示词分析与优化工具API",
        "status": "running",
        "demo_endpoints": {
            "prompts": "/api/v1/demo/prompts",
            "analysis": "/api/v1/demo/analysis"
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "prompts": "/api/v1/prompts",
            "analysis": "/api/v1/analysis",
            "optimization": "/api/v1/optimization",
            "templates": "/api/v1/templates",
            "models": "/api/v1/models"
        }
    }
