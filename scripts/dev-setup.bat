@echo off
REM Enhance Prompt Engineer 开发环境设置脚本 (Windows)

echo 🚀 开始设置 Enhance Prompt Engineer 开发环境...

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose 未安装，请先安装 Docker Compose
    pause
    exit /b 1
)

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist backend\logs mkdir backend\logs
if not exist backend\uploads mkdir backend\uploads

REM 复制环境变量文件
if not exist .env (
    echo 📝 创建环境变量文件...
    copy .env.example .env
    echo ✅ 已创建 .env 文件，请根据需要修改配置
)

REM 停止可能运行的容器
echo 🛑 停止现有容器...
docker-compose -f docker/docker-compose.dev.yml down --remove-orphans

REM 构建并启动服务
echo 🏗️  构建并启动开发环境...
docker-compose -f docker/docker-compose.dev.yml up --build -d

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker-compose -f docker/docker-compose.dev.yml ps

echo.
echo 🎉 开发环境设置完成！
echo.
echo 📋 服务访问地址:
echo    前端应用:        http://localhost:3000
echo    后端API:         http://localhost:8000
echo    API文档:         http://localhost:8000/docs
echo    pgAdmin:         http://localhost:5050
echo    Redis Commander: http://localhost:8081
echo.
echo 🔑 默认登录信息:
echo    pgAdmin:    admin@enhanceprompt.com / admin123
echo    数据库:     postgres / postgres123
echo.
echo 📝 常用命令:
echo    查看日志:   docker-compose -f docker/docker-compose.dev.yml logs -f [service]
echo    停止服务:   docker-compose -f docker/docker-compose.dev.yml down
echo    重启服务:   docker-compose -f docker/docker-compose.dev.yml restart [service]
echo.
echo 🚀 开始开发吧！
pause
