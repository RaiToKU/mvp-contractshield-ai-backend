#!/usr/bin/env python3
"""检查数据库状态和迁移版本"""

import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

def check_database_status():
    load_dotenv()
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://contractshield:contractshield123@localhost:5432/contractshield')
    
    try:
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        # 检查表
        tables = inspector.get_table_names()
        print('数据库中的表:', tables)
        
        # 检查tasks表结构
        if 'tasks' in tables:
            columns = inspector.get_columns('tasks')
            print('\ntasks表的列:')
            for col in columns:
                print(f'  {col["name"]}: {col["type"]} (nullable: {col["nullable"]})')
        
        # 检查Alembic版本
        if 'alembic_version' in tables:
            with engine.connect() as conn:
                result = conn.execute(text('SELECT version_num FROM alembic_version'))
                version = result.fetchone()
                print(f'\n当前Alembic版本: {version[0] if version else "未找到"}')
        else:
            print('\n未找到alembic_version表')
            
        # 检查用户数据
        if 'users' in tables:
            with engine.connect() as conn:
                result = conn.execute(text('SELECT id, username, email FROM users'))
                users = result.fetchall()
                print(f'\n用户数据:')
                for user in users:
                    print(f'  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}')
                    
    except Exception as e:
        print(f'数据库检查失败: {e}')

if __name__ == "__main__":
    check_database_status()