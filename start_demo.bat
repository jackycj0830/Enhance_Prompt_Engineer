@echo off
echo ========================================
echo   Enhance Prompt Engineer - Demo
echo ========================================
echo.

echo 正在启动演示页面...
echo.

REM 检查是否安装了Chrome
where chrome >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 使用Chrome浏览器打开演示页面...
    start chrome "%~dp0demo\index.html"
    goto :end
)

REM 检查是否安装了Edge
where msedge >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo 使用Edge浏览器打开演示页面...
    start msedge "%~dp0demo\index.html"
    goto :end
)

REM 使用默认浏览器
echo 使用默认浏览器打开演示页面...
start "" "%~dp0demo\index.html"

:end
echo.
echo ========================================
echo 演示页面已启动！
echo.
echo 功能特性：
echo - 智能提示词分析
echo - 实时评分系统
echo - 优化建议生成
echo - 响应式界面设计
echo.
echo 如需完整功能，请参考 SETUP_GUIDE.md
echo 安装Python和Node.js环境
echo ========================================
echo.
pause
