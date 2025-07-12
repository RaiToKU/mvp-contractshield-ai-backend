#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime

def get_task_33_info():
    """获取任务33的详细信息"""
    base_url = "http://localhost:8000/api/v1"
    
    print("=" * 60)
    print("📋 任务33报告生成情况查询")
    print("=" * 60)
    
    try:
        # 1. 获取审查结果
        print("\n🔍 查询审查结果...")
        response = requests.get(f"{base_url}/review/33")
        if response.status_code == 200:
            review_data = response.json()
            print(f"✅ 审查结果获取成功")
            print(f"   任务ID: {review_data.get('task_id')}")
            print(f"   状态: {review_data.get('status')}")
            print(f"   合同类型: {review_data.get('contract_type')}")
            print(f"   角色: {review_data.get('role')}")
            print(f"   创建时间: {review_data.get('created_at')}")
            print(f"   更新时间: {review_data.get('updated_at')}")
            
            # 分析摘要和风险
            summary = review_data.get('summary', '')
            risks = review_data.get('risks', [])
            print(f"   摘要长度: {len(summary)} 字符")
            print(f"   风险数量: {len(risks)} 项")
            
            if risks:
                print(f"   风险类型: {[risk.get('type', 'Unknown') for risk in risks[:3]]}...")
        else:
            print(f"❌ 审查结果获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return
    
        # 2. 获取报告预览
        print("\n📄 查询报告预览...")
        response = requests.get(f"{base_url}/export/33/preview")
        if response.status_code == 200:
            preview_data = response.json()
            print(f"✅ 报告预览获取成功")
            print(f"   支持的导出格式: {preview_data.get('export_formats', [])}")
        else:
            print(f"❌ 报告预览获取失败: {response.status_code}")
    
        # 3. 检查可用的导出格式
        print("\n🎯 查询导出格式...")
        response = requests.get(f"{base_url}/export/33/formats")
        if response.status_code == 200:
            formats_data = response.json()
            print(f"✅ 导出格式获取成功")
            formats = formats_data.get('formats', [])
            for fmt in formats:
                status = "✅" if fmt.get('available') else "❌"
                print(f"   {status} {fmt.get('name')} ({fmt.get('format')}) - {fmt.get('description')}")
        else:
            print(f"❌ 导出格式获取失败: {response.status_code}")
    
        # 4. 尝试生成报告（不下载，只检查是否可以生成）
        print("\n📊 测试报告生成...")
        for format_type in ['pdf', 'docx', 'txt']:
            try:
                response = requests.get(f"{base_url}/export/33?format={format_type}", stream=True)
                if response.status_code == 200:
                    content_length = response.headers.get('content-length', 'Unknown')
                    content_type = response.headers.get('content-type', 'Unknown')
                    print(f"   ✅ {format_type.upper()} 报告可生成 (大小: {content_length} bytes, 类型: {content_type})")
                else:
                    print(f"   ❌ {format_type.upper()} 报告生成失败: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {format_type.upper()} 报告生成出错: {e}")
    
        # 5. 检查exports目录
        print("\n📁 检查导出目录...")
        exports_dir = "./exports"
        if os.path.exists(exports_dir):
            files = [f for f in os.listdir(exports_dir) if f.startswith('contract_review_33_')]
            if files:
                print(f"   ✅ 找到 {len(files)} 个相关文件:")
                for file in files:
                    file_path = os.path.join(exports_dir, file)
                    file_size = os.path.getsize(file_path)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"     📄 {file} ({file_size} bytes, 修改时间: {mod_time})")
            else:
                print(f"   ⚠️  导出目录存在但未找到任务33的文件")
        else:
            print(f"   ❌ 导出目录不存在")
    
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 查询过程中出错: {e}")
    
    print("\n" + "=" * 60)
    print("查询完成")
    print("=" * 60)

if __name__ == "__main__":
    get_task_33_info()