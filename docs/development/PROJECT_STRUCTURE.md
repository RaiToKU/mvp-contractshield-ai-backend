# ContractShield AI Backend - 项目结构

本文档描述了 ContractShield AI 后端项目的整体结构和各个组件的功能。

## 项目概览

ContractShield AI 是一个基于 FastAPI 的智能合同审查系统，使用 AI 技术来分析和审查法律合同文档。

## 目录结构概览

```
contractshield-ai-backend/
├── app/                     # 核心应用代码
├── database/                # 数据库相关文件
├── deployment/              # 部署和运维文件
├── docs/                    # 项目文档
├── tests/                   # 测试文件
├── temp/                    # 临时文件（开发用）
├── .github/                 # GitHub 配置
├── uploads/                 # 上传文件目录（运行时创建）
├── exports/                 # 导出文件目录（运行时创建）
└── 配置和文档文件
```

## 详细说明

### 📁 app/ - 核心应用代码

包含 FastAPI 应用的所有核心代码：

- `main.py` - FastAPI 应用主文件，包含应用初始化、中间件配置、路由注册
- `database.py` - 数据库连接和会话管理
- `models.py` - SQLAlchemy 数据模型定义
- `websocket_manager.py` - WebSocket 连接管理器
- `routes/` - API 路由模块
  - `upload.py` - 文件上传相关路由
  - `review.py` - 合同审查相关路由
  - `export.py` - 报告导出相关路由
  - `websocket.py` - WebSocket 路由
- `services/` - 业务逻辑服务
  - `file_service.py` - 文件处理服务
  - `ai_service.py` - AI 服务集成
  - `review_service.py` - 合同审查服务
  - `export_service.py` - 报告导出服务

### 📁 database/ - 数据库相关文件

包含所有数据库相关的配置和脚本：

- `alembic/` - Alembic 数据库迁移文件
  - `versions/` - 迁移版本文件
  - `env.py` - Alembic 环境配置
  - `script.py.mako` - 迁移脚本模板
- `alembic.ini` - Alembic 配置文件
- `init_db.py` - 数据库初始化脚本
- `update_db.py` - 数据库更新脚本
- `init.sql` - 初始化 SQL 脚本

**使用说明：**
```bash
# 进入数据库目录执行迁移
cd database
alembic upgrade head
cd ..
```

### 📁 deployment/ - 部署和运维文件

包含部署、配置和运行相关的脚本：

- `deploy.sh` - 部署脚本
- `docker-compose.yml` - Docker 编排配置
- `Dockerfile` - Docker 镜像构建文件
- `nginx.conf` - Nginx 反向代理配置

**使用说明：**
```bash
# Docker 部署
docker-compose -f deployment/docker-compose.yml up -d

# 使用 Nginx 配置
sudo cp deployment/nginx.conf /etc/nginx/sites-available/contractshield
```

### 📁 docs/ - 项目文档

包含所有项目相关的文档：

- `API_Documentation.md` - API 接口文档
- `Frontend_Integration_Guide.md` - 前端集成指南
- `PROJECT_STRUCTURE.md` - 项目结构说明（本文档）
- `WebSocket_Guide.md` - WebSocket 使用指南

### 📁 tests/ - 测试文件

包含所有测试相关的文件：

- `test_*.py` - 单元测试和集成测试
  - `test_api.py` - API 测试
  - `test_services.py` - 服务层测试
  - `test_api_endpoints.py` - API 端点测试
  - `test_implementation.py` - 实现测试
  - `test_websocket.py` - WebSocket 测试
- `simple_*.py` - 简单测试脚本
  - `simple_api_test.py` - 简单 API 测试
  - `simple_websocket_test.py` - 简单 WebSocket 测试
- `websocket_test.html` - WebSocket 浏览器测试页面
- `create_test_pdf.py` - 测试 PDF 生成工具
- `run_tests.py` - 测试运行脚本
- `conftest.py` - pytest 配置文件
- `README.md` - 测试文档

### 📁 temp/ - 临时文件（开发用）

包含开发过程中的临时文件：

- `check_task_33.py` - 临时测试脚本
- `get_task_33_info.py` - 临时信息获取脚本
- `test_contract.txt` - 测试合同文本
- `test_contract_copy.pdf` - 测试合同PDF

### 📁 .github/ - GitHub 配置

包含 GitHub 相关的配置文件：

- `workflows/` - GitHub Actions 工作流配置

**使用说明：**
```bash
# 运行所有测试
pytest tests/

# 运行特定测试
python tests/simple_api_test.py

# 在浏览器中测试 WebSocket
open tests/websocket_test.html
```

### 📄 根目录文件

- `run.py` - 应用启动脚本
- `requirements.txt` - Python 依赖列表
- `pytest.ini` - pytest 配置
- `.env.example` - 环境变量示例
- `.gitignore` - Git 忽略文件配置
- `README.md` - 项目主文档
- `docker-compose.prod.yml` - 生产环境 Docker Compose 配置

### 📁 运行时目录

这些目录在应用运行时自动创建：

- `uploads/` - 用户上传的文件存储
- `exports/` - 生成的报告文件存储

## 目录组织原则

1. **功能分离**：按功能将文件分组到不同目录
2. **环境隔离**：开发、测试、部署相关文件分别存放
3. **易于维护**：相关文件集中管理，便于查找和修改
4. **标准化**：遵循 Python 项目的标准目录结构

## 开发工作流

1. **开发新功能**：在 `app/` 目录下添加代码
2. **编写测试**：在 `tests/` 目录下添加测试文件
3. **数据库变更**：在 `database/` 目录下管理迁移
4. **部署配置**：在 `deployment/` 目录下修改配置
5. **文档更新**：在 `docs/` 目录下维护文档

## 注意事项

- 数据库迁移需要在 `database/` 目录下执行
- 测试文件统一放在 `tests/` 目录下
- 部署相关配置集中在 `deployment/` 目录
- 核心业务逻辑保持在 `app/` 目录下
- 项目文档集中在 `docs/` 目录下
- 临时开发文件放在 `temp/` 目录下

这种目录结构使项目更加清晰、易于维护和扩展。