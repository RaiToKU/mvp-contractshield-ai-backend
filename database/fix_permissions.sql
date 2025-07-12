-- 权限修复脚本
-- 确保 contractshield 用户拥有所有必要权限

-- 确保用户存在并设置正确密码
ALTER USER contractshield WITH PASSWORD 'contractshield123';

-- 重新授予所有权限
GRANT ALL PRIVILEGES ON DATABASE contractshield TO contractshield;
GRANT ALL ON SCHEMA public TO contractshield;
GRANT CREATE ON SCHEMA public TO contractshield;
GRANT USAGE ON SCHEMA public TO contractshield;

-- 授予所有现有对象的权限
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO contractshield;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO contractshield;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contractshield;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO contractshield;

-- 显示权限修复结果
SELECT 'Permissions fixed for contractshield user' as status;