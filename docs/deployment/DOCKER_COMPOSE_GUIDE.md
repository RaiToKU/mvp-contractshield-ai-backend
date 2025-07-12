# ContractShield AI - Docker Compose 部署指南

## 🚀 快速开始

### 1. 配置环境变量

Docker Compose 会**自动读取项目根目录下的 `.env` 文件**，无需额外配置。

```bash
# 方式一：从模板创建（推荐）
cp .env.docker .env

# 方式二：从示例创建
cp .env.example .env

# 编辑环境变量（重要：设置你的 OpenRouter API Key）
nano .env
```

**重要说明**：
- `.env` 文件必须放在 `docker-compose.yml` 同级目录
- Docker Compose 会自动加载 `.env` 文件中的变量
- 在 `docker-compose.yml` 中使用 `${变量名}` 语法引用环境变量

### 2. 启动服务
```bash
# 使用部署脚本启动（推荐）
./docker-deploy.sh start

# 或者直接使用 docker-compose
docker-compose up -d --build
```

### 3. 访问服务
- **API 文档**: http://localhost:8000/docs
- **API 接口**: http://localhost:8000
- **数据库**: localhost:5432

## 📋 环境变量详解

### .env 文件结构
```bash
# OpenRouter AI API 配置（必须配置）
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 数据库配置（已在 docker-compose.yml 中预设）
POSTGRES_DB=contractshield
POSTGRES_USER=contractshield
POSTGRES_PASSWORD=contractshield123

# 应用配置（可选，有默认值）
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# 文件上传配置（可选，有默认值）
MAX_FILE_SIZE=50000000
```

### 环境变量使用方式

#### 在 docker-compose.yml 中的使用
```yaml
services:
  app:
    environment:
      # 直接引用 .env 文件中的变量
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DATABASE_URL=postgresql://contractshield:contractshield123@postgres:5432/contractshield
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
```

#### 变量优先级
1. **docker-compose.yml 中直接定义的值**（最高优先级）
2. **.env 文件中的变量**
3. **系统环境变量**
4. **应用默认值**（最低优先级）

### 必需的环境变量
| 变量名 | 说明 | 示例值 | 是否必需 |
|--------|------|--------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | `sk-or-v1-xxx...` | ✅ **必需** |

### 可选的环境变量
| 变量名 | 说明 | 默认值 | 备注 |
|--------|------|--------|------|
| `APP_PORT` | 应用端口 | 8000 | 容器内端口 |
| `DEBUG` | 调试模式 | False | 生产环境建议 False |
| `LOG_LEVEL` | 日志级别 | INFO | DEBUG/INFO/WARNING/ERROR |
| `MAX_FILE_SIZE` | 最大文件大小 | 50000000 | 字节为单位 |
| `POSTGRES_DB` | 数据库名 | contractshield | 已预设 |
| `POSTGRES_USER` | 数据库用户 | contractshield | 已预设 |
| `POSTGRES_PASSWORD` | 数据库密码 | contractshield123 | 已预设 |

## 📋 服务组件

### PostgreSQL 数据库
- **容器名**: contractshield-postgres
- **端口**: 5432
- **数据库**: contractshield
- **用户名**: contractshield
- **密码**: contractshield123

### ContractShield AI 应用
- **容器名**: contractshield-app
- **端口**: 8000
- **健康检查**: http://localhost:8000/health

## 🛠️ 管理命令

### 使用部署脚本（推荐）
```bash
# 启动服务
./docker-deploy.sh start

# 停止服务
./docker-deploy.sh stop

# 重启服务
./docker-deploy.sh restart

# 查看日志
./docker-deploy.sh logs

# 查看状态
./docker-deploy.sh status

# 清理所有数据
./docker-deploy.sh clean
```

### 使用 Docker Compose
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重新构建并启动
docker-compose up -d --build
```

## 📁 数据持久化

### 数据卷
- `postgres_data`: PostgreSQL 数据
- `app_uploads`: 上传的文件
- `app_exports`: 导出的文件
- `app_logs`: 应用日志

### 备份数据
```bash
# 备份数据库
docker exec contractshield-postgres pg_dump -U contractshield contractshield > backup.sql

