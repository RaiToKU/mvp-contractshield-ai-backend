#!/usr/bin/env python3

from app.database import SessionLocal
from app.models import Task, ReviewResult
from sqlalchemy.orm import joinedload

def check_task_33():
    """检查任务33的状态和报告生成情况"""
    db = SessionLocal()
    try:
        # 查询任务33
        task = db.query(Task).filter(Task.id == 33).first()
        
        if not task:
            print("❌ 任务33不存在")
            return
        
        print(f"📋 任务33基本信息:")
        print(f"   状态: {task.status}")
        print(f"   合同类型: {task.contract_type}")
        print(f"   角色: {task.role}")
        print(f"   创建时间: {task.created_at}")
        print(f"   更新时间: {task.updated_at}")
        
        # 查询审查结果
        review_result = db.query(ReviewResult).filter(ReviewResult.task_id == 33).first()
        
        if review_result:
            print(f"\n📊 审查结果:")
            print(f"   结果状态: 存在")
            print(f"   创建时间: {review_result.created_at}")
            print(f"   摘要长度: {len(review_result.summary) if review_result.summary else 0} 字符")
            print(f"   风险数量: {len(review_result.risks) if review_result.risks else 0} 项")
        else:
            print(f"\n❌ 未找到审查结果")
        
        # 检查导出文件
        import os
        import glob
        export_dir = "exports"
        if os.path.exists(export_dir):
            pattern = os.path.join(export_dir, f"contract_review_33_*")
            files = glob.glob(pattern)
            if files:
                print(f"\n📄 导出文件:")
                for file in files:
                    file_size = os.path.getsize(file)
                    print(f"   {os.path.basename(file)} ({file_size} bytes)")
            else:
                print(f"\n❌ 未找到导出文件")
        else:
            print(f"\n❌ 导出目录不存在")
            
    except Exception as e:
        print(f"❌ 查询出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_task_33()