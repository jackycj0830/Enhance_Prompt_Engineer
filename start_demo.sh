#!/bin/bash

echo "========================================"
echo "   Enhance Prompt Engineer - Demo"
echo "========================================"
echo

echo "正在启动演示页面..."
echo

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_FILE="$SCRIPT_DIR/demo/index.html"

# 检查操作系统并使用相应的命令打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "在macOS上使用默认浏览器打开演示页面..."
    open "$DEMO_FILE"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "在Linux上使用默认浏览器打开演示页面..."
    xdg-open "$DEMO_FILE"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash/Cygwin)
    echo "在Windows上使用默认浏览器打开演示页面..."
    start "$DEMO_FILE"
else
    echo "未知操作系统，请手动打开: $DEMO_FILE"
fi

echo
echo "========================================"
echo "演示页面已启动！"
echo
echo "功能特性："
echo "- 智能提示词分析"
echo "- 实时评分系统"
echo "- 优化建议生成"
echo "- 响应式界面设计"
echo
echo "如需完整功能，请参考 SETUP_GUIDE.md"
echo "安装Python和Node.js环境"
echo "========================================"
echo

read -p "按Enter键退出..."
