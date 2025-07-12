#!/bin/bash

# 数据库调试脚本
# 用于诊断数据库初始化问题

echo "=== 数据库调试脚本 ==="

# 检查容器状态
echo "1. 检查容器状态..."
docker-compose ps

echo ""
echo "2. 检查 postgres 容器日志..."
docker-compose logs postgres | tail -20

echo ""
echo "3. 尝试连接 postgres 用户..."
docker-compose exec postgres psql -U postgres -d contractshield -c "SELECT version();"

echo ""
echo "4. 检查用户是否存在..."
docker-compose exec postgres psql -U postgres -d contractshield -c "SELECT rolname FROM pg_roles WHERE rolname = 'contractshield';"

echo ""
echo "5. 如果用户不存在，手动创建..."
docker-compose exec postgres psql -U postgres -d contractshield -c "
CREATE USER contractshield WITH PASSWORD 'contractshield123';
GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
GRANT ALL ON SCHEMA public TO contractshield;
GRANT CREATE ON SCHEMA public TO contractshield;
GRANT USAGE ON SCHEMA public TO contractshield;
"

echo ""
echo "6. 测试 contractshield 用户连接..."
docker-compose exec postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "SELECT current_user;"

echo ""
echo "7. 检查表是否存在..."
docker-compose exec postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "\dt"

echo ""
echo "=== 调试完成 ==="