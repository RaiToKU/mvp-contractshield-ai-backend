#!/bin/bash

# ContractShield AI Backend - 环境变量修复脚本
# 用于检查和修复 OPENROUTER_API_KEY 环境变量配置问题

echo "🔧 ContractShield AI Backend - 环境变量修复脚本"
echo "================================================"

# 检查当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 项目根目录: $PROJECT_ROOT"
echo "📁 部署目录: $SCRIPT_DIR"

# 检查 .env 文件
ENV_FILE="$SCRIPT_DIR/.env"
ENV_PRODUCTION_FILE="$SCRIPT_DIR/.env.production"

echo ""
echo "🔍 检查环境变量配置..."

# 检查是否存在 .env 文件
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  未找到 .env 文件，从模板创建..."
    if [ -f "$SCRIPT_DIR/.env.production.example" ]; then
        cp "$SCRIPT_DIR/.env.production.example" "$ENV_FILE"
        echo "✅ 已从 .env.production.example 创建 .env 文件"
    else
        echo "❌ 未找到 .env.production.example 模板文件"
        exit 1
    fi
fi

# 检查 OPENROUTER_API_KEY
if grep -q "OPENROUTER_API_KEY=" "$ENV_FILE"; then
    CURRENT_KEY=$(grep "OPENROUTER_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    if [ "$CURRENT_KEY" = "your_openrouter_api_key_here" ] || [ -z "$CURRENT_KEY" ]; then
        echo "⚠️  OPENROUTER_API_KEY 未设置或使用默认值"
        echo "请设置正确的 OpenRouter API Key:"
        echo "编辑文件: $ENV_FILE"
        echo "设置: OPENROUTER_API_KEY=your_actual_api_key"
    else
        echo "✅ OPENROUTER_API_KEY 已设置"
    fi
else
    echo "⚠️  .env 文件中缺少 OPENROUTER_API_KEY 配置"
    echo "OPENROUTER_API_KEY=your_openrouter_api_key_here" >> "$ENV_FILE"
    echo "✅ 已添加 OPENROUTER_API_KEY 配置到 .env 文件"
fi

# 检查是否存在旧的 OPENAI_API_KEY 配置
if grep -q "OPENAI_API_KEY=" "$ENV_FILE"; then
    echo "⚠️  发现旧的 OPENAI_API_KEY 配置，建议删除或注释"
    echo "请检查文件: $ENV_FILE"
fi

echo ""
echo "🐳 Docker 容器重启建议..."
echo "如果容器正在运行，请重启以加载新的环境变量:"
echo ""
echo "# 停止容器"
echo "docker-compose -f $SCRIPT_DIR/docker-compose.yml down"
echo ""
echo "# 重新启动容器"
echo "docker-compose -f $SCRIPT_DIR/docker-compose.yml up -d"
echo ""
echo "# 查看应用日志"
echo "docker-compose -f $SCRIPT_DIR/docker-compose.yml logs -f app"

echo ""
echo "🔍 环境变量验证..."
echo "容器启动后，可以使用以下命令验证环境变量:"
echo ""
echo "# 检查容器内环境变量"
echo "docker exec contractshield-app env | grep OPENROUTER_API_KEY"
echo ""
echo "# 检查应用健康状态"
echo "curl http://localhost:8000/health"

echo ""
echo "✅ 环境变量修复脚本执行完成"
echo "请按照上述建议设置 API Key 并重启容器"