#!/bin/bash

# 最终验证脚本
echo "=== ContractShield 部署验证 ==="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 检查容器状态
log_info "检查容器状态..."
docker-compose ps

# 2. 测试数据库连接
log_info "测试数据库连接..."
if docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "SELECT 'Database connection: OK' as status;" 2>/dev/null; then
    log_success "数据库连接正常"
else
    log_error "数据库连接失败"
fi

# 3. 测试应用健康检查
log_info "测试应用健康检查..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log_success "应用健康检查通过"
    echo "响应: $HEALTH_RESPONSE"
else
    log_error "应用健康检查失败"
    echo "响应: $HEALTH_RESPONSE"
fi

# 4. 测试 Nginx 代理
log_info "测试 Nginx 代理..."
NGINX_RESPONSE=$(curl -s http://localhost:80/health 2>/dev/null)
if echo "$NGINX_RESPONSE" | grep -q "healthy"; then
    log_success "Nginx 代理正常"
else
    log_error "Nginx 代理可能有问题"
fi

# 5. 检查数据库表
log_info "检查数据库表结构..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    'Table: ' || tablename as info,
    tableowner as owner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
"

# 6. 检查 pgvector 扩展
log_info "检查 pgvector 扩展..."
docker exec contractshield-postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    'Extension: ' || extname as info,
    extversion as version
FROM pg_extension 
WHERE extname = 'vector';
"

echo ""
log_success "🎉 验证完成！"
echo ""
echo "如果所有检查都通过，ContractShield AI Backend 已成功部署并运行。"
echo ""
echo "访问地址："
echo "  - API: http://localhost:8000"
echo "  - Web: http://localhost:80"
echo ""