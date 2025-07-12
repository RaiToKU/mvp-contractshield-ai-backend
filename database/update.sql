-- ContractShield AI 数据库更新脚本
-- 版本: v1.1
-- 更新时间: 2024-01-02

-- 在这里添加数据库结构更新的 SQL 语句

-- 示例：添加新字段
-- ALTER TABLE tasks ADD COLUMN IF NOT EXISTS new_field VARCHAR(100);

-- 示例：创建新表
-- CREATE TABLE IF NOT EXISTS new_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- 示例：创建新索引
-- CREATE INDEX IF NOT EXISTS idx_new_field ON tasks(new_field);

-- 示例：更新数据
-- UPDATE tasks SET status = 'pending' WHERE status = 'uploaded';

-- 记录更新日志
INSERT INTO review_history (task_id, step_name, step_result, step_status) 
VALUES (0, 'database_update', '{"version": "v1.1", "description": "数据库结构更新"}', 'completed')
ON CONFLICT DO NOTHING;

-- 显示更新完成信息
SELECT 
    'Database update completed!' as message,
    'v1.1' as version,
    current_timestamp as updated_at;

COMMIT;