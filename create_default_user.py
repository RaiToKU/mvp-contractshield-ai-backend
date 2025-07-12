#!/usr/bin/env python3
"""创建默认用户脚本"""

from app.database import SessionLocal
from app.models import User

def create_default_user():
    """创建默认用户"""
    db = SessionLocal()
    try:
        # 检查是否已存在用户
        existing_user = db.query(User).filter(User.id == 1).first()
        if not existing_user:
            # 创建默认用户
            default_user = User(
                id=1,
                username='default_user',
                email='default@example.com'
            )
            db.add(default_user)
            db.commit()
            print('默认用户创建成功')
        else:
            print('默认用户已存在')
    except Exception as e:
        print(f'创建用户失败: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_user()