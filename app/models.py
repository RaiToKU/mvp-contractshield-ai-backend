from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    tasks = relationship("Task", back_populates="user")

class Task(Base):
    """审查任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="PENDING")  # PENDING, EXTRACTING, ENTITY_READY, READY, IN_PROGRESS, COMPLETED, FAILED
    contract_type = Column(String(50))
    role = Column(String(50))  # buyer, seller, etc.
    entities_data = Column(JSON)  # 存储提取的实体数据
    entities_extracted_at = Column(TIMESTAMP)  # 实体提取时间
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="tasks")
    files = relationship("File", back_populates="task")
    roles = relationship("Role", back_populates="task")
    paragraphs = relationship("Paragraph", back_populates="task")
    risks = relationship("Risk", back_populates="task")

class File(Base):
    """文件表"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    filename = Column(String(255))
    path = Column(String(500))
    file_type = Column(String(10))  # pdf, docx, etc.
    ocr_text = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="files")

class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    role_key = Column(String(50))  # buyer, seller, etc.
    party_names = Column(JSON)  # JSON数组存储主体名称
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="roles")

class Paragraph(Base):
    """段落表"""
    __tablename__ = "paragraphs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    text = Column(Text)
    embedding = Column(Vector(1536))  # OpenAI embedding维度
    paragraph_index = Column(Integer)  # 段落在文档中的顺序
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="paragraphs")

class Risk(Base):
    """风险表"""
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    clause_id = Column(String(50))  # 条款编号
    title = Column(String(200))  # 风险标题
    risk_level = Column(String(20))  # HIGH, MEDIUM, LOW
    summary = Column(Text)  # 风险摘要
    suggestion = Column(Text)  # 建议
    paragraph_refs = Column(JSON)  # 关联的段落ID列表
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="risks")
    statutes = relationship("Statute", back_populates="risk")

class Statute(Base):
    """法规引用表"""
    __tablename__ = "statutes"
    
    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"))
    statute_ref = Column(String(200))  # 法规引用
    statute_text = Column(Text)  # 法规条文
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # 关系
    risk = relationship("Risk", back_populates="statutes")