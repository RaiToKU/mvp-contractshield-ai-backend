# ContractShield AI 后端 - Docker 镜像构建和部署指南

## 📋 概述

本指南说明如何将 ContractShield AI 后端打包为 Docker 镜像并推送到远程仓库，然后在目标服务器上运行容器。

**重要说明：** 此方案只打包应用本身，数据库、Nginx 等外部服务需要单独部署和配置。

## 🏗️ 第一步：构建和推送 Docker 镜像

### 1.1 构建镜像

在项目根目录执行：

```bash
# 构建镜像
docker build -f deployment/Dockerfile -t contractshield-ai:latest .

# 打标签（替换为你的仓库地址）
docker tag contractshield-ai:latest crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

### 1.2 推送到远程仓库

```bash
# 登录阿里云容器镜像仓库
docker login crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com

# 推送镜像
docker push crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

### 1.3 自动化构建脚本

使用提供的 `push_image.sh` 脚本：

```bash
# 给脚本执行权限
chmod +x push_image.sh

# 执行构建和推送
./push_image.sh
```

## 🗄️ 第二步：准备外部服务

### 2.1 PostgreSQL 数据库

**选项 A：使用 Docker 运行数据库**

```bash
# 创建数据库容器
docker run -d \
  --name contractshield-db \
  -e POSTGRES_DB=contractshield \
  -e POSTGRES_USER=contractshield \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg15

# 等待数据库启动
sleep 30

# 初始化数据库（创建 pgvector 扩展）
docker exec -i contractshield-db psql -U contractshield -d contractshield << 'EOF'
CREATE EXTENSION IF NOT EXISTS vector;
ALTER SYSTEM SET shared_preload_libraries = 'vector';
SELECT pg_reload_conf();
EOF
```

**选项 B：使用现有 PostgreSQL 服务**

确保你的 PostgreSQL 服务器已安装 pgvector 扩展：

```sql
-- 连接到你的数据库
CREATE DATABASE contractshield;
\c contractshield;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.2 配置数据库连接

记录数据库连接信息，稍后在运行容器时使用：

```
数据库主机: localhost (或你的数据库服务器IP)
数据库端口: 5432
数据库名: contractshield
用户名: contractshield
密码: your_secure_password
```

## 🚀 第三步：运行应用容器

### 3.1 基本运行命令

```bash
docker run -d \
  --name contractshield-app \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://contractshield:your_secure_password@host.docker.internal:5432/contractshield" \
  -e OPENROUTER_API_KEY="your_openrouter_api_key" \
  -e APP_HOST="0.0.0.0" \
  -e APP_PORT="8000" \
  -e DEBUG="False" \
  -e UPLOAD_DIR="/app/uploads" \
  -e MAX_FILE_SIZE="50000000" \
  -e TESSERACT_CMD="/usr/bin/tesseract" \
  -v contractshield_uploads:/app/uploads \
  -v contractshield_exports:/app/exports \
  -v contractshield_logs:/app/logs \
  --restart unless-stopped \
  crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

### 3.2 使用环境文件

创建 `.env` 文件：

```bash
cat > .env << 'EOF'
# 数据库配置
DATABASE_URL=postgresql://contractshield:your_secure_password@host.docker.internal:5432/contractshield

# OpenRouter AI API 配置
OPENROUTER_API_KEY=your_openrouter_api_key

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False

# 文件上传配置
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=50000000

# Tesseract OCR 配置
TESSERACT_CMD=/usr/bin/tesseract

# 日志配置
LOG_LEVEL=INFO
EOF
```

然后使用环境文件运行：

```bash
docker run -d \
  --name contractshield-app \
  -p 8000:8000 \
  --env-file .env \
  -v contractshield_uploads:/app/uploads \
  -v contractshield_exports:/app/exports \
  -v contractshield_logs:/app/logs \
  --restart unless-stopped \
  crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

## ⚙️ 第四步：详细配置说明

### 4.1 必需的环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 数据库连接字符串 | `postgresql://user:pass@host:5432/dbname` |
| `OPENROUTER_API_KEY` | OpenRouter AI API 密钥 | `sk-or-v1-xxx...` |

### 4.2 可选的环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_HOST` | `0.0.0.0` | 应用监听地址 |
| `APP_PORT` | `8000` | 应用监听端口 |
| `DEBUG` | `False` | 是否开启调试模式 |
| `UPLOAD_DIR` | `/app/uploads` | 文件上传目录 |
| `MAX_FILE_SIZE` | `50000000` | 最大文件大小（字节） |
| `TESSERACT_CMD` | `/usr/bin/tesseract` | Tesseract OCR 命令路径 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 4.3 数据库连接字符串格式

