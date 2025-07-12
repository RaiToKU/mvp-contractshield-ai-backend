# ContractShield AI Backend

合同审查AI后端服务 - 基于FastAPI的智能合同风险分析系统

## 功能特性

- 📄 **多格式文件支持**: PDF、DOCX、图片等格式的合同文件上传
- 🔍 **智能文本提取**: OCR技术提取合同文本内容
- 🤖 **AI风险分析**: 基于OpenRouter API的智能风险识别
- 🎯 **角色识别**: 自动识别合同主体和用户角色
- 📊 **实时进度**: WebSocket实时推送审查进度
- 📋 **报告导出**: 支持PDF、DOCX、TXT格式的审查报告
- 🔍 **向量检索**: 基于PGVector的语义相似度搜索

## 技术栈

- **Web框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + PGVector
- **ORM**: SQLAlchemy
- **AI服务**: OpenRouter API
- **文档处理**: pytesseract, pdf2docx, python-docx
- **实时通信**: WebSocket
- **数据库迁移**: Alembic

## 🚀 快速部署 (推荐)

### Docker 部署

1. **构建和推送镜像**
```bash
# 给脚本执行权限
chmod +x deployment/push_image.sh

# 构建并推送镜像
cd deployment
./push_image.sh
cd ..
```

2. **在目标服务器部署**
```bash
# 复制配置文件
cp .env.example .env
nano .env  # 配置数据库连接和 API 密钥

# 执行部署
chmod +x deployment/deploy.sh
cd deployment
./deploy.sh
cd ..
```

3. **验证部署**
```bash
# 健康检查
curl http://localhost:8000/health

# 查看容器状态
docker ps
```

详细部署指南请参考：[Docker 部署指南](docs/DOCKER_DEPLOYMENT_GUIDE.md)

## 🛠️ 本地开发

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+ (带 PGVector 扩展)
- Tesseract OCR

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd mvp-contractshield-ai-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 3. 环境配置

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和 API 密钥
```

### 4. 数据库设置

#### 方式一：使用数据库管理脚本（推荐）
```bash
# 给脚本执行权限
chmod +x db-manager.sh

# 显示数据库连接信息
./db-manager.sh info

# 启动数据库容器（如果未启动）
cd deployment && docker-compose up -d postgres && cd ..

# 初始化数据库
./db-manager.sh init

# 验证初始化
./db-manager.sh status
```

#### 方式二：手动设置
```bash
# 创建数据库
sudo -u postgres createdb contractshield

# 启用PGVector扩展
sudo -u postgres psql contractshield -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 执行数据库迁移
cd database
alembic upgrade head
cd ..
```

#### 数据库管理账号
- **数据库名**: contractshield
- **用户名**: contractshield
- **密码**: contractshield123
- **端口**: 5432

详细说明请参考：[数据库初始化指南](docs/deployment/DATABASE_INIT_GUIDE.md)

### 5. 启动服务

```bash
python run.py
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📚 文档

### 📖 [完整文档索引](docs/README.md)

#### 🚀 部署文档
- [Docker Compose 指南](docs/deployment/DOCKER_COMPOSE_GUIDE.md) - **推荐的部署方式**
- [简单部署指南](docs/deployment/DEPLOY_SIMPLE.md) - 快速部署说明
- [Docker 部署指南](docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md) - 详细的 Docker 部署文档
- [环境变量配置](docs/deployment/ENV_CONFIG_GUIDE.md) - 环境变量详细配置说明
- [Docker 构建优化](docs/deployment/DOCKER_BUILD_OPTIMIZATION.md) - Docker 镜像构建优化指南

#### 🔌 API 文档
- [API 文档](docs/api/API_Documentation.md) - 完整的 REST API 接口文档
- [WebSocket 指南](docs/api/WebSocket_Guide.md) - WebSocket 实时通信接口文档

#### 💻 开发文档
- [项目结构](docs/development/PROJECT_STRUCTURE.md) - 项目架构和代码结构说明
- [前端集成指南](docs/development/Frontend_Integration_Guide.md) - 前端对接指南

#### 🔧 故障排除
- [OpenCV 修复指南](docs/troubleshooting/OPENCV_FIX_GUIDE.md) - OpenCV 相关问题解决方案

## 🔧 主要 API 接口

### 文件上传
```bash
POST /api/v1/upload
Content-Type: multipart/form-data
```

### 角色识别
```bash
POST /api/v1/draft_roles
POST /api/v1/confirm_roles
```

### 开始审查
```bash
POST /api/v1/review
```

### 获取结果
```bash
GET /api/v1/review/{task_id}
```

### 导出报告
```bash
GET /api/v1/export/{task_id}?format=pdf
```

### WebSocket 连接
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/review/{task_id}');
```

## 🗂️ 项目结构

```
mvp-contractshield-ai-backend/
├── app/                     # 核心应用代码
│   ├── main.py              # 主应用文件
│   ├── models.py            # 数据模型
│   ├── routes/              # 路由模块
│   └── services/            # 业务服务
├── database/                # 数据库相关
├── deployment/              # 部署配置
├── docs/                    # 文档
├── tests/                   # 测试文件
├── .env.example             # 环境配置模板
├── push_image.sh            # 镜像构建脚本
├── deploy.sh                # 部署脚本
└── requirements.txt         # 依赖列表
```

## 🛠️ 开发

### 数据库迁移
```bash
cd database
alembic upgrade head
cd ..
```

### 运行测试
```bash
cd tests
python run_tests.py
```

## 📞 支持

如有问题，请查看相关文档或联系开发团队。