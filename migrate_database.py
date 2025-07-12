#!/usr/bin/env python3
"""
数据库表结构迁移脚本
将旧的表结构迁移到新的模型定义
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def migrate_database():
    """迁移数据库表结构"""
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://contractshield:contractshield123@localhost:5432/contractshield")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 检查当前表结构
            inspector = inspect(engine)
            
            # 检查tasks表是否存在user_id列
            tasks_columns = [col['name'] for col in inspector.get_columns('tasks')]
            logger.info(f"当前tasks表列: {tasks_columns}")
            
            if 'user_id' not in tasks_columns:
                logger.info("添加user_id列到tasks表...")
                
                # 首先创建users表（如果不存在）
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE,
                        email VARCHAR(100) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # 创建默认用户
                conn.execute(text("""
                    INSERT INTO users (username, email) 
                    VALUES ('default_user', 'default@example.com')
                    ON CONFLICT (username) DO NOTHING;
                """))
                
                # 添加user_id列到tasks表
                conn.execute(text("""
                    ALTER TABLE tasks 
                    ADD COLUMN IF NOT EXISTS user_id INTEGER 
                    REFERENCES users(id) DEFAULT 1;
                """))
                
                # 更新现有记录的user_id
                conn.execute(text("""
                    UPDATE tasks SET user_id = 1 WHERE user_id IS NULL;
                """))
                
                logger.info("✅ user_id列添加成功")
            
            # 检查并添加其他缺失的列
            required_columns = {
                'role': 'VARCHAR(50)',
                'entities_data': 'JSON',
                'entities_extracted_at': 'TIMESTAMP'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in tasks_columns:
                    logger.info(f"添加{col_name}列...")
                    conn.execute(text(f"""
                        ALTER TABLE tasks 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                    """))
                    logger.info(f"✅ {col_name}列添加成功")
            
            # 检查并创建其他必要的表
            tables = inspector.get_table_names()
            
            if 'files' not in tables:
                logger.info("创建files表...")
                conn.execute(text("""
                    CREATE TABLE files (
                        id SERIAL PRIMARY KEY,
                        task_id INTEGER REFERENCES tasks(id),
                        filename VARCHAR(255),
                        path VARCHAR(500),
                        file_type VARCHAR(10),
                        ocr_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ files表创建成功")
            
            if 'roles' not in tables:
                logger.info("创建roles表...")
                conn.execute(text("""
                    CREATE TABLE roles (
                        id SERIAL PRIMARY KEY,
                        task_id INTEGER REFERENCES tasks(id),
                        role_key VARCHAR(50),
                        party_names JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ roles表创建成功")
            
            if 'paragraphs' not in tables:
                logger.info("创建paragraphs表...")
                conn.execute(text("""
                    CREATE TABLE paragraphs (
                        id SERIAL PRIMARY KEY,
                        task_id INTEGER REFERENCES tasks(id),
                        text TEXT,
                        embedding vector(1536),
                        paragraph_index INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ paragraphs表创建成功")
            
            if 'risks' not in tables:
                logger.info("创建risks表...")
                conn.execute(text("""
                    CREATE TABLE risks (
                        id SERIAL PRIMARY KEY,
                        task_id INTEGER REFERENCES tasks(id),
                        clause_id VARCHAR(50),
                        title VARCHAR(200),
                        risk_level VARCHAR(20),
                        summary TEXT,
                        suggestion TEXT,
                        paragraph_refs JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ risks表创建成功")
            
            if 'statutes' not in tables:
                logger.info("创建statutes表...")
                conn.execute(text("""
                    CREATE TABLE statutes (
                        id SERIAL PRIMARY KEY,
                        risk_id INTEGER REFERENCES risks(id),
                        statute_ref VARCHAR(200),
                        statute_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                logger.info("✅ statutes表创建成功")
            
            # 提交所有更改
            conn.commit()
            logger.info("🎉 数据库迁移完成！")
            
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        raise

if __name__ == "__main__":
    migrate_database()