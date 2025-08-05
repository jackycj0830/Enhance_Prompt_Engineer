# Enhance Prompt Engineer

一款专业的提示词分析与优化工具，帮助AI开发者、内容创作者和企业用户提升提示词质量和AI输出效果。

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd Enhance_Prompt_Engineer
```

2. 后端环境设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 前端环境设置
```bash
cd frontend
npm install
```

4. 数据库设置
```bash
# 创建数据库
createdb enhance_prompt_engineer
# 运行迁移
cd backend && python manage.py migrate
```

5. 启动服务
```bash
# 后端服务
cd backend && python main.py

# 前端服务
cd frontend && npm run dev
```

## 📁 项目结构

```
Enhance_Prompt_Engineer/
├── docs/                    # 项目文档
├── specs/                   # 功能规格文档
├── backend/                 # 后端代码
├── frontend/               # 前端代码
├── scripts/               # 自动化脚本
├── docker/               # Docker配置
└── README.md             # 项目说明
```

## 🛠 开发指南

### 代码规范
- Python: 遵循PEP 8标准，使用Black格式化
- JavaScript/TypeScript: 使用ESLint + Prettier
- 提交信息: 遵循Conventional Commits规范

### 测试
```bash
# 后端测试
cd backend && pytest

# 前端测试
cd frontend && npm test
```

## 📖 文档

- [项目概览](./PROJECT_OVERVIEW.md)
- [需求文档](./docs/requirements.md)
- [设计文档](./docs/design.md)
- [任务分解](./docs/tasks.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- 项目负责人: AI开发团队
- 邮箱: team@enhanceprompt.com
- 项目链接: [GitHub Repository](https://github.com/your-org/enhance-prompt-engineer)
