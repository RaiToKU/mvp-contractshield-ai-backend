#!/usr/bin/env python3
"""
ContractShield AI Backend 启动脚本

使用方法:
    python run.py
    
或者使用uvicorn直接运行:
    uvicorn run:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"Starting ContractShield AI Backend...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"Health: http://{host}:{port}/health")
    
    uvicorn.run(
        "run:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info",
        access_log=True
    )