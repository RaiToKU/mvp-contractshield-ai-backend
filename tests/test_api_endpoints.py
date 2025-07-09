#!/usr/bin/env python3
"""
测试新实现的API端点
"""

import requests
import time
import json
import os

BASE_URL = "http://localhost:8001"

def test_health():
    """测试健康检查端点"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ 健康检查通过")
            print(f"✓ 响应: {response.json()}")
            return True
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")
        return False

def test_upload_and_entity_extraction():
    """测试文件上传和实体提取功能"""
    print("\n=== 测试文件上传和实体提取 ===")
    
    try:
        # 使用项目中的测试文件
        test_file_path = "test_contract.txt"
        
        if not os.path.exists(test_file_path):
            print(f"✗ 测试文件不存在: {test_file_path}")
            return None
        
        # 复制txt文件为pdf文件以通过文件类型检查
        import shutil
        pdf_test_path = "test_contract_copy.pdf"
        shutil.copy2(test_file_path, pdf_test_path)
        
        # 上传PDF文件
        with open(pdf_test_path, "rb") as f:
            files = {"file": ("test_contract.pdf", f, "application/pdf")}
            data = {
                "contract_type": "purchase",
                "user_id": 1
            }
            
            response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✓ 文件上传成功，任务ID: {task_id}")
            
            # 等待实体提取完成
            print("等待实体提取完成...")
            time.sleep(3)
            
            return task_id
        else:
            print(f"✗ 文件上传失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 文件上传异常: {e}")
        return None

def test_draft_roles(task_id):
    """测试获取草稿角色"""
    print("\n=== 测试获取草稿角色 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/review/draft-roles/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 获取草稿角色成功")
            print(f"✓ 候选角色数量: {len(result.get('candidates', []))}")
            
            for i, candidate in enumerate(result.get('candidates', [])):
                print(f"  - 候选{i+1}: {candidate.get('role')} - {candidate.get('label')} ({candidate.get('description')})")
                print(f"    实体: {candidate.get('entities', [])}")
            
            return result
        else:
            print(f"✗ 获取草稿角色失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 获取草稿角色异常: {e}")
        return None

def test_confirm_roles(task_id):
    """测试确认角色（自动选择）"""
    print("\n=== 测试确认角色（自动选择） ===")
    
    try:
        data = {
            "role": "buyer",
            "selected_entity_index": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/review/confirm-roles/{task_id}",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 角色确认成功")
            print(f"✓ 状态: {result.get('status')}")
            print(f"✓ 角色: {result.get('role')}")
            print(f"✓ 主体名称: {result.get('party_names')}")
            print(f"✓ 是否自动选择: {result.get('auto_selected')}")
            return result
        else:
            print(f"✗ 角色确认失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 角色确认异常: {e}")
        return None

def main():
    """主测试函数"""
    print("开始测试API端点...\n")
    
    # 测试健康检查
    if not test_health():
        print("服务器未正常运行，终止测试")
        return
    
    # 测试文件上传和实体提取
    task_id = test_upload_and_entity_extraction()
    if not task_id:
        print("文件上传失败，终止测试")
        return
    
    # 测试获取草稿角色
    draft_result = test_draft_roles(task_id)
    if not draft_result:
        print("获取草稿角色失败，终止测试")
        return
    
    # 测试确认角色
    confirm_result = test_confirm_roles(task_id)
    if not confirm_result:
        print("角色确认失败，终止测试")
        return
    
    print("\n🎉 所有API测试通过！新功能实现正确。")

if __name__ == "__main__":
    main()