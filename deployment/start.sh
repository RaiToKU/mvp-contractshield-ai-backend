#!/bin/bash

# ContractShield AI Backend 快速启动脚本

set -e

echo "🚀 ContractShield AI Backend 快速启动"
echo "====================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 切换到脚本目录
cd "$(dirname "$0")"

# 检查环境配置
if [ ! -f ".env.production" ]; then
    echo "📝 创建环境配置文件..."
    cp .env.production.example .env.production
    echo "⚠️  请编辑 .env.production 文件，设置 OPENAI_API_KEY"
fi

echo "🔧 启动服务..."

# 启动数据库
echo "📊 启动数据库..."
docker-compose up -d postgres

# 等待数据库就绪
echo "⏳ 等待数据库初始化..."
docker-compose up db-wait

# 启动应用
echo "🚀 启动应用..."
docker-compose up -d app

# 启动其他服务
echo "🔄 启动代理..."
docker-compose up -d nginx

echo "✅ 启动完成！"
echo
echo "访问地址："
echo "  - API: http://localhost:8000"
echo "  - 文档: http://localhost:8000/docs"
echo
echo "管理命令："
echo "  - 查看状态: docker-compose ps"
echo "  - 查看日志: docker-compose logs -f"
echo "  - 停止服务: docker-compose down"
echo "  - 验证部署: ./verify.sh"