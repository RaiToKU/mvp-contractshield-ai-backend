# ContractShield AI - 环境变量配置说明

## 📋 环境变量文件说明

### 文件类型和用途

| 文件名 | 用途 | 说明 |
|--------|------|------|
| `.env` | **实际使用的环境变量** | Docker Compose 自动读取 |
| `.env.example` | 通用环境变量模板 | 包含所有可能的配置项 |
| `.env.docker` | Docker Compose 专用模板 | 简化版，只包含必需配置 |

### Docker Compose 环境变量加载机制

#### 1. 自动加载 .env 文件
```bash
# Docker Compose 会自动查找并加载以下文件（按优先级）：
# 1. .env（项目根目录）
# 2. 系统环境变量
# 3. docker-compose.yml 中的默认值
```

#### 2. 环境变量引用语法
```yaml
# 在 docker-compose.yml 中使用
services:
  app:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}  # 从 .env 文件读取
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db  # 直接定义
```

#### 3. 变量替换规则
```bash
# .env 文件内容
OPENROUTER_API_KEY=sk-or-v1-abc123
APP_PORT=8000

# docker-compose.yml 中的使用
environment:
  - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}  # 结果：sk-or-v1-abc123
  - APP_PORT=${APP_PORT:-8000}                # 结果：8000（带默认值）
  - DEBUG=${DEBUG:-false}                     # 结果：false（.env中未定义时使用默认值）
```

## 🔧 配置步骤

### 1. 创建 .env 文件
```bash
# 方式一：从 Docker 模板创建（推荐）
cp .env.docker .env

# 方式二：从通用模板创建
cp .env.example .env

# 方式三：手动创建
touch .env
```

### 2. 编辑必需的环境变量
```bash
# 编辑 .env 文件
nano .env

# 最少需要配置：
OPENROUTER_API_KEY=your_actual_api_key_here
```

### 3. 验证配置
```bash
# 检查 .env 文件内容
cat .env

# 验证 Docker Compose 配置
docker-compose config

# 查看解析后的环境变量
docker-compose config app
```

## 📝 .env 文件模板

### 最小配置（必需）
```bash
# OpenRouter AI API 配置
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 完整配置（可选）
```bash
# OpenRouter AI API 配置（必须配置）
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 数据库配置（Docker Compose 中已预设，通常不需要修改）
POSTGRES_DB=contractshield
POSTGRES_USER=contractshield
POSTGRES_PASSWORD=contractshield123

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 文件上传配置
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=50000000

# Tesseract OCR 配置
TESSERACT_CMD=/usr/bin/tesseract

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## ⚠️ 注意事项

### 1. 文件位置
- `.env` 文件必须放在 `docker-compose.yml` 同级目录
- 不要放在子目录中

### 2. 文件格式
```bash
# ✅ 正确格式
KEY=value
ANOTHER_KEY=another_value

# ❌ 错误格式
KEY = value          # 不要有空格
KEY="value"          # 通常不需要引号
KEY='value'          # 通常不需要引号
```

### 3. 安全考虑
```bash
# 确保 .env 文件不被提交到版本控制
echo ".env" >> .gitignore

# 检查 .gitignore
cat .gitignore | grep .env
```

### 4. 变量优先级
1. **docker-compose.yml 中直接定义** （最高）
2. **系统环境变量**
3. **.env 文件中的变量**
4. **docker-compose.yml 中的默认值** （最低）

## 🔍 调试和验证

### 检查环境变量是否生效
```bash
# 1. 查看 Docker Compose 解析结果
docker-compose config

# 2. 检查容器内的环境变量
docker exec contractshield-app env | grep OPENROUTER

# 3. 测试应用是否能正常启动
docker-compose logs app

# 4. 验证 API 功能
curl http://localhost:8000/health
```

### 常见问题排查
```bash
# 问题：环境变量不生效
# 解决：检查文件位置和格式
ls -la .env
cat .env

# 问题：API 密钥错误
# 解决：验证密钥格式
docker exec contractshield-app env | grep OPENROUTER_API_KEY

# 问题：端口冲突
# 解决：修改端口配置
echo "APP_PORT=8001" >> .env
docker-compose up -d --force-recreate
```

## 📚 相关文档

- [Docker Compose 部署指南](./DOCKER_COMPOSE_GUIDE.md)
- [API 文档](./API_Documentation.md)
- [故障排除指南](./DOCKER_DEPLOYMENT_GUIDE.md)