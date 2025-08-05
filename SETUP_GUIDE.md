# 🚀 Enhance Prompt Engineer 部署指南

## 📋 系统要求

### 必需软件
- **Python 3.8+** - 后端运行环境
- **Node.js 16+** - 前端构建和运行
- **Git** - 代码版本控制

### 可选软件
- **PostgreSQL** - 生产环境数据库（开发环境可使用SQLite）
- **Redis** - 缓存服务（可选）

## 🛠️ 快速开始

### 方法一：演示版本（无需安装依赖）

1. **直接查看演示界面**
   ```bash
   # 在浏览器中打开
   file:///path/to/Enhance_Prompt_Engineer/demo/index.html
   ```

2. **或者使用VS Code Live Server**
   - 在VS Code中安装 "Live Server" 扩展
   - 右键点击 `demo/index.html`
   - 选择 "Open with Live Server"

### 方法二：完整开发环境

#### 1. 安装Python依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
# 复制环境配置文件
cp .env.dev .env

# 编辑配置文件（可选）
# 默认使用SQLite数据库，无需额外配置
```

#### 3. 启动后端服务

```bash
# 在backend目录下
python main.py
```

后端服务将在 `http://localhost:8000` 启动

#### 4. 安装前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用yarn
yarn install
```

#### 5. 启动前端开发服务器

```bash
# 在frontend目录下
npm run dev
# 或使用yarn
yarn dev
```

前端服务将在 `http://localhost:3000` 启动

## 🌐 访问应用

### 演示版本
- **前端界面**: 打开 `demo/index.html` 文件
- **功能**: 基本的UI演示和模拟分析功能

### 完整版本
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📁 项目结构

```
Enhance_Prompt_Engineer/
├── backend/                 # 后端代码
│   ├── app/                # FastAPI应用
│   ├── config/             # 配置文件
│   ├── tests/              # 测试代码
│   ├── main.py             # 主程序入口
│   ├── requirements.txt    # Python依赖
│   └── .env.dev           # 开发环境配置
├── frontend/               # 前端代码
│   ├── src/               # React源代码
│   ├── public/            # 静态资源
│   ├── package.json       # Node.js依赖
│   └── vite.config.ts     # Vite配置
├── demo/                  # 演示版本
│   └── index.html         # 静态演示页面
├── docs/                  # 文档
└── README.md              # 项目说明
```

## 🔧 开发工具配置

### VS Code 推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ritwickdey.liveserver"
  ]
}
```

### VS Code 工作区设置

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 🐛 常见问题

### 1. Python模块导入错误
```bash
# 确保在正确的目录下运行
cd backend
python main.py
```

### 2. 端口被占用
```bash
# 检查端口使用情况
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 或者修改端口配置
# 后端: 修改 main.py 中的 port 参数
# 前端: 修改 vite.config.ts 中的 server.port
```

### 3. 数据库连接失败
- 检查 `.env` 文件中的数据库配置
- 确保数据库服务正在运行
- 开发环境可以使用默认的SQLite配置

### 4. 前端构建失败
```bash
# 清理缓存
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## 🚀 生产环境部署

### 1. 环境配置
- 使用PostgreSQL数据库
- 配置Redis缓存
- 设置环境变量
- 配置HTTPS

### 2. 构建前端
```bash
cd frontend
npm run build
```

### 3. 部署后端
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. 使用Docker（可选）
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 📞 技术支持

如果遇到问题，请检查：
1. 系统要求是否满足
2. 依赖是否正确安装
3. 端口是否被占用
4. 环境变量是否正确配置

更多帮助请参考项目文档或提交Issue。
