#!/usr/bin/env python3
"""
WebSocket连接测试脚本
用于测试和演示WebSocket连接功能
"""

import asyncio
import websockets
import json
import sys
import time
from typing import Optional

# WebSocket服务器配置
WS_HOST = "localhost"
WS_PORT = 8000
BASE_WS_URL = f"ws://{WS_HOST}:{WS_PORT}"

class WebSocketTester:
    """WebSocket测试类"""
    
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
    
    async def test_health_websocket(self):
        """测试健康检查WebSocket"""
        print("=== 测试健康检查WebSocket ===")
        
        uri = f"{BASE_WS_URL}/ws/health"
        print(f"连接到: {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✓ WebSocket连接成功")
                
                # 接收欢迎消息
                welcome_msg = await websocket.recv()
                print(f"✓ 收到欢迎消息: {welcome_msg}")
                
                # 发送ping消息
                ping_msg = {"type": "ping", "timestamp": time.time()}
                await websocket.send(json.dumps(ping_msg))
                print(f"✓ 发送ping消息: {ping_msg}")
                
                # 接收pong响应
                pong_response = await websocket.recv()
                print(f"✓ 收到pong响应: {pong_response}")
                
                return True
                
        except Exception as e:
            print(f"✗ 健康检查WebSocket测试失败: {e}")
            return False
    
    async def test_review_websocket(self, task_id: int):
        """测试审查进度WebSocket"""
        print(f"\n=== 测试审查进度WebSocket (任务ID: {task_id}) ===")
        
        uri = f"{BASE_WS_URL}/ws/review/{task_id}"
        print(f"连接到: {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✓ WebSocket连接成功")
                
                # 接收连接确认消息
                connection_msg = await websocket.recv()
                print(f"✓ 收到连接确认: {connection_msg}")
                
                # 请求当前状态
                status_request = {"type": "get_status"}
                await websocket.send(json.dumps(status_request))
                print(f"✓ 发送状态请求: {status_request}")
                
                # 接收状态响应
                status_response = await websocket.recv()
                print(f"✓ 收到状态响应: {status_response}")
                
                # 发送心跳包
                heartbeat = {"type": "heartbeat", "timestamp": time.time()}
                await websocket.send(json.dumps(heartbeat))
                print(f"✓ 发送心跳包: {heartbeat}")
                
                # 等待可能的进度更新
                print("等待进度更新消息（5秒）...")
                try:
                    progress_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"✓ 收到进度更新: {progress_msg}")
                except asyncio.TimeoutError:
                    print("⚠ 未收到进度更新消息（正常，任务可能已完成）")
                
                return True
                
        except Exception as e:
            print(f"✗ 审查进度WebSocket测试失败: {e}")
            return False
    
    async def test_websocket_with_client_id(self, client_id: str = "test_client_001"):
        """测试带客户端ID的WebSocket"""
        print(f"\n=== 测试客户端WebSocket (客户端ID: {client_id}) ===")
        
        uri = f"{BASE_WS_URL}/ws/test/{client_id}"
        print(f"连接到: {uri}")
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✓ WebSocket连接成功")
                
                # 接收欢迎消息
                welcome_msg = await websocket.recv()
                print(f"✓ 收到欢迎消息: {welcome_msg}")
                
                # 发送测试消息
                test_messages = [
                    {"type": "test", "message": "Hello WebSocket!"},
                    {"type": "data", "payload": {"key": "value", "number": 42}},
                    {"type": "ping", "timestamp": time.time()}
                ]
                
                for msg in test_messages:
                    await websocket.send(json.dumps(msg))
                    print(f"✓ 发送消息: {msg}")
                    
                    # 接收回显
                    response = await websocket.recv()
                    print(f"✓ 收到回显: {response}")
                
                return True
                
        except Exception as e:
            print(f"✗ 客户端WebSocket测试失败: {e}")
            return False
    
    async def run_all_tests(self, task_id: Optional[int] = None):
        """运行所有WebSocket测试"""
        print("开始WebSocket连接测试...\n")
        
        results = []
        
        # 测试健康检查WebSocket
        results.append(await self.test_health_websocket())
        
        # 测试客户端WebSocket
        results.append(await self.test_websocket_with_client_id())
        
        # 如果提供了任务ID，测试审查进度WebSocket
        if task_id:
            results.append(await self.test_review_websocket(task_id))
        else:
            print("\n⚠ 未提供任务ID，跳过审查进度WebSocket测试")
            print("提示: 可以先运行 test_api_endpoints.py 创建任务，然后使用任务ID测试")
        
        # 总结测试结果
        print("\n=== 测试结果总结 ===")
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            print(f"🎉 所有测试通过! ({passed}/{total})")
        else:
            print(f"⚠ 部分测试失败: {passed}/{total} 通过")
        
        return passed == total

def print_connection_guide():
    """打印WebSocket连接使用说明"""
    print("""
=== WebSocket连接使用说明 ===

1. 服务器端点:
   - 健康检查: ws://localhost:8000/ws/health
   - 审查进度: ws://localhost:8000/ws/review/{task_id}
   - 测试连接: ws://localhost:8000/ws/test/{client_id}

2. 连接步骤:
   a) 确保后端服务正在运行 (python run.py)
   b) 使用WebSocket客户端连接到相应端点
   c) 发送和接收JSON格式的消息

3. 消息格式:
   - 发送: {"type": "message_type", "data": "your_data"}
   - 接收: {"type": "response_type", "message": "response_message"}

4. 前端JavaScript连接示例:
   ```javascript
   // 连接到审查进度WebSocket
   const ws = new WebSocket('ws://localhost:8000/ws/review/123');
   
   ws.onopen = function(event) {
       console.log('WebSocket连接已建立');
   };
   
   ws.onmessage = function(event) {
       const data = JSON.parse(event.data);
       console.log('收到消息:', data);
   };
   
   ws.onerror = function(error) {
       console.error('WebSocket错误:', error);
   };
   
   ws.onclose = function(event) {
       console.log('WebSocket连接已关闭');
   };
   
   // 发送消息
   ws.send(JSON.stringify({type: 'get_status'}));
   ```

5. Python客户端连接示例:
   ```python
   import asyncio
   import websockets
   import json
   
   async def connect_to_websocket():
       uri = "ws://localhost:8000/ws/health"
       async with websockets.connect(uri) as websocket:
           # 接收消息
           message = await websocket.recv()
           print(f"收到: {message}")
           
           # 发送消息
           await websocket.send(json.dumps({"type": "ping"}))
   
   asyncio.run(connect_to_websocket())
   ```

6. 常见问题排查:
   - 连接被拒绝: 检查服务器是否运行在正确端口
   - 消息格式错误: 确保发送有效的JSON格式
   - 连接断开: 检查网络连接和服务器日志
   - CORS问题: 确保CORS配置允许WebSocket连接

7. 调试建议:
   - 查看服务器日志: 运行时会显示连接和断开信息
   - 使用浏览器开发者工具的Network标签查看WebSocket连接
   - 先测试健康检查端点确认基本连接功能
""")

async def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print_connection_guide()
            return
        
        try:
            task_id = int(sys.argv[1])
        except ValueError:
            print("错误: 任务ID必须是数字")
            print("用法: python test_websocket.py [task_id]")
            print("或者: python test_websocket.py --help")
            return
    else:
        task_id = None
    
    tester = WebSocketTester()
    await tester.run_all_tests(task_id)
    
    print("\n如需查看详细连接说明，请运行: python test_websocket.py --help")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")