#!/bin/bash

# ContractShield AI Backend 部署验证脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 检查服务状态
check_services() {
    log_info "检查 Docker 服务状态..."
    
    # 检查 Docker Compose 服务
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker Compose 服务正在运行"
        docker-compose ps
    else
        log_error "Docker Compose 服务未运行"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    log_info "检查数据库连接..."
    
    # 检查 PostgreSQL 连接
    if docker-compose exec -T postgres pg_isready -U contractshield -d contractshield &>/dev/null; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
        return 1
    fi
    
    # 检查数据库表
    log_info "检查数据库表结构..."
    tables=$(docker-compose exec -T postgres psql -U contractshield -d contractshield -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';" 2>/dev/null | tr -d ' ' | grep -v '^$' | wc -l)
    
    if [ "$tables" -gt 0 ]; then
        log_success "数据库表已创建 ($tables 个表)"
        docker-compose exec -T postgres psql -U contractshield -d contractshield -c "\\dt"
    else
        log_error "数据库表未创建"
        return 1
    fi
    
    # 检查 pgvector 扩展
    log_info "检查 pgvector 扩展..."
    if docker-compose exec -T postgres psql -U contractshield -d contractshield -t -c "SELECT 1 FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | grep -q "1"; then
        log_success "pgvector 扩展已安装"
    else
        log_error "pgvector 扩展未安装"
        return 1
    fi
}

# 检查应用服务
check_application() {
    log_info "检查应用服务..."
    
    # 检查应用健康状态
    for i in {1..10}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "应用服务健康检查通过"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "应用服务健康检查失败"
            return 1
        fi
        sleep 2
    done
    
    # 检查 API 文档
    if curl -f http://localhost:8000/docs &>/dev/null; then
        log_success "API 文档可访问"
    else
        log_warning "API 文档不可访问"
    fi
}

# 检查 Nginx 服务
check_nginx() {
    log_info "检查 Nginx 服务..."
    
    if curl -f http://localhost:80/health &>/dev/null; then
        log_success "Nginx 代理正常"
    else
        log_warning "Nginx 代理不可用（可选服务）"
    fi
}

# 性能测试
performance_test() {
    log_info "执行基本性能测试..."
    
    # 测试数据库查询性能
    start_time=$(date +%s%N)
    docker-compose exec -T postgres psql -U contractshield -d contractshield -c "SELECT COUNT(*) FROM tasks;" &>/dev/null
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))
    
    if [ $duration -lt 1000 ]; then
        log_success "数据库查询性能良好 (${duration}ms)"
    else
        log_warning "数据库查询性能较慢 (${duration}ms)"
    fi
}

# 显示系统信息
show_system_info() {
    log_info "系统信息："
    echo "  - Docker 版本: $(docker --version)"
    echo "  - Docker Compose 版本: $(docker-compose --version 2>/dev/null || docker compose version)"
    echo "  - 系统时间: $(date)"
    echo "  - 可用内存: $(free -h | grep '^Mem:' | awk '{print $7}' 2>/dev/null || echo 'N/A')"
    echo "  - 磁盘空间: $(df -h . | tail -1 | awk '{print $4}' 2>/dev/null || echo 'N/A')"
}

# 显示访问信息
show_access_info() {
    log_success "🎉 部署验证完成！"
    echo
    echo "服务访问地址："
    echo "  - API 服务: http://localhost:8000"
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo "  - Nginx 代理: http://localhost:80"
    echo
    echo "数据库信息："
    echo "  - 主机: localhost:5432"
    echo "  - 数据库: contractshield"
    echo "  - 用户: contractshield"
    echo
}

# 主函数
main() {
    echo "ContractShield AI Backend 部署验证"
    echo "===================================="
    echo
    
    show_system_info
    echo
    
    # 执行检查
    check_services || exit 1
    echo
    
    check_database || exit 1
    echo
    
    check_application || exit 1
    echo
    
    check_nginx
    echo
    
    performance_test
    echo
    
    show_access_info
}

# 切换到脚本目录
cd "$(dirname "$0")"

# 执行主函数
main "$@"