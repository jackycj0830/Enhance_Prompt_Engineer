"""
Enhance Prompt Engineer - 主应用入口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

# 创建FastAPI应用实例
app = FastAPI(
    title="Enhance Prompt Engineer API",
    description="专业的提示词分析与优化工具API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

# 根路径
@app.get("/")
async def root():
    """根路径 - API状态检查"""
    return {
        "message": "Enhance Prompt Engineer API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "enhance-prompt-engineer-api"
    }

# API版本路由组
@app.get("/api/v1")
async def api_v1_info():
    """API v1 信息"""
    return {
        "version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "analysis": "/api/v1/analysis", 
            "optimization": "/api/v1/optimization",
            "templates": "/api/v1/templates",
            "users": "/api/v1/users"
        }
    }

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("🚀 Enhance Prompt Engineer API 启动中...")
    print(f"📝 API文档: http://localhost:8000/docs")
    print(f"🔍 健康检查: http://localhost:8000/health")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("🛑 Enhance Prompt Engineer API 正在关闭...")

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
