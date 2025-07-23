-- 创建缺失表的完整迁移脚本
-- 执行时间：需要在线上数据库执行

-- 1. 创建users表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- 2. 创建files表（如果不存在）
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    path VARCHAR(500),
    file_type VARCHAR(10),
    ocr_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_files_id ON files(id);
CREATE INDEX IF NOT EXISTS ix_files_task_id ON files(task_id);

-- 3. 创建roles表（如果不存在）
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    role_key VARCHAR(50),
    party_names JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_roles_id ON roles(id);
CREATE INDEX IF NOT EXISTS ix_roles_task_id ON roles(task_id);

-- 4. 创建paragraphs表（如果不存在）
CREATE TABLE IF NOT EXISTS paragraphs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    text TEXT,
    embedding vector(1536),
    paragraph_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_paragraphs_id ON paragraphs(id);
CREATE INDEX IF NOT EXISTS ix_paragraphs_task_id ON paragraphs(task_id);
CREATE INDEX IF NOT EXISTS idx_paragraphs_embedding ON paragraphs 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 5. 创建risks表（如果不存在）
CREATE TABLE IF NOT EXISTS risks (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    clause_id VARCHAR(50),
    title VARCHAR(200),
    risk_level VARCHAR(20),
    summary TEXT,
    suggestion TEXT,
    paragraph_refs JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_risks_id ON risks(id);
CREATE INDEX IF NOT EXISTS ix_risks_task_id ON risks(task_id);

-- 6. 创建statutes表（如果不存在）
CREATE TABLE IF NOT EXISTS statutes (
    id SERIAL PRIMARY KEY,
    risk_id INTEGER REFERENCES risks(id) ON DELETE CASCADE,
    statute_ref VARCHAR(200),
    statute_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_statutes_id ON statutes(id);
CREATE INDEX IF NOT EXISTS ix_statutes_risk_id ON statutes(risk_id);

-- 授予contractshield用户对新表的权限
DO $$
BEGIN
    -- 授予对所有表的权限
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
    
    -- 特别授予对新表的权限
    GRANT ALL ON users TO contractshield;
    GRANT ALL ON files TO contractshield;
    GRANT ALL ON roles TO contractshield;
    GRANT ALL ON paragraphs TO contractshield;
    GRANT ALL ON risks TO contractshield;
    GRANT ALL ON statutes TO contractshield;
    
    -- 授予对序列的权限
    GRANT ALL ON users_id_seq TO contractshield;
    GRANT ALL ON files_id_seq TO contractshield;
    GRANT ALL ON roles_id_seq TO contractshield;
    GRANT ALL ON paragraphs_id_seq TO contractshield;
    GRANT ALL ON risks_id_seq TO contractshield;
    GRANT ALL ON statutes_id_seq TO contractshield;
    
    RAISE NOTICE 'All new table permissions granted to contractshield user';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Could not grant table permissions: %', SQLERRM;
END
$$;

-- 验证所有表是否创建成功
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'files', 'roles', 'paragraphs', 'risks', 'statutes')
ORDER BY table_name;