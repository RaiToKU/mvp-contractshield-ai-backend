# ContractShield AI Backend - 部署指南

## 概述

本指南提供了 ContractShield AI Backend 的完整部署方案，使用 Docker Compose 实现一键部署，包括数据库初始化、插件安装和服务启动的完整流程。

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 内存
- 至少 10GB 磁盘空间

## 快速部署

### 1. 准备环境

```bash
# 克隆项目
git clone <repository-url>
cd mvp-contractshield-ai-backend/deployment

# 配置环境变量
cp .env.production .env.local
# 编辑 .env.local，设置 OPENAI_API_KEY 等必要配置
```

### 2. 一键部署

```bash
# 标准部署
./deploy.sh

# 清理后重新部署
./deploy.sh --clean

# 仅验证部署状态
./deploy.sh --verify
```

### 3. 访问服务

部署完成后，可以通过以下地址访问：

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Nginx 代理**: http://localhost:80

## 部署架构

### 服务组件

1. **PostgreSQL 数据库** (`postgres`)
   - 镜像: `pgvector/pgvector:pg15`
   - 端口: 5432
   - 包含 pgvector 扩展支持

2. **数据库初始化等待服务** (`db-wait`)
   - 确保数据库完全初始化后再启动应用
   - 验证数据库连接和表结构

3. **应用服务** (`app`)
   - 基于 Python 3.11
   - 端口: 8000
   - 包含 OCR 和文档处理功能

4. **Nginx 反向代理** (`nginx`)
   - 端口: 80, 443
   - 可选组件，用于负载均衡

### 数据库初始化流程

部署过程中会按顺序执行以下初始化脚本：

1. `database/init.sql` - 创建 pgvector 扩展
2. `database/init_user.sql` - 创建数据库用户和基础权限
3. `database/fix_permissions.sql` - 修复和确认用户权限
4. `database/init_complete.sql` - 创建表结构和索引

### 启动顺序

1. PostgreSQL 数据库启动
2. 数据库健康检查通过
3. 执行数据库初始化脚本
4. db-wait 服务验证数据库就绪
5. 应用服务启动
6. Nginx 服务启动

## 配置说明

### 环境变量配置

主要配置项（`.env.production`）：

```bash
# 数据库配置
POSTGRES_DB=contractshield
POSTGRES_USER=contractshield
POSTGRES_PASSWORD=contractshield123
DATABASE_URL=postgresql://contractshield:contractshield123@postgres:5432/contractshield

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here

# 文件配置
MAX_FILE_SIZE=50MB
UPLOAD_DIR=/app/uploads
TEMP_DIR=/app/temp
```

### Docker Compose 配置

主要特性：

- **健康检查**: 所有服务都配置了健康检查
- **依赖管理**: 确保服务按正确顺序启动
- **数据持久化**: 使用 Docker volumes 持久化数据
- **网络隔离**: 使用自定义网络确保服务间通信

## 管理命令

### 基本操作

```bash
# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart app

# 进入容器
docker-compose exec app bash
docker-compose exec postgres psql -U contractshield -d contractshield
```

### 数据库操作

```bash
# 连接数据库
docker-compose exec postgres psql -U contractshield -d contractshield

# 查看表结构
docker-compose exec postgres psql -U contractshield -d contractshield -c "\\dt"

# 备份数据库
docker-compose exec postgres pg_dump -U contractshield contractshield > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U contractshield -d contractshield < backup.sql
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose exec postgres pg_isready -U contractshield -d contractshield
   
   # 查看数据库日志
   docker-compose logs postgres
   ```

2. **应用启动失败**
   ```bash
   # 查看应用日志
   docker-compose logs app
   
   # 检查环境变量
   docker-compose exec app env | grep DATABASE_URL
   ```

3. **pgvector 扩展问题**
   ```bash
   # 检查扩展状态
   docker-compose exec postgres psql -U contractshield -d contractshield -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

4. **数据库权限问题** (`permission denied for schema public`)
   ```bash
   # 测试数据库权限
   ./test_permissions.sh
   
   # 手动修复权限
   docker-compose exec postgres psql -U postgres -d contractshield -f /docker-entrypoint-initdb.d/03-fix-permissions.sql
   
   # 验证权限设置
   docker-compose exec postgres psql -U contractshield -d contractshield -c "SELECT current_user, has_schema_privilege('public', 'CREATE');"
   ```

5. **表创建失败**
   ```bash
   # 检查用户权限
   docker-compose exec postgres psql -U postgres -d contractshield -c "\\du contractshield"
   
   # 重新授予权限
   docker-compose exec postgres psql -U postgres -d contractshield -c "GRANT ALL ON SCHEMA public TO contractshield;"
   ```

### 重新部署

如果遇到问题，可以完全重新部署：

```bash
# 停止所有服务
./deploy.sh --stop

# 清理并重新部署
./deploy.sh --clean
```

## 生产环境建议

### 安全配置

1. **修改默认密码**
   ```bash
   # 在 .env.production 中设置强密码
   POSTGRES_PASSWORD=your_strong_password_here
   ```

2. **配置 HTTPS**
   - 修改 `nginx.conf` 添加 SSL 配置
   - 使用 Let's Encrypt 获取证书

3. **网络安全**
   - 限制数据库端口访问
   - 配置防火墙规则

### 性能优化

1. **数据库优化**
   - 调整 PostgreSQL 配置参数
   - 定期执行 VACUUM 和 ANALYZE

2. **应用优化**
   - 配置适当的内存限制
   - 启用应用缓存

3. **监控配置**
   - 添加日志聚合
   - 配置性能监控

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull

# 重新构建并部署
./deploy.sh --clean
```

### 数据库迁移

```bash
# 如果有数据库结构变更
docker-compose exec app python -m alembic upgrade head
```

### 备份策略

建议定期备份：

1. 数据库数据
2. 上传的文件
3. 配置文件

## 支持

如果遇到问题，请：

1. 查看日志文件
2. 检查配置文件
3. 参考故障排除部分
4. 联系技术支持