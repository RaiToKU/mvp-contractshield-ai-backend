#!/bin/bash

# 完整重新部署脚本
echo "=== ContractShield 完整重新部署 ==="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 完全清理
log_info "完全清理现有部署..."
docker-compose down -v 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# 2. 启动数据库
log_info "启动数据库服务..."
docker-compose up -d postgres

# 3. 等待数据库启动
log_info "等待数据库启动..."
sleep 30

# 4. 验证数据库状态
log_info "验证数据库状态..."
for i in {1..10}; do
    if docker-compose exec -T postgres pg_isready -U postgres -d contractshield 2>/dev/null; then
        log_success "数据库已就绪"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "数据库启动超时"
        docker-compose logs postgres
        exit 1
    fi
    sleep 3
done

# 5. 强制确保用户存在
log_info "确保 contractshield 用户存在..."
docker-compose exec -T postgres psql -U postgres -d contractshield << 'EOF'
-- 确保用户存在
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'contractshield') THEN
        CREATE USER contractshield WITH PASSWORD 'contractshield123';
        GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
        GRANT ALL PRIVILEGES ON SCHEMA public TO contractshield;
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
        GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contractshield;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contractshield;
    END IF;
END
$$;

-- 验证用户
SELECT 'User verification:' as status, rolname, rolcanlogin FROM pg_roles WHERE rolname = 'contractshield';
EOF

# 6. 测试用户连接
log_info "测试 contractshield 用户连接..."
if docker-compose exec -T postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "SELECT current_user, current_database();"; then
    log_success "contractshield 用户连接成功！"
else
    log_error "contractshield 用户连接失败"
    exit 1
fi

# 7. 启动 db-wait 服务
log_info "启动数据库等待服务..."
docker-compose up -d db-wait

# 8. 等待 db-wait 完成
log_info "等待数据库验证完成..."
sleep 10

# 检查 db-wait 状态
if docker-compose ps db-wait | grep -q "Exit 0"; then
    log_success "数据库验证完成"
else
    log_warning "检查 db-wait 日志..."
    docker-compose logs db-wait
fi

# 9. 启动应用服务
log_info "启动应用服务..."
docker-compose up -d app

# 10. 等待应用启动
log_info "等待应用启动..."
sleep 20

# 11. 检查应用健康状态
log_info "检查应用健康状态..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health 2>/dev/null; then
        log_success "应用健康检查通过"
        break
    fi
    if [ $i -eq 10 ]; then
        log_warning "应用健康检查失败，查看日志..."
        docker-compose logs app
    fi
    sleep 3
done

# 12. 启动 nginx
log_info "启动 Nginx 服务..."
docker-compose up -d nginx

# 13. 最终状态检查
log_info "最终状态检查..."
docker-compose ps

# 14. 显示访问信息
echo ""
log_success "🎉 部署完成！"
echo ""
echo "访问信息："
echo "  - API 端点: http://localhost:8000"
echo "  - Nginx 代理: http://localhost:80"
echo "  - 数据库: localhost:5432"
echo ""
echo "验证命令："
echo "  - 检查服务状态: docker-compose ps"
echo "  - 查看应用日志: docker-compose logs app"
echo "  - 测试 API: curl http://localhost:8000/health"
echo ""