```
postgresql://[用户名]:[密码]@[主机]:[端口]/[数据库名]
```

**不同场景的连接字符串：**

- **本地数据库容器**: `postgresql://contractshield:password@host.docker.internal:5432/contractshield`
- **远程数据库服务器**: `postgresql://contractshield:password@192.168.1.100:5432/contractshield`
- **云数据库服务**: `postgresql://user:pass@your-db-host.com:5432/contractshield`

### 4.4 获取 OpenRouter API 密钥

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号并登录
3. 在 API Keys 页面创建新的 API 密钥
4. 复制密钥（格式：`sk-or-v1-xxx...`）

## 🔍 第五步：验证部署

### 5.1 检查容器状态

```bash
# 查看容器状态
docker ps

# 查看容器日志
docker logs contractshield-app

# 实时查看日志
docker logs -f contractshield-app
```

### 5.2 健康检查

```bash
# 检查应用健康状态
curl http://localhost:8000/health

# 预期返回
{"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

### 5.3 API 测试

```bash
# 测试文件上传接口
curl -X POST http://localhost:8000/upload \
  -F "file=@test.pdf" \
  -H "Content-Type: multipart/form-data"
```

## 🛠️ 第六步：常见问题和解决方案

### 6.1 数据库连接失败

**问题**: 容器无法连接到数据库

**解决方案**:
```bash
# 检查数据库是否运行
docker ps | grep postgres

# 检查网络连接
docker exec contractshield-app ping host.docker.internal

# 检查数据库连接
docker exec contractshield-app python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('数据库连接成功')
except Exception as e:
    print(f'数据库连接失败: {e}')
"
```

### 6.2 API 密钥错误

**问题**: OpenRouter API 调用失败

**解决方案**:
```bash
# 检查环境变量
docker exec contractshield-app env | grep OPENROUTER_API_KEY

# 测试 API 密钥
docker exec contractshield-app python -c "
import os
import requests
api_key = os.getenv('OPENROUTER_API_KEY')
headers = {'Authorization': f'Bearer {api_key}'}
response = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
print(f'API 状态: {response.status_code}')
"
```

### 6.3 文件上传失败

**问题**: 文件上传时出现权限错误

**解决方案**:
```bash
# 检查挂载卷权限
docker exec contractshield-app ls -la /app/uploads

# 修复权限（如果需要）
docker exec contractshield-app chown -R app:app /app/uploads
```

## 📋 第七步：生产环境建议

### 7.1 安全配置

```bash
# 使用非 root 用户运行
docker run -d \
  --name contractshield-app \
  --user 1000:1000 \
  -p 8000:8000 \
  --env-file .env \
  -v contractshield_uploads:/app/uploads \
  -v contractshield_exports:/app/exports \
  -v contractshield_logs:/app/logs \
  --restart unless-stopped \
  --memory 2g \
  --cpus 1.0 \
  crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

### 7.2 反向代理配置（可选）

如果需要使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7.3 监控和日志

```bash
# 设置日志轮转
docker run -d \
  --name contractshield-app \
  -p 8000:8000 \
  --env-file .env \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -v contractshield_uploads:/app/uploads \
  -v contractshield_exports:/app/exports \
  -v contractshield_logs:/app/logs \
  --restart unless-stopped \
  crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

## 🔄 第八步：更新和维护

### 8.1 更新应用

```bash
# 拉取最新镜像
docker pull crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest

# 停止旧容器
docker stop contractshield-app
docker rm contractshield-app

# 启动新容器（使用相同的配置）
docker run -d \
  --name contractshield-app \
  -p 8000:8000 \
  --env-file .env \
  -v contractshield_uploads:/app/uploads \
  -v contractshield_exports:/app/exports \
  -v contractshield_logs:/app/logs \
  --restart unless-stopped \
  crpi-quxtxo1i28qk1e0c.cn-guangzhou.personal.cr.aliyuncs.com/arceus/mvp-contractshield-ai-backend:latest
```

### 8.2 备份数据

```bash
# 备份上传文件
docker run --rm -v contractshield_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup_$(date +%Y%m%d).tar.gz -C /data .

# 备份数据库
docker exec contractshield-db pg_dump -U contractshield contractshield > backup_$(date +%Y%m%d).sql
```

## 📞 支持和故障排除

如果遇到问题，请提供以下信息：

1. 容器状态：`docker ps -a`
2. 容器日志：`docker logs contractshield-app`
3. 环境变量：`docker exec contractshield-app env`
4. 系统信息：`docker version` 和 `docker info`