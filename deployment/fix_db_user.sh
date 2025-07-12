#!/bin/bash

# 一键修复数据库用户问题的脚本
# 这个脚本将彻底解决 contractshield 用户不存在的问题

set -e

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

echo "=== ContractShield 数据库用户修复脚本 ==="

# 1. 完全清理
log_info "完全清理现有容器和数据..."
docker-compose down -v 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true

# 等待端口释放
sleep 5

# 2. 启动数据库
log_info "启动数据库服务..."
docker-compose up -d postgres

# 3. 等待数据库完全启动
log_info "等待数据库启动（30秒）..."
sleep 30

# 4. 检查数据库状态
log_info "检查数据库状态..."
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

# 5. 强制创建用户（忽略初始化脚本）
log_info "强制创建 contractshield 用户..."
docker-compose exec -T postgres psql -U postgres -d contractshield << 'EOF'
-- 删除用户（如果存在）
DROP USER IF EXISTS contractshield;

-- 创建用户
CREATE USER contractshield WITH PASSWORD 'contractshield123';

-- 授予所有权限
GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
ALTER USER contractshield CREATEDB;
GRANT ALL ON SCHEMA public TO contractshield;
GRANT CREATE ON SCHEMA public TO contractshield;
GRANT USAGE ON SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO contractshield;

-- 验证用户
SELECT 'User contractshield created successfully' as status;
\du contractshield
EOF

# 6. 测试用户连接
log_info "测试 contractshield 用户连接..."
if docker-compose exec -T postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "SELECT current_user, current_database();"; then
    log_success "contractshield 用户连接成功！"
else
    log_error "contractshield 用户连接失败"
    exit 1
fi

# 7. 创建必要的表（如果不存在）
log_info "创建必要的表和扩展..."
docker-compose exec -T postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield << 'EOF'
-- 创建 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建表（如果不存在）
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    result_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    review_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS export_records (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    export_type VARCHAR(50) NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_task_id ON document_chunks(task_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_review_history_task_id ON review_history(task_id);
CREATE INDEX IF NOT EXISTS idx_export_records_task_id ON export_records(task_id);

SELECT 'Tables created successfully' as status;
\dt
EOF

# 8. 最终验证
log_info "最终验证..."
docker-compose exec -T postgres env PGPASSWORD=contractshield123 psql -U contractshield -d contractshield -c "
SELECT 
    'Database verification:' as status,
    current_user as user,
    current_database() as database,
    (SELECT count(*) FROM pg_tables WHERE schemaname = 'public') as table_count,
    (SELECT count(*) FROM pg_extension WHERE extname = 'vector') as vector_extension;
"

log_success "🎉 数据库用户修复完成！"
echo
echo "现在可以启动应用服务："
echo "  docker-compose up -d app"
echo "  docker-compose up -d nginx"
echo
echo "或者运行完整部署："
echo "  ./deploy.sh"