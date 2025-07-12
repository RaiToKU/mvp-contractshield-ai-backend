-- 数据库表结构修复脚本
-- 修复tasks表缺少user_id列的问题

-- 1. 创建users表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建默认用户
INSERT INTO users (username, email) 
VALUES ('default_user', 'default@example.com')
ON CONFLICT (username) DO NOTHING;

-- 3. 添加user_id列到tasks表
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id INTEGER DEFAULT 1;

-- 4. 添加外键约束（如果列已存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'tasks_user_id_fkey'
    ) THEN
        ALTER TABLE tasks ADD CONSTRAINT tasks_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id);
    END IF;
END $$;

-- 5. 更新现有记录的user_id
UPDATE tasks SET user_id = 1 WHERE user_id IS NULL;

-- 6. 添加其他缺失的列
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS role VARCHAR(50);
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS entities_data JSON;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS entities_extracted_at TIMESTAMP;

-- 7. 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);

-- 显示修复结果
\d tasks;