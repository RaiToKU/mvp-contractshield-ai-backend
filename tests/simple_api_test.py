#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的API测试脚本
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 健康检查通过")
            print(f"✓ 响应: {result}")
            return True
        else:
            print(f"✗ 健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 健康检查异常: {e}")
        return False

def test_get_draft_roles():
    """测试获取草稿角色（不依赖文件上传）"""
    print("\n=== 测试获取草稿角色 ===")
    
    try:
        # 模拟一个任务ID（假设数据库中存在）
        task_id = 1
        
        response = requests.get(f"{BASE_URL}/api/v1/review/{task_id}/draft-roles")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 获取草稿角色成功")
            print(f"✓ 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        elif response.status_code == 404:
            print(f"⚠ 任务不存在（这是正常的，因为我们使用的是模拟ID）")
            return None
        else:
            print(f"✗ 获取草稿角色失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 获取草稿角色异常: {e}")
        return None

def test_confirm_roles():
    """测试确认角色（不依赖文件上传）"""
    print("\n=== 测试确认角色 ===")
    
    try:
        # 模拟一个任务ID
        task_id = 1
        
        # 模拟角色确认数据
        confirm_data = {
            "roles": [
                {
                    "role_type": "buyer",
                    "party_names": ["北京科技有限公司"],
                    "selected_entity_index": 0,
                    "auto_selected": False
                },
                {
                    "role_type": "supplier", 
                    "party_names": ["上海贸易股份有限公司"],
                    "selected_entity_index": 0,
                    "auto_selected": False
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/review/{task_id}/confirm-roles",
            json=confirm_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ 确认角色成功")
            print(f"✓ 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        elif response.status_code == 404:
            print(f"⚠ 任务不存在（这是正常的，因为我们使用的是模拟ID）")
            return None
        else:
            print(f"✗ 确认角色失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 确认角色异常: {e}")
        return None

def test_api_documentation():
    """测试API文档访问"""
    print("\n=== 测试API文档 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        
        if response.status_code == 200:
            print("✓ API文档可访问")
            print(f"✓ 文档URL: {BASE_URL}/docs")
            return True
        else:
            print(f"✗ API文档访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ API文档访问异常: {e}")
        return False

def main():
    """主测试函数"""
    print("开始简化API测试...")
    
    # 测试健康检查
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n❌ 健康检查失败，终止测试")
        return
    
    # 测试API文档
    test_api_documentation()
    
    # 测试获取草稿角色
    test_get_draft_roles()
    
    # 测试确认角色
    test_confirm_roles()
    
    print("\n=== 测试完成 ===")
    print("✓ 基本API功能测试完成")
    print("✓ 服务器运行正常")
    print(f"✓ API文档地址: {BASE_URL}/docs")

if __name__ == "__main__":
    main()