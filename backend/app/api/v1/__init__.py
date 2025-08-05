"""
API v1 路由
"""

from fastapi import APIRouter
from .endpoints import auth, users, prompts, analysis, optimization, templates

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["提示词管理"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["提示词分析"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["优化建议"])
api_router.include_router(templates.router, prefix="/templates", tags=["模板管理"])

@api_router.get("/")
async def api_v1_info():
    """API v1 信息"""
    return {
        "version": "v1",
        "title": "Enhance Prompt Engineer API",
        "description": "专业的提示词分析与优化工具API",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "prompts": "/api/v1/prompts",
            "analysis": "/api/v1/analysis", 
            "optimization": "/api/v1/optimization",
            "templates": "/api/v1/templates"
        }
    }
