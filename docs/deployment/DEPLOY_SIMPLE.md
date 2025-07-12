# ContractShield AI - 简单粗暴部署方案

## 🎯 超简单部署

只需要 3 步：

### 1. 构建镜像
```bash
cd deployment
./push_image.sh
cd ..
```

### 2. 配置 API 密钥
```bash
cp .env.example .env
nano .env  # 只需要修改 OPENROUTER_API_KEY
```

### 3. 一键部署
```bash
cd deployment
./deploy.sh
cd ..
```

完成！应用将在 http://localhost:8000 运行

## 📁 核心文件

- **`deployment/push_image.sh`** - 构建和推送 Docker 镜像
- **`deployment/deploy.sh`** - 一键部署脚本（包含数据库）
- **`database/init_complete.sql`** - 完整数据库初始化脚本
- **`database/update.sql`** - 数据库更新脚本模板
- **`.env.example`** - 环境配置模板

## 🗄️ 数据库管理

### 初始化数据库
数据库会在首次部署时自动初始化，使用 `database/init_complete.sql`

### 更新数据库
编辑 `database/update.sql` 文件，添加更新语句，然后执行：
```bash
docker exec -i contractshield-db psql -U contractshield -d contractshield < database/update.sql
```

### 数据库连接
```bash
# 连接数据库
docker exec -it contractshield-db psql -U contractshield -d contractshield

# 备份数据库
docker exec contractshield-db pg_dump -U contractshield contractshield > backup.sql

# 恢复数据库
docker exec -i contractshield-db psql -U contractshield -d contractshield < backup.sql
```

## 🔧 管理命令

```bash
# 查看应用日志
docker logs -f contractshield-app

# 查看数据库日志
docker logs -f contractshield-db

# 重启应用
docker restart contractshield-app

# 停止所有服务
docker stop contractshield-app contractshield-db

# 更新应用
cd deployment
./push_image.sh  # 构建新镜像
./deploy.sh      # 重新部署
cd ..
```

## 📋 默认配置

- **应用端口**: 8000
- **数据库端口**: 5432
- **数据库用户**: contractshield
- **数据库密码**: contractshield123
- **数据库名**: contractshield

## 🚨 注意事项

1. **必须配置 OpenRouter API 密钥**，否则 AI 功能无法使用
2. 数据库数据存储在 Docker 卷 `postgres_data` 中，删除卷会丢失数据
3. 上传的文件存储在 Docker 卷中，重新部署不会丢失
4. 首次部署会自动创建数据库容器，后续部署可选择是否重新创建

## 🔍 故障排除

### 应用无法启动
```bash
docker logs contractshield-app
```

### 数据库连接失败
```bash
docker logs contractshield-db
docker exec contractshield-app ping host.docker.internal
```

### API 调用失败
检查 `.env` 文件中的 `OPENROUTER_API_KEY` 是否正确配置