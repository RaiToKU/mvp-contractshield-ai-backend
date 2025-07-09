#!/usr/bin/env python3
"""
初始化数据库
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import Base

def init_database():
    """初始化数据库"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✓ 数据库初始化完成")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✓ 创建的表: {tables}")
        
        # 检查tasks表的字段
        if 'tasks' in tables:
            columns = inspector.get_columns('tasks')
            column_names = [col['name'] for col in columns]
            print(f"✓ tasks表字段: {column_names}")
            
            # 检查新字段是否存在
            if 'entities_data' in column_names:
                print("✓ entities_data字段已存在")
            else:
                print("⚠ entities_data字段不存在")
                
            if 'entities_extracted_at' in column_names:
                print("✓ entities_extracted_at字段已存在")
            else:
                print("⚠ entities_extracted_at字段不存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    print("开始初始化数据库...")
    if init_database():
        print("数据库初始化成功！")
    else:
        print("数据库初始化失败！")