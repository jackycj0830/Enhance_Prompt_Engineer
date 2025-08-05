#!/bin/bash

# Enhance Prompt Engineer 开发环境设置脚本

set -e

echo "🚀 开始设置 Enhance Prompt Engineer 开发环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  警告: 端口 $port ($service) 已被占用"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

echo "🔍 检查端口占用情况..."
check_port 3000 "前端服务"
check_port 8000 "后端服务"
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 5050 "pgAdmin"
check_port 8081 "Redis Commander"

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p uploads
mkdir -p backend/logs
mkdir -p backend/uploads

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 停止可能运行的容器
echo "🛑 停止现有容器..."
docker-compose -f docker/docker-compose.dev.yml down --remove-orphans

# 构建并启动服务
echo "🏗️  构建并启动开发环境..."
docker-compose -f docker/docker-compose.dev.yml up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker/docker-compose.dev.yml ps

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
timeout 60 bash -c 'until docker exec enhance_prompt_postgres pg_isready -U postgres; do sleep 2; done'

echo ""
echo "🎉 开发环境设置完成！"
echo ""
echo "📋 服务访问地址:"
echo "   前端应用:        http://localhost:3000"
echo "   后端API:         http://localhost:8000"
echo "   API文档:         http://localhost:8000/docs"
echo "   pgAdmin:         http://localhost:5050"
echo "   Redis Commander: http://localhost:8081"
echo ""
echo "🔑 默认登录信息:"
echo "   pgAdmin:    admin@enhanceprompt.com / admin123"
echo "   数据库:     postgres / postgres123"
echo ""
echo "📝 常用命令:"
echo "   查看日志:   docker-compose -f docker/docker-compose.dev.yml logs -f [service]"
echo "   停止服务:   docker-compose -f docker/docker-compose.dev.yml down"
echo "   重启服务:   docker-compose -f docker/docker-compose.dev.yml restart [service]"
echo ""
echo "🚀 开始开发吧！"
