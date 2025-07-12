#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from database import test_connection, DATABASE_URL
    
    print(f"正在测试数据库连接...")
    print(f"数据库URL: {DATABASE_URL}")
    
    # 测试连接
    if test_connection():
        print("✅ 数据库连接成功！")
    else:
        print("❌ 数据库连接失败！")
        
except Exception as e:
    print(f"❌ 连接测试出错: {e}")
    import traceback
    traceback.print_exc()