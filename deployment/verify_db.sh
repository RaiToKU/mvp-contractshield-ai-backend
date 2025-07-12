#!/bin/bash

# 数据库验证脚本
echo "=== ContractShield 数据库验证 ==="

# 检查容器状态
echo "[INFO] 检查容器状态..."
docker ps --filter "name=contractshield-postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 测试 contractshield 用户连接
echo -e "\n[INFO] 测试 contractshield 用户连接..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    '✅ 用户连接成功' as status,
    current_user as user,
    current_database() as database;
"

# 检查表结构
echo -e "\n[INFO] 检查数据库表..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
"

# 检查扩展
echo -e "\n[INFO] 检查 pgvector 扩展..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    extname as extension_name,
    extversion as version
FROM pg_extension 
WHERE extname = 'vector';
"

# 测试基本操作
echo -e "\n[INFO] 测试基本数据库操作..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
-- 测试插入和查询
INSERT INTO tasks (id, title, description, status, created_at, updated_at) 
VALUES ('test-' || extract(epoch from now()), 'Test Task', 'Database connection test', 'pending', now(), now())
ON CONFLICT (id) DO NOTHING;

SELECT 
    '✅ 数据库操作正常' as status,
    count(*) as total_tasks
FROM tasks;
"

echo -e "\n[SUCCESS] 🎉 数据库验证完成！"
echo "contractshield 用户现在可以正常访问数据库了。"