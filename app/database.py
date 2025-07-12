from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import os
import time
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/contractshield")

# 创建引擎，增加连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # 设置为 True 可以看到 SQL 查询日志
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection(max_retries=5, retry_delay=2):
    """测试数据库连接，带重试机制"""
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                logger.info("数据库连接测试成功")
                return True
        except OperationalError as e:
            logger.warning(f"数据库连接尝试 {attempt + 1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("数据库连接失败，已达到最大重试次数")
                raise
    return False

def init_db():
    """初始化数据库，创建表和启用PGVector扩展"""
    try:
        # 首先测试连接
        test_connection()
        
        # 启用PGVector扩展
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("PGVector 扩展已启用")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise