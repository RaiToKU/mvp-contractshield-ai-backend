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
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from app.main import app
from app.websocket_manager import manager

# WebSocket服务器配置
WS_HOST = "localhost"
WS_PORT = 8000
BASE_WS_URL = f"ws://{WS_HOST}:{WS_PORT}"


@pytest.mark.websocket
class TestWebSocketConnections:
    """WebSocket连接测试"""
    
    def test_websocket_health_check(self, client):
        """测试WebSocket健康检查"""
        with client.websocket_connect("/ws/health") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "health_check"
            assert data["status"] == "connected"
    
    def test_websocket_review_progress(self, client, sample_task):
        """测试WebSocket审查进度"""
        with client.websocket_connect(f"/ws/review/{sample_task.id}") as websocket:
            # 模拟发送进度更新
            with patch.object(manager, 'send_progress') as mock_send:
                mock_send.return_value = None
                
                # 发送测试消息
                websocket.send_json({
                    "type": "start_review",
                    "task_id": sample_task.id
                })
                
                # 接收响应
                data = websocket.receive_json()
                assert data["type"] == "review_started"
    
    def test_websocket_with_client_id(self, client):
        """测试带客户端ID的WebSocket连接"""
        client_id = "test_client_123"
        
        with client.websocket_connect(f"/ws/{client_id}") as websocket:
            # 发送连接确认
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["client_id"] == client_id
    
    def test_websocket_disconnect(self, client):
        """测试WebSocket断开连接"""
        with client.websocket_connect("/ws/health") as websocket:
            # 正常连接
            data = websocket.receive_json()
            assert data["type"] == "health_check"
            
            # 断开连接
            websocket.close()
    
    def test_websocket_invalid_endpoint(self, client):
        """测试无效的WebSocket端点"""
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/invalid") as websocket:
                pass


@pytest.mark.websocket
class TestWebSocketManager:
    """WebSocket管理器测试"""
    
    @pytest.mark.asyncio
    async def test_websocket_manager_send_progress(self, sample_task):
        """测试WebSocket管理器发送进度"""
        # 模拟连接
        mock_websocket = AsyncMock()
        manager.active_connections[sample_task.id] = mock_websocket
        
        await manager.send_progress(sample_task.id, "processing", 50)
        
        mock_websocket.send_json.assert_called_once_with({
            "type": "progress",
            "task_id": sample_task.id,
            "status": "processing",
            "progress": 50
        })
    
    @pytest.mark.asyncio
    async def test_websocket_manager_send_completion(self, sample_task):
        """测试WebSocket管理器发送完成消息"""
        # 模拟连接
        mock_websocket = AsyncMock()
        manager.active_connections[sample_task.id] = mock_websocket
        
        result_data = {"risks": [], "summary": {}}
        await manager.send_completion(sample_task.id, result_data)
        
        mock_websocket.send_json.assert_called_once_with({
            "type": "completed",
            "task_id": sample_task.id,
            "result": result_data
        })
    
    @pytest.mark.asyncio
    async def test_websocket_manager_send_error(self, sample_task):
        """测试WebSocket管理器发送错误消息"""
        # 模拟连接
        mock_websocket = AsyncMock()
        manager.active_connections[sample_task.id] = mock_websocket
        
        error_message = "处理过程中发生错误"
        await manager.send_error(sample_task.id, error_message)
        
        mock_websocket.send_json.assert_called_once_with({
            "type": "error",
            "task_id": sample_task.id,
            "message": error_message
        })
    
    @pytest.mark.asyncio
    async def test_websocket_manager_connection_management(self, sample_task):
        """测试WebSocket连接管理"""
        mock_websocket = AsyncMock()
        
        # 测试添加连接
        manager.connect(sample_task.id, mock_websocket)
        assert sample_task.id in manager.active_connections
        
        # 测试断开连接
        manager.disconnect(sample_task.id)
        assert sample_task.id not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast(self):
        """测试WebSocket广播消息"""
        # 模拟多个连接
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        manager.active_connections["client1"] = mock_ws1
        manager.active_connections["client2"] = mock_ws2
        
        message = {"type": "broadcast", "data": "test"}
        await manager.broadcast(message)
        
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
        
        # 清理
        manager.active_connections.clear()


