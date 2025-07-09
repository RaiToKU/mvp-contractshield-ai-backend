#!/usr/bin/env python3
"""
测试新实现的实体数据存储和角色确认功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import Task, Role
from app.services.review_service import ReviewService
from app.database import SessionLocal
from datetime import datetime
import json

def test_entities_storage():
    """测试实体数据存储功能"""
    print("=== 测试实体数据存储功能 ===")
    
    db = SessionLocal()
    try:
        # 创建测试任务
        test_task = Task(
            user_id=1,
            contract_type="purchase",
            status="UPLOADED",
            entities_data={
                "companies": ["测试公司A", "测试公司B", "供应商C"],
                "persons": ["张三", "李四"],
                "organizations": ["政府机构"]
            },
            entities_extracted_at=datetime.utcnow()
        )
        
        db.add(test_task)
        db.commit()
        db.refresh(test_task)
        
        print(f"✓ 任务创建成功，ID: {test_task.id}")
        print(f"✓ 实体数据: {test_task.entities_data}")
        print(f"✓ 提取时间: {test_task.entities_extracted_at}")
        
        return test_task.id
        
    except Exception as e:
        print(f"✗ 实体数据存储测试失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_confirm_roles_with_auto_selection(task_id):
    """测试角色确认的自动选择功能"""
    print("\n=== 测试角色确认自动选择功能 ===")
    
    try:
        review_service = ReviewService()
        
        # 测试自动选择第一个公司实体
        result = review_service.confirm_roles(
            task_id=task_id,
            role="buyer",
            party_names=None,
            selected_entity_index=0
        )
        
        print(f"✓ 角色确认成功")
        print(f"✓ 状态: {result['status']}")
        print(f"✓ 角色: {result['role']}")
        print(f"✓ 自动选择的主体: {result['party_names']}")
        print(f"✓ 是否自动选择: {result.get('auto_selected', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 角色确认测试失败: {e}")
        return False

def test_get_draft_roles(task_id):
    """测试获取草稿角色功能"""
    print("\n=== 测试获取草稿角色功能 ===")
    
    try:
        review_service = ReviewService()
        
        result = review_service.get_draft_roles(task_id)
        
        print(f"✓ 获取草稿角色成功")
        print(f"✓ 候选角色数量: {len(result['candidates'])}")
        print(f"✓ 实体数据: {result.get('entities', {})}")
        
        for i, candidate in enumerate(result['candidates']):
            print(f"  - 候选{i+1}: {candidate['role']} ({candidate['description']})")
        
        return True
        
    except Exception as e:
        print(f"✗ 获取草稿角色测试失败: {e}")
        return False

def cleanup_test_data(task_id):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    
    db = SessionLocal()
    try:
        # 删除角色记录
        db.query(Role).filter(Role.task_id == task_id).delete()
        
        # 删除任务记录
        db.query(Task).filter(Task.id == task_id).delete()
        
        db.commit()
        print("✓ 测试数据清理完成")
        
    except Exception as e:
        print(f"✗ 清理测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """主测试函数"""
    print("开始测试新实现的功能...\n")
    
    # 测试实体数据存储
    task_id = test_entities_storage()
    if not task_id:
        print("实体数据存储测试失败，终止测试")
        return
    
    # 测试获取草稿角色
    if not test_get_draft_roles(task_id):
        cleanup_test_data(task_id)
        return
    
    # 测试角色确认
    if not test_confirm_roles_with_auto_selection(task_id):
        cleanup_test_data(task_id)
        return
    
    # 清理测试数据
    cleanup_test_data(task_id)
    
    print("\n🎉 所有测试通过！新功能实现正确。")

if __name__ == "__main__":
    main()