#!/usr/bin/env python3
"""
手动更新数据库结构，添加新字段
"""

import sqlite3
import os

def update_database():
    """更新数据库结构"""
    db_path = 'contractshield.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"当前tasks表字段: {columns}")
        
        # 添加entities_data字段
        if 'entities_data' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN entities_data TEXT")
            print("✓ 添加entities_data字段成功")
        else:
            print("entities_data字段已存在")
        
        # 添加entities_extracted_at字段
        if 'entities_extracted_at' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN entities_extracted_at TIMESTAMP")
            print("✓ 添加entities_extracted_at字段成功")
        else:
            print("entities_extracted_at字段已存在")
        
        conn.commit()
        
        # 验证更新
        cursor.execute("PRAGMA table_info(tasks)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"更新后tasks表字段: {new_columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"更新数据库失败: {e}")
        return False

if __name__ == "__main__":
    print("开始更新数据库结构...")
    if update_database():
        print("数据库更新完成！")
    else:
        print("数据库更新失败！")