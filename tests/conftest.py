import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models import User, Task, File, Role, Paragraph, Risk, Statute

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app=app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """创建示例用户"""
    user = User(
        username="testuser",
        email="test@example.com"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_task(db_session, sample_user):
    """创建示例任务"""
    task = Task(
        user_id=sample_user.id,
        contract_type="purchase",
        status="pending"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def sample_file(db_session, sample_task):
    """创建示例文件"""
    file = File(
        task_id=sample_task.id,
        filename="test_contract.pdf",
        path="/test/path/test_contract.pdf",
        file_type="pdf",
        ocr_text="测试OCR文本内容"
    )
    db_session.add(file)
    db_session.commit()
    db_session.refresh(file)
    return file


@pytest.fixture
def sample_role(db_session, sample_task):
    """创建示例角色"""
    role = Role(
        task_id=sample_task.id,
        role_key="buyer",
        party_names=["Test Company"]
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def sample_paragraph(db_session, sample_task):
    """创建示例段落"""
    paragraph = Paragraph(
        task_id=sample_task.id,
        text="这是一个测试段落内容",
        paragraph_index=1,
        embedding=[0.1] * 1536  # 模拟embedding向量
    )
    db_session.add(paragraph)
    db_session.commit()
    db_session.refresh(paragraph)
    return paragraph


@pytest.fixture
def sample_risk(db_session, sample_task):
    """创建示例风险"""
    risk = Risk(
        task_id=sample_task.id,
        clause_id="第1条",
        title="付款风险",
        risk_level="HIGH",
        summary="测试风险描述",
        suggestion="测试建议",
        paragraph_refs=[1]
    )
    db_session.add(risk)
    db_session.commit()
    db_session.refresh(risk)
    return risk


@pytest.fixture
def sample_statute(db_session, sample_risk):
    """创建示例法规"""
    statute = Statute(
        risk_id=sample_risk.id,
        statute_ref="测试法规条文",
        statute_text="测试法规内容"
    )
    db_session.add(statute)
    db_session.commit()
    db_session.refresh(statute)
    return statute


@pytest.fixture
def ai_service():
    """创建AI服务实例"""
    from unittest.mock import patch
    from app.services.ai_service import AIService
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
        return AIService()


# 测试数据
SAMPLE_CONTRACT_TEXT = """
合同编号：TEST-001

甲方：测试公司A
乙方：测试公司B

第一条 合同标的
本合同标的为软件开发服务。

第二条 价款及支付方式
合同总价为人民币100万元，分三期支付。

第三条 违约责任
任何一方违约，应承担违约责任。
"""

SAMPLE_UPLOAD_FILE = {
    "filename": "test_contract.pdf",
    "content": b"PDF content here",
    "content_type": "application/pdf"
}