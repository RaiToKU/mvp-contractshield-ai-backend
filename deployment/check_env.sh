#!/bin/bash

echo "🔍 检查 OPENROUTER_API_KEY 环境变量配置"
echo "========================================"

# 检查 .env 文件
if [ -f ".env" ]; then
    echo "✅ 找到 .env 文件"
    if grep -q "OPENROUTER_API_KEY" .env; then
        echo "✅ .env 文件包含 OPENROUTER_API_KEY"
        grep "OPENROUTER_API_KEY" .env
    else
        echo "❌ .env 文件缺少 OPENROUTER_API_KEY"
    fi
else
    echo "❌ 未找到 .env 文件"
fi

echo ""
echo "🐳 检查 Docker 容器状态"
echo "========================"

# 检查容器是否运行
if docker ps | grep -q "contractshield-app"; then
    echo "✅ contractshield-app 容器正在运行"
    
    echo ""
    echo "🔍 检查容器内环境变量"
    echo "===================="
    docker exec contractshield-app env | grep -E "(OPENROUTER|OPENAI)" || echo "❌ 未找到相关 API Key 环境变量"
    
    echo ""
    echo "📋 最近的应用日志"
    echo "================"
    docker logs contractshield-app --tail 10
else
    echo "❌ contractshield-app 容器未运行"
    echo ""
    echo "📋 所有容器状态"
    echo "=============="
    docker ps -a | grep contractshield
fi