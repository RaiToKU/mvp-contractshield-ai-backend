-- 为tasks表添加缺失字段的完整迁移脚本
-- 执行时间：需要在线上数据库执行

-- 1. 添加user_id字段，允许为NULL
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- 2. 添加role字段，允许为NULL
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS role VARCHAR(50);

-- 3. 添加entities_data字段，允许为NULL
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS entities_data JSONB;

-- 4. 添加entities_extracted_at字段，允许为NULL
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS entities_extracted_at TIMESTAMP;

-- 添加注释说明
COMMENT ON COLUMN tasks.user_id IS '用户ID，允许为NULL，为后续账号体系预留';
COMMENT ON COLUMN tasks.role IS '用户角色，如buyer、seller等';
COMMENT ON COLUMN tasks.entities_data IS '存储提取的实体数据';
COMMENT ON COLUMN tasks.entities_extracted_at IS '实体提取时间';

-- 验证所有字段是否添加成功
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'tasks' 
AND column_name IN ('user_id', 'role', 'entities_data', 'entities_extracted_at')
ORDER BY column_name;