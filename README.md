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
- **AI服务**: OpenRouter API (qwen/qwen3-235b-a22b:free)
- **文档处理**: pytesseract, pdf2docx, python-docx
- **实时通信**: WebSocket
- **数据库迁移**: Alembic

## 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+
- Tesseract OCR

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd mvp-contractshield-ai-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置

```bash
# 安装PostgreSQL和PGVector扩展
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb contractshield

# 启用PGVector扩展
sudo -u postgres psql contractshield -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 4. 环境配置

复制并编辑环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/contractshield

# OpenRouter配置
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=50000000

# Tesseract配置
TESSERACT_CMD=/usr/local/bin/tesseract
```

### 5. 数据库迁移

```bash
# 切换到数据库目录
cd database

# 初始化迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head

# 返回项目根目录
cd ..
```

### 6. 启动服务

```bash
# 开发模式
python run.py

# 或使用uvicorn
uvicorn run:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API接口

### 文件上传

```bash
POST /api/v1/upload
Content-Type: multipart/form-data

# 参数:
# file: 合同文件
# contract_type: 合同类型
```

### 角色识别

```bash
POST /api/v1/draft_roles
Content-Type: application/json

{
  "task_id": 1
}
```

### 确认角色

```bash
POST /api/v1/confirm_roles
Content-Type: application/json

{
  "task_id": 1,
  "role": "buyer",
  "party_names": ["ABC公司"]
}
```

### 开始审查

```bash
POST /api/v1/review
Content-Type: application/json

{
  "task_id": 1
}
```

### 获取结果

```bash
GET /api/v1/review/{task_id}
```

### 导出报告

```bash
GET /api/v1/export/{task_id}?format=pdf
```

### WebSocket连接

```javascript
// 连接审查进度推送
const ws = new WebSocket('ws://localhost:8000/ws/review/{task_id}');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Progress:', data);
};
```

## 项目结构

```
mvp-contractshield-ai-backend/
├── app/                     # 核心应用代码
│   ├── __init__.py
│   ├── main.py              # 主应用文件
│   ├── database.py          # 数据库配置
│   ├── models.py            # 数据模型
│   ├── websocket_manager.py # WebSocket管理
│   ├── routes/              # 路由模块
│   │   ├── upload.py        # 文件上传
│   │   ├── review.py        # 审查相关
│   │   ├── export.py        # 报告导出
│   │   └── websocket.py     # WebSocket路由
│   └── services/            # 业务服务
│       ├── file_service.py  # 文件处理
│       ├── ai_service.py    # AI服务
│       ├── review_service.py # 审查服务
│       └── export_service.py # 导出服务
├── database/                # 数据库相关文件
│   ├── alembic/             # 数据库迁移
│   ├── alembic.ini          # Alembic配置
│   ├── init_db.py           # 数据库初始化
│   ├── update_db.py         # 数据库更新脚本
│   └── init.sql             # 初始化SQL
├── scripts/                 # 部署和配置脚本
│   ├── docker-compose.yml   # Docker编排
│   ├── Dockerfile           # Docker镜像
│   ├── nginx.conf           # Nginx配置
│   └── run.py               # 原始启动脚本
├── tests/                   # 测试文件
│   ├── test_*.py            # 各种测试文件
│   ├── simple_*.py          # 简单测试脚本
│   ├── websocket_test.html  # WebSocket测试页面
│   └── create_test_pdf.py   # 测试PDF生成
├── uploads/                 # 上传文件目录
├── exports/                 # 导出文件目录
├── requirements.txt         # 依赖列表
├── .env                     # 环境配置
├── run.py                   # 启动脚本
├── README.md               # 项目文档
├── API_Documentation.md     # API文档
└── WebSocket_Guide.md       # WebSocket使用指南
```

## 开发指南

### 添加新的路由

1. 在 `app/routes/` 目录下创建新的路由文件
2. 在 `app/main.py` 中注册路由

### 添加新的服务

1. 在 `app/services/` 目录下创建服务文件
2. 在相应的路由中导入和使用服务

### 数据库迁移

```bash
# 切换到数据库目录
cd database

# 创建新迁移
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 返回项目根目录
cd ..
```

## 部署

### Docker部署

```dockerfile
# Dockerfile示例
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run.py"]
```

### 生产环境配置

1. 设置环境变量
2. 配置反向代理（Nginx）
3. 使用进程管理器（Supervisor/systemd）
4. 配置日志轮转
5. 设置监控和告警

## 常见问题

### Q: OCR识别效果不好？
A: 确保Tesseract正确安装，并配置中文语言包。可以调整图片预处理参数。

### Q: 向量检索速度慢？
A: 确保PGVector扩展正确安装，并为embedding字段创建索引。

### Q: OpenRouter API调用失败？
A: 检查API密钥是否正确，网络连接是否正常，是否有足够的配额。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请联系开发团队。