-- 数据库用户初始化脚本
-- 使用最简单可靠的方式创建用户

-- 删除用户（如果存在）
DROP USER IF EXISTS contractshield;

-- 创建用户
CREATE USER contractshield WITH PASSWORD 'contractshield123';

-- 授予数据库权限
GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
ALTER USER contractshield CREATEDB;

-- 授予 schema 权限
GRANT ALL ON SCHEMA public TO contractshield;
GRANT CREATE ON SCHEMA public TO contractshield;
GRANT USAGE ON SCHEMA public TO contractshield;

-- 授予现有对象权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO contractshield;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO contractshield;

-- 验证用户创建
SELECT 'User contractshield created successfully' as status;