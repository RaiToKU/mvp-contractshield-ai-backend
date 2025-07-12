#!/usr/bin/env python3
"""查询用户脚本"""

from app.database import SessionLocal
from app.models import User

def query_users():
    """查询所有用户"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f'用户总数: {len(users)}')
        for user in users:
            print(f'用户ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}')
    except Exception as e:
        print(f'查询用户失败: {e}')
    finally:
        db.close()

if __name__ == "__main__":
    query_users()