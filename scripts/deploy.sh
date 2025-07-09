#!/bin/bash

# ContractShield AI Backend 部署脚本
# 使用方法: ./scripts/deploy.sh [staging|production]

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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
if [ $# -eq 0 ]; then
    log_error "请指定部署环境: staging 或 production"
    echo "使用方法: $0 [staging|production]"
    exit 1
fi

ENVIRONMENT=$1

# 验证环境参数
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    log_error "无效的环境参数: $ENVIRONMENT"
    echo "支持的环境: staging, production"
    exit 1
fi

log_info "开始部署到 $ENVIRONMENT 环境..."

# 检查必要的文件
check_files() {
    log_info "检查必要的配置文件..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f ".env.prod" ]; then
            log_error "生产环境配置文件 .env.prod 不存在"
            log_info "请复制 .env.prod.example 为 .env.prod 并配置相应的值"
            exit 1
        fi
    else
        if [ ! -f ".env.staging" ]; then
            log_warning "暂存环境配置文件 .env.staging 不存在，将使用 .env.example"
            cp .env.example .env.staging
        fi
    fi
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        log_error "生产环境 Docker Compose 文件不存在"
        exit 1
    fi
    
    log_success "配置文件检查完成"
}

# 备份数据库
backup_database() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "备份生产数据库..."
        
        # 创建备份目录
        mkdir -p backups
        
        # 生成备份文件名
        BACKUP_FILE="backups/contractshield_$(date +%Y%m%d_%H%M%S).sql"
        
        # 执行备份
        docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U contractshield contractshield > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            log_success "数据库备份完成: $BACKUP_FILE"
        else
            log_error "数据库备份失败"
            exit 1
        fi
    fi
}

# 拉取最新镜像
pull_images() {
    log_info "拉取最新的 Docker 镜像..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml --env-file .env.prod pull
    else
        docker-compose -f docker-compose.prod.yml --env-file .env.staging pull
    fi
    
    if [ $? -eq 0 ]; then
        log_success "镜像拉取完成"
    else
        log_error "镜像拉取失败"
        exit 1
    fi
}

# 停止旧服务
stop_services() {
    log_info "停止现有服务..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml --env-file .env.prod down
    else
        docker-compose -f docker-compose.prod.yml --env-file .env.staging down
    fi
    
    log_success "服务停止完成"
}

# 启动新服务
start_services() {
    log_info "启动新服务..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    else
        docker-compose -f docker-compose.prod.yml --env-file .env.staging up -d
    fi
    
    if [ $? -eq 0 ]; then
        log_success "服务启动完成"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 30
    
    # 检查应用健康状态
    for i in {1..10}; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "应用健康检查通过"
            return 0
        fi
        
        log_warning "健康检查失败，等待重试... ($i/10)"
        sleep 10
    done
    
    log_error "应用健康检查失败"
    return 1
}

# 清理旧镜像
cleanup() {
    log_info "清理未使用的 Docker 镜像..."
    docker system prune -f
    log_success "清理完成"
}

# 发送通知
send_notification() {
    local status=$1
    local message="ContractShield AI Backend 部署到 $ENVIRONMENT 环境 $status"
    
    # 如果配置了 Slack Webhook，发送通知
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    log_info "通知已发送: $message"
}

# 回滚函数
rollback() {
    log_error "部署失败，开始回滚..."
    
    # 停止当前服务
    stop_services
    
    # 如果有备份，可以在这里恢复
    # restore_backup
    
    # 启动之前的版本（这里需要根据实际情况实现）
    log_warning "请手动检查并恢复服务"
    
    send_notification "失败，已触发回滚"
    exit 1
}

# 主部署流程
main() {
    log_info "=== ContractShield AI Backend 部署开始 ==="
    log_info "环境: $ENVIRONMENT"
    log_info "时间: $(date)"
    
    # 设置错误处理
    trap rollback ERR
    
    # 执行部署步骤
    check_files
    backup_database
    pull_images
    stop_services
    start_services
    
    # 健康检查
    if health_check; then
        cleanup
        send_notification "成功"
        log_success "=== 部署完成 ==="
        log_info "应用已成功部署到 $ENVIRONMENT 环境"
        log_info "访问地址: http://localhost:8000"
        log_info "健康检查: http://localhost:8000/health"
        log_info "API 文档: http://localhost:8000/docs"
    else
        rollback
    fi
}

# 执行主函数
main "$@"