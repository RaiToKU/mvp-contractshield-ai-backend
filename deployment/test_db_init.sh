#!/bin/bash

# 数据库初始化测试脚本
# 逐步测试数据库初始化过程

set -e

echo "=== 数据库初始化测试 ==="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. 停止并清理现有服务
log_info "停止并清理现有服务..."
docker-compose down -v 2>/dev/null || true

# 2. 启动数据库服务
log_info "启动数据库服务..."
docker-compose up -d postgres

# 3. 等待数据库启动
log_info "等待数据库启动..."
sleep 15

# 4. 检查数据库是否可访问
log_info "检查数据库连接..."
if docker-compose exec postgres pg_isready -U postgres -d contractshield; then
    log_success "数据库连接正常"
else
    log_error "数据库连接失败"
    docker-compose logs postgres
    exit 1
fi

# 5. 检查初始化脚本是否执行
log_info "检查初始化脚本执行情况..."
docker-compose logs postgres | grep -E "(init|user|permission)" || true

# 6. 检查用户是否存在
log_info "检查 contractshield 用户..."
USER_EXISTS=$(docker-compose exec postgres psql -U postgres -d contractshield -t -c "SELECT 1 FROM pg_roles WHERE rolname='contractshield';" | xargs)
if [ "$USER_EXISTS" = "1" ]; then
    log_success "contractshield 用户存在"
else
    log_error "contractshield 用户不存在，手动创建..."
    
    # 手动创建用户
    docker-compose exec postgres psql -U postgres -d contractshield -c "
        DROP USER IF EXISTS contractshield;
        CREATE USER contractshield WITH PASSWORD 'contractshield123';
        GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
        GRANT ALL ON SCHEMA public TO contractshield;
        GRANT CREATE ON SCHEMA public TO contractshield;
        GRANT USAGE ON SCHEMA public TO contractshield;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contractshield;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contractshield;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO contractshield;
    "
    
    # 再次检查
    USER_EXISTS=$(docker-compose exec postgres psql -U postgres -d contractshield -t -c "SELECT 1 FROM pg_roles WHERE rolname='contractshield';" | xargs)
    if [ "$USER_EXISTS" = "1" ]; then
        log_success "contractshield 用户手动创建成功"
    else
        log_error "用户创建失败"
        exit 1
    fi
fi

# 7. 测试用户连接
log_info "测试 contractshield 用户连接..."
if docker-compose exec postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "SELECT current_user;"; then
    log_success "contractshield 用户连接成功"
else
    log_error "contractshield 用户连接失败"
    exit 1
fi

# 8. 检查扩展
log_info "检查 pgvector 扩展..."
EXTENSION_EXISTS=$(docker-compose exec postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" | xargs)
if [ "$EXTENSION_EXISTS" = "1" ]; then
    log_success "pgvector 扩展已安装"
else
    log_warning "pgvector 扩展未安装，这可能在后续步骤中安装"
fi

# 9. 启动 db-wait 服务进行完整验证
log_info "运行完整的数据库验证..."
if docker-compose up db-wait; then
    log_success "数据库验证通过"
else
    log_error "数据库验证失败"
    docker-compose logs db-wait
    exit 1
fi

log_success "🎉 数据库初始化测试完成！"
echo
echo "现在可以启动应用服务："
echo "  docker-compose up -d app"
echo "  docker-compose up -d nginx"