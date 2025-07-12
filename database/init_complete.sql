-- ContractShield AI 数据库初始化脚本
-- 版本: v1.0
-- 创建时间: 2024-01-01

-- 创建数据库（如果不存在）
-- CREATE DATABASE contractshield;

-- 连接到数据库
-- \c contractshield;

-- 确保 contractshield 用户有足够的权限
DO $$
BEGIN
    -- 确保用户对 public schema 有完整权限
    GRANT ALL ON SCHEMA public TO contractshield;
    GRANT CREATE ON SCHEMA public TO contractshield;
    GRANT USAGE ON SCHEMA public TO contractshield;
    
    -- 确保对现有对象的权限
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO contractshield;
    
    RAISE NOTICE 'Permissions verified for contractshield user';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Could not set permissions: %', SQLERRM;
END
$$;

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    contract_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'uploaded',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_text TEXT,
    parties JSONB,
    user_role VARCHAR(50),
    user_party_names JSONB,
    review_result JSONB,
    progress INTEGER DEFAULT 0,
    error_message TEXT
);

-- 创建文档块表（用于向量检索）
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建审查历史表
CREATE TABLE IF NOT EXISTS review_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    step_name VARCHAR(100) NOT NULL,
    step_result JSONB,
    step_status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建导出记录表
CREATE TABLE IF NOT EXISTS export_records (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    export_format VARCHAR(20) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_task_id ON document_chunks(task_id);
CREATE INDEX IF NOT EXISTS idx_review_history_task_id ON review_history(task_id);
CREATE INDEX IF NOT EXISTS idx_export_records_task_id ON export_records(task_id);

-- 创建向量索引（提高检索性能）
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 tasks 表创建更新时间触发器
DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 优化数据库配置（用于向量操作）
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- 重新加载配置
SELECT pg_reload_conf();

-- 确保 contractshield 用户对所有新创建的表有权限
DO $$
BEGIN
    -- 授予对所有表的权限
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO contractshield;
    
    -- 特别授予对主要表的权限
    GRANT ALL ON tasks TO contractshield;
    GRANT ALL ON document_chunks TO contractshield;
    GRANT ALL ON review_history TO contractshield;
    GRANT ALL ON export_records TO contractshield;
    
    -- 授予对序列的权限
    GRANT ALL ON tasks_id_seq TO contractshield;
    GRANT ALL ON document_chunks_id_seq TO contractshield;
    GRANT ALL ON review_history_id_seq TO contractshield;
    GRANT ALL ON export_records_id_seq TO contractshield;
    
    RAISE NOTICE 'All table permissions granted to contractshield user';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Could not grant table permissions: %', SQLERRM;
END
$$;

-- 插入初始数据（可选）
-- INSERT INTO tasks (file_name, file_path, file_type, contract_type, status) 
-- VALUES ('示例合同.pdf', '/app/uploads/example.pdf', 'pdf', '采购合同', 'uploaded');

-- 显示创建的表
\dt

-- 显示数据库信息
SELECT 
    'Database initialized successfully!' as message,
    current_database() as database_name,
    current_timestamp as initialized_at;

COMMIT;