# 恢复数据库
docker exec -i contractshield-postgres psql -U contractshield contractshield < backup.sql
```

## 🔧 配置说明

### 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | **必须设置** |
| `APP_PORT` | 应用端口 | 8000 |
| `DEBUG` | 调试模式 | False |
| `LOG_LEVEL` | 日志级别 | INFO |
| `MAX_FILE_SIZE` | 最大文件大小 | 50000000 |

### 网络配置
- 所有服务运行在 `contractshield-network` 网络中
- 应用通过服务名 `postgres` 连接数据库
- 外部只暴露必要的端口（8000, 5432）

## 🔍 故障排除

### 环境变量相关问题

#### 1. 检查 .env 文件是否被正确加载
```bash
# 查看 docker-compose 解析后的配置
docker-compose config

# 检查特定服务的环境变量
docker-compose config --services
docker-compose config app
```

#### 2. 验证容器内的环境变量
```bash
# 查看应用容器的所有环境变量
docker exec contractshield-app env

# 检查特定的环境变量
docker exec contractshield-app env | grep OPENROUTER_API_KEY
docker exec contractshield-app env | grep DATABASE_URL
```

#### 3. .env 文件格式要求
```bash
# ✅ 正确格式
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEBUG=False

# ❌ 错误格式（不要有空格）
OPENROUTER_API_KEY = sk-or-v1-your-key-here
DEBUG = False

# ❌ 错误格式（不要用引号，除非值本身包含引号）
OPENROUTER_API_KEY="sk-or-v1-your-key-here"
```

### 常见问题

#### 1. 服务启动失败
```bash
# 查看详细日志
docker-compose logs app
docker-compose logs postgres

# 检查容器状态
docker-compose ps
```

#### 2. 数据库连接失败
```bash
# 检查数据库是否就绪
docker exec contractshield-postgres pg_isready -U contractshield

# 测试数据库连接
docker exec contractshield-postgres psql -U contractshield -d contractshield -c "SELECT 1;"
```

#### 3. API 调用失败
```bash
# 检查 OPENROUTER_API_KEY 是否正确设置
docker exec contractshield-app env | grep OPENROUTER_API_KEY

# 测试健康检查
curl http://localhost:8000/health

# 查看应用日志
docker-compose logs -f app
```

#### 4. 端口冲突
如果端口 8000 或 5432 被占用：
```bash
# 方式一：修改 .env 文件（推荐）
echo "APP_PORT=8001" >> .env

# 方式二：修改 docker-compose.yml 中的端口映射
# 将 "8000:8000" 改为 "8001:8000"
```

#### 5. 环境变量不生效
```bash
# 确保 .env 文件在正确位置
ls -la .env

# 重新启动服务以加载新的环境变量
docker-compose down
docker-compose up -d

# 强制重新构建
docker-compose up -d --build --force-recreate
```

### 清理和重置
```bash
# 停止所有服务
docker-compose down

# 清理所有数据
docker-compose down -v

# 清理 Docker 缓存
docker system prune -a
```

## 📊 监控和日志

### 查看实时日志
```bash
# 所有服务日志
docker-compose logs -f

# 特定服务日志
docker-compose logs -f app
docker-compose logs -f postgres
```

### 健康检查
```bash
# 检查应用健康状态
curl http://localhost:8000/health

# 检查数据库健康状态
docker exec contractshield-postgres pg_isready -U contractshield
```

## 🔄 更新和维护

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 数据库迁移
```bash
# 进入应用容器
docker exec -it contractshield-app bash

# 运行数据库迁移
python -m alembic upgrade head
```

## 🚀 生产环境建议

1. **安全配置**
   - 修改默认数据库密码
   - 使用强密码和安全的 API 密钥
   - 配置防火墙规则

2. **性能优化**
   - 调整 PostgreSQL 配置
   - 配置适当的资源限制
   - 使用 SSD 存储

3. **备份策略**
   - 定期备份数据库
   - 备份上传的文件
   - 测试恢复流程

4. **监控**
   - 配置日志聚合
   - 设置健康检查告警
   - 监控资源使用情况