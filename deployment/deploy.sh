#!/bin/bash

# ContractShield AI Backend 部署脚本
# 使用 Docker Compose 一键部署

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

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查完成"
}

# 检查环境变量
check_environment() {
    log_info "检查环境配置..."
    
    if [ ! -f ".env.production" ]; then
        log_warning "未找到 .env.production 文件，创建默认配置..."
        cp .env.production.example .env.production 2>/dev/null || true
    fi
    
    # 检查必要的环境变量
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY 未设置，请在 .env.production 中配置"
    fi
    
    log_success "环境配置检查完成"
}

# 清理旧容器和镜像
cleanup() {
    log_info "清理旧的容器和镜像..."
    
    # 停止并删除容器
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 删除未使用的镜像
    docker image prune -f 2>/dev/null || true
    
    log_success "清理完成"
}

# 构建和启动服务
deploy() {
    log_info "开始部署 ContractShield AI Backend..."
    
    # 设置环境变量文件
    export COMPOSE_FILE=docker-compose.yml
    
    # 构建并启动服务
    log_info "构建应用镜像..."
    docker-compose build --no-cache
    
    log_info "启动数据库服务..."
    docker-compose up -d postgres
    
    log_info "等待数据库启动..."
    sleep 10
    
    # 检查数据库是否启动成功
    log_info "检查数据库状态..."
    if ! docker-compose exec postgres pg_isready -U postgres -d contractshield; then
        log_error "数据库启动失败，查看日志："
        docker-compose logs postgres
        return 1
    fi
    
    # 检查用户是否创建成功
    log_info "检查数据库用户..."
    USER_EXISTS=$(docker-compose exec postgres psql -U postgres -d contractshield -t -c "SELECT 1 FROM pg_roles WHERE rolname='contractshield';" | xargs)
    if [ "$USER_EXISTS" != "1" ]; then
        log_warning "contractshield 用户不存在，手动创建..."
        docker-compose exec postgres psql -U postgres -d contractshield -c "
            CREATE USER contractshield WITH PASSWORD 'contractshield123';
            GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
            GRANT ALL ON SCHEMA public TO contractshield;
            GRANT CREATE ON SCHEMA public TO contractshield;
            GRANT USAGE ON SCHEMA public TO contractshield;
        "
    fi
    
    log_info "等待数据库初始化完成..."
    if ! docker-compose up db-wait; then
        log_error "数据库初始化失败，运行调试脚本..."
        ./debug_db.sh
        return 1
    fi
    
    log_info "启动应用服务..."
    docker-compose up -d app
    
    log_info "启动反向代理..."
    docker-compose up -d nginx
    
    log_success "所有服务启动完成"
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    log_info "检查服务状态..."
    docker-compose ps
    
    # 检查应用健康状态
    log_info "检查应用健康状态..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "应用服务健康检查通过"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "应用服务健康检查失败"
            return 1
        fi
        sleep 2
    done
    
    # 检查数据库连接
    log_info "检查数据库连接..."
    if docker-compose exec -T postgres pg_isready -U contractshield -d contractshield &>/dev/null; then
        log_success "数据库连接正常"
    else
        log_error "数据库连接失败"
        return 1
    fi
    
    log_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 ContractShield AI Backend 部署成功！"
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
    echo "管理命令："
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 查看状态: docker-compose ps"
    echo
}

# 显示帮助信息
show_help() {
    echo "ContractShield AI Backend 部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -c, --clean    清理后重新部署"
    echo "  -v, --verify   仅验证部署状态"
    echo "  --stop         停止所有服务"
    echo "  --logs         查看服务日志"
    echo "  --debug        运行数据库调试脚本"
    echo
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean)
            check_dependencies
            cleanup
            check_environment
            deploy
            verify_deployment
            show_deployment_info
            ;;
        -v|--verify)
            verify_deployment
            ;;
        --stop)
            log_info "停止所有服务..."
            docker-compose down
            log_success "所有服务已停止"
            ;;
        --logs)
            docker-compose logs -f
            ;;
        --debug)
            log_info "运行数据库调试脚本..."
            ./debug_db.sh
            ;;
        "")
            check_dependencies
            check_environment
            deploy
            verify_deployment
            show_deployment_info
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 切换到脚本目录
cd "$(dirname "$0")"

# 执行主函数
main "$@"