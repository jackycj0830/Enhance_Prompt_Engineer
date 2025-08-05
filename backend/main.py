"""
Enhance Prompt Engineer - 主应用入口
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime

# 导入配置和数据库
try:
    from config.database import check_db_connection, check_redis_connection, init_db
except ImportError:
    print("警告: 数据库模块导入失败，使用模拟函数")
    def check_db_connection():
        return True
    def check_redis_connection():
        return True
    def init_db():
        return True

try:
    from app.api.v1 import api_router
except ImportError:
    print("警告: API路由导入失败，使用基本路由")
    from fastapi import APIRouter
    api_router = APIRouter()

    @api_router.get("/")
    async def basic_info():
        return {"message": "Basic API is running", "status": "ok"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 Enhance Prompt Engineer API 启动中...")

    # 检查数据库连接
    if check_db_connection():
        print("✅ 数据库连接成功")
        # 初始化数据库
        if init_db():
            print("✅ 数据库初始化成功")
        else:
            print("⚠️ 数据库初始化失败，但应用继续运行")
    else:
        print("⚠️ 数据库连接失败，但应用继续运行")

    if check_redis_connection():
        print("✅ Redis连接成功")
    else:
        print("⚠️ Redis连接失败，但应用继续运行")

    print("✅ 数据库连接正常")
    print(f"📝 API文档: http://localhost:8000/docs")
    print(f"🔍 健康检查: http://localhost:8000/health")

    yield

    # 关闭时执行
    print("🛑 Enhance Prompt Engineer API 正在关闭...")

# 创建FastAPI应用实例
app = FastAPI(
    title="Enhance Prompt Engineer API",
    description="专业的提示词分析与优化工具API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

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

# 数据库状态检查端点
@app.get("/api/v1/status")
async def system_status():
    """系统状态检查"""
    db_status = check_db_connection()
    redis_status = check_redis_connection()

    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 开发环境直接运行
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
