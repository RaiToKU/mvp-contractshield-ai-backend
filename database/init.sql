-- 初始化数据库脚本
-- 创建PGVector扩展

-- 确保以超级用户身份执行
-- 创建 vector 扩展
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE EXTENSION vector;
        RAISE NOTICE 'pgvector extension created successfully';
    ELSE
        RAISE NOTICE 'pgvector extension already exists';
    END IF;
END
$$;

-- 创建 uuid-ossp 扩展（可选，用于生成UUID）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        CREATE EXTENSION "uuid-ossp";
        RAISE NOTICE 'uuid-ossp extension created successfully';
    ELSE
        RAISE NOTICE 'uuid-ossp extension already exists';
    END IF;
END
$$;

-- 验证扩展安装
DO $$
BEGIN
    -- 测试向量类型
    PERFORM '[1,2,3]'::vector;
    RAISE NOTICE 'Vector type test passed';
    
    -- 测试向量操作
    PERFORM '[1,2,3]'::vector <-> '[1,2,4]'::vector;
    RAISE NOTICE 'Vector distance operation test passed';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'pgvector extension test failed: %', SQLERRM;
END
$$;

-- 设置数据库参数优化向量操作
-- 注意：这些设置需要重启数据库才能生效
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- 重新加载配置（部分参数立即生效）
SELECT pg_reload_conf();

-- 显示安装结果
SELECT 
    'pgvector extension initialized successfully!' as message,
    extversion as version
FROM pg_extension 
WHERE extname = 'vector';

-- 显示数据库信息
SELECT 
    current_database() as database_name,
    current_user as current_user,
    version() as postgresql_version;