@pytest.mark.websocket
class TestWebSocketMessages:
    """WebSocket消息处理测试"""
    
    def test_websocket_message_format(self, client):
        """测试WebSocket消息格式"""
        with client.websocket_connect("/ws/health") as websocket:
            data = websocket.receive_json()
            
            # 验证消息格式
            assert isinstance(data, dict)
            assert "type" in data
            assert "timestamp" in data or "status" in data
    
    def test_websocket_ping_pong(self, client):
        """测试WebSocket ping/pong"""
        with client.websocket_connect("/ws/health") as websocket:
            # 发送ping
            websocket.send_json({"type": "ping"})
            
            # 接收pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
    
    def test_websocket_multiple_messages(self, client, sample_task):
        """测试WebSocket多条消息"""
        with client.websocket_connect(f"/ws/review/{sample_task.id}") as websocket:
            # 发送多条消息
            messages = [
                {"type": "start_review", "task_id": sample_task.id},
                {"type": "get_status", "task_id": sample_task.id}
            ]
            
            for message in messages:
                websocket.send_json(message)
                response = websocket.receive_json()
                assert "type" in response
    
    def test_websocket_error_handling(self, client, sample_task):
        """测试WebSocket错误处理"""
        with client.websocket_connect(f"/ws/review/{sample_task.id}") as websocket:
            # 发送无效消息
            websocket.send_json({"type": "invalid_type"})
            
            # 应该收到错误响应
            data = websocket.receive_json()
            assert data["type"] == "error"
    
    def test_websocket_json_validation(self, client):
        """测试WebSocket JSON验证"""
        with client.websocket_connect("/ws/health") as websocket:
            # 发送有效JSON
            websocket.send_json({"type": "test", "data": "valid"})
            
            # 接收响应
            data = websocket.receive_json()
            assert isinstance(data, dict)


@pytest.mark.websocket
@pytest.mark.slow
class TestWebSocketPerformance:
    """WebSocket性能测试"""
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self, client):
        """测试WebSocket并发连接"""
        connections = []
        
        try:
            # 创建多个并发连接
            for i in range(5):
                ws = client.websocket_connect(f"/ws/client_{i}")
                connections.append(ws.__enter__())
            
            # 验证所有连接都成功
            for ws in connections:
                data = ws.receive_json()
                assert data["type"] == "connection_established"
        
        finally:
            # 清理连接
            for ws in connections:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass
    
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self, client, sample_task):
        """测试WebSocket消息吞吐量"""
        with client.websocket_connect(f"/ws/review/{sample_task.id}") as websocket:
            # 发送大量消息
            message_count = 10
            
            for i in range(message_count):
                websocket.send_json({
                    "type": "ping",
                    "sequence": i
                })
                
                response = websocket.receive_json()
                assert response["type"] == "pong"


# WebSocket连接使用说明
"""
WebSocket端点说明：

1. 健康检查: /ws/health
   - 用于测试WebSocket连接是否正常
   - 连接后会收到健康检查消息

2. 审查进度: /ws/review/{task_id}
   - 用于接收特定任务的审查进度更新
   - 会收到进度、完成、错误等类型的消息

3. 客户端连接: /ws/{client_id}
   - 用于建立带客户端ID的连接
   - 可以接收针对特定客户端的消息

消息格式：
{
    "type": "消息类型",
    "task_id": "任务ID（可选）",
    "client_id": "客户端ID（可选）",
    "data": "消息数据",
    "timestamp": "时间戳"
}

JavaScript连接示例：
const ws = new WebSocket('ws://localhost:8000/ws/review/123');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};
"""

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