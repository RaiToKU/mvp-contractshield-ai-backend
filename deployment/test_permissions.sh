#!/bin/bash

# 数据库权限测试脚本
# 用于验证 contractshield 用户是否有正确的权限

echo "🔍 测试数据库权限..."

# 等待数据库启动
echo "等待数据库启动..."
sleep 5

# 测试基本连接
echo "📡 测试数据库连接..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "SELECT current_user, current_database();"

if [ $? -eq 0 ]; then
    echo "✅ 数据库连接成功"
else
    echo "❌ 数据库连接失败"
    exit 1
fi

# 测试创建表权限
echo "🔧 测试创建表权限..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "
CREATE TABLE IF NOT EXISTS test_permissions (
    id SERIAL PRIMARY KEY,
    test_data VARCHAR(100)
);
"

if [ $? -eq 0 ]; then
    echo "✅ 创建表权限正常"
else
    echo "❌ 创建表权限失败"
    exit 1
fi

# 测试插入数据权限
echo "📝 测试插入数据权限..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "
INSERT INTO test_permissions (test_data) VALUES ('permission test');
"

if [ $? -eq 0 ]; then
    echo "✅ 插入数据权限正常"
else
    echo "❌ 插入数据权限失败"
    exit 1
fi

# 测试查询数据权限
echo "🔍 测试查询数据权限..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "
SELECT * FROM test_permissions;
"

if [ $? -eq 0 ]; then
    echo "✅ 查询数据权限正常"
else
    echo "❌ 查询数据权限失败"
    exit 1
fi

# 清理测试表
echo "🧹 清理测试数据..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "
DROP TABLE IF EXISTS test_permissions;
"

# 检查主要表是否存在
echo "📋 检查主要表..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "\\dt"

# 检查 pgvector 扩展
echo "🔌 检查 pgvector 扩展..."
docker-compose exec -T postgres psql -U contractshield -d contractshield -c "
SELECT * FROM pg_extension WHERE extname = 'vector';
"

echo "🎉 权限测试完成！"