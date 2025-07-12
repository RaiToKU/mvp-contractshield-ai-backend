# 数据库初始化快速指南

## 🔑 数据库管理账号信息

```bash
数据库名: contractshield
用户名:   contractshield  
密码:     contractshield123
主机:     localhost
端口:     5432
```

## 🚀 快速初始化步骤

### 1. 启动数据库服务

```bash
# 方式一：使用 deployment 目录的 docker-compose
cd deployment
docker-compose up -d postgres

# 方式二：直接启动 PostgreSQL 容器
docker run -d \
  --name contractshield-postgres \
  -e POSTGRES_DB=contractshield \
  -e POSTGRES_USER=contractshield \
  -e POSTGRES_PASSWORD=contractshield123 \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15
```

### 2. 等待数据库启动

```bash
# 检查容器状态
docker ps | grep postgres

# 检查数据库是否就绪
docker exec contractshield-postgres pg_isready -U contractshield -d contractshield
```

### 3. 手动初始化数据库

```bash
# 安装 PGVector 扩展
docker exec -i contractshield-postgres psql -U contractshield -d contractshield << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

# 执行初始化脚本
docker exec -i contractshield-postgres psql -U contractshield -d contractshield < database/init_complete.sql
```

### 4. 验证初始化

```bash
# 连接到数据库
docker exec -it contractshield-postgres psql -U contractshield -d contractshield

# 在 psql 中执行以下命令查看表结构
\dt
\dx
```

## 🔧 使用数据库管理脚本

```bash
# 给脚本执行权限
chmod +x db-manager.sh

# 显示连接信息
./db-manager.sh info

# 初始化数据库
./db-manager.sh init

# 连接到数据库
./db-manager.sh connect

# 查看数据库状态
./db-manager.sh status

# 显示帮助
./db-manager.sh help
```

## 🔍 常见问题解决

### 问题1：容器无法启动
```bash
# 检查端口是否被占用
lsof -i :5432

# 停止可能冲突的服务
brew services stop postgresql  # 如果安装了 Homebrew PostgreSQL
```

### 问题2：初始化脚本未执行
```bash
# 手动执行初始化
docker exec -i contractshield-postgres psql -U contractshield -d contractshield < database/init.sql
docker exec -i contractshield-postgres psql -U contractshield -d contractshield < database/init_complete.sql
```

### 问题3：权限问题
```bash
# 重新创建容器
docker stop contractshield-postgres
docker rm contractshield-postgres
docker volume rm postgres_data  # 注意：这会删除所有数据

# 重新启动
cd deployment
docker-compose up -d postgres
```

### 问题4：连接失败
```bash
# 检查容器日志
docker logs contractshield-postgres

# 检查网络连接
docker exec contractshield-postgres netstat -tlnp
```

## 📊 数据库管理命令

```bash
# 备份数据库
docker exec contractshield-postgres pg_dump -U contractshield -d contractshield > backup.sql

# 恢复数据库
docker exec -i contractshield-postgres psql -U contractshield -d contractshield < backup.sql

# 查看数据库大小
docker exec contractshield-postgres psql -U contractshield -d contractshield -c "SELECT pg_size_pretty(pg_database_size('contractshield'));"

# 查看表大小
docker exec contractshield-postgres psql -U contractshield -d contractshield -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## 🔗 外部连接

如果需要从外部工具连接数据库：

```bash
# 连接字符串
postgresql://contractshield:contractshield123@localhost:5432/contractshield

# pgAdmin 连接参数
Host: localhost
Port: 5432
Database: contractshield
Username: contractshield
Password: contractshield123

# DBeaver 连接参数
Server Host: localhost
Port: 5432
Database: contractshield
Username: contractshield
Password: contractshield123
```