#!/usr/bin/env python3
"""
简化的WebSocket连接测试
"""

import asyncio
import json
try:
    import websockets
except ImportError:
    print("错误: websockets库未安装")
    print("请运行: pip install websockets")
    exit(1)

async def test_health_websocket():
    """测试健康检查WebSocket"""
    print("测试健康检查WebSocket...")
    
    uri = "ws://localhost:8000/ws/health"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 接收欢迎消息
            welcome_msg = await websocket.recv()
            print(f"✓ 收到消息: {welcome_msg}")
            
            # 发送ping消息
            ping_msg = {"type": "ping"}
            await websocket.send(json.dumps(ping_msg))
            print(f"✓ 发送ping消息")
            
            # 接收响应
            response = await websocket.recv()
            print(f"✓ 收到响应: {response}")
            
            return True
            
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

async def test_review_websocket():
    """测试审查WebSocket（使用测试任务ID）"""
    print("\n测试审查WebSocket...")
    
    task_id = 1  # 使用测试任务ID
    uri = f"ws://localhost:8000/ws/review/{task_id}"
    print(f"连接到: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 接收连接确认
            connection_msg = await websocket.recv()
            print(f"✓ 收到连接确认: {connection_msg}")
            
            # 请求状态
            status_request = {"type": "get_status"}
            await websocket.send(json.dumps(status_request))
            print(f"✓ 发送状态请求")
            
            # 接收状态响应
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                print(f"✓ 收到状态响应: {status_response}")
            except asyncio.TimeoutError:
                print("⚠ 状态响应超时")
            
            return True
            
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

async def main():
    print("开始WebSocket连接测试...\n")
    
    # 测试健康检查
    health_ok = await test_health_websocket()
    
    # 测试审查WebSocket
    review_ok = await test_review_websocket()
    
    print("\n=== 测试结果 ===")
    print(f"健康检查WebSocket: {'✓ 通过' if health_ok else '✗ 失败'}")
    print(f"审查WebSocket: {'✓ 通过' if review_ok else '✗ 失败'}")
    
    if health_ok and review_ok:
        print("\n🎉 所有WebSocket测试通过!")
    else:
        print("\n⚠ 部分WebSocket测试失败")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"\n测试失败: {e}")