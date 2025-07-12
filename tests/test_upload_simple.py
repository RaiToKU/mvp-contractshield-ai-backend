#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的文件上传测试
"""

import requests
import io
import json

BASE_URL = "http://localhost:8000"

def test_file_upload():
    """测试文件上传功能"""
    print("\n=== 测试文件上传 ===")
    
    try:
        # 使用现有的PDF测试文件
        pdf_file_path = "/Users/yagamiraito/Documents/mvp/mvp-contractshield-ai-backend/temp/test_contract_copy.pdf"
        
        with open(pdf_file_path, 'rb') as f:
            files = {
                'file': ('test_contract.pdf', f, 'application/pdf')
            }
            
            data = {
                'contract_type': '技术服务合同'
            }
            
            # 发送上传请求
            response = requests.post(f"{BASE_URL}/api/v1/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 文件上传成功")
            print(f"✓ 任务ID: {result.get('task_id')}")
            print(f"✓ 状态: {result.get('status')}")
            return result.get('task_id')
        else:
            print(f"✗ 文件上传失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 文件上传异常: {e}")
        return None

def test_upload_status(task_id):
    """测试获取上传状态"""
    print(f"\n=== 测试获取上传状态 (任务ID: {task_id}) ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/upload/status/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 获取状态成功")
            print(f"✓ 状态: {result.get('status')}")
            print(f"✓ 进度: {result.get('progress', 0)}%")
            return result
        else:
            print(f"✗ 获取状态失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 获取状态异常: {e}")
        return None

def main():
    """主测试函数"""
    print("开始文件上传测试...")
    
    # 测试健康检查
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ 服务器运行正常")
        else:
            print("✗ 服务器异常")
            return
    except Exception as e:
        print(f"✗ 无法连接到服务器: {e}")
        return
    
    # 测试文件上传
    task_id = test_file_upload()
    
    if task_id:
        # 测试获取状态
        test_upload_status(task_id)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()