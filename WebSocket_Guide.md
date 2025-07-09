# WebSocket连接和使用说明

## 概述

ContractShield AI后端提供了三个WebSocket端点，用于实时通信和进度推送：

1. **健康检查WebSocket** - 用于测试WebSocket服务是否正常
2. **审查进度WebSocket** - 用于实时推送合同审查进度
3. **测试WebSocket** - 用于开发和调试

## 服务器配置

- **服务器地址**: `localhost:8000`
- **协议**: WebSocket (ws://)
- **数据格式**: JSON

## WebSocket端点详情

### 1. 健康检查WebSocket

**端点**: `ws://localhost:8000/ws/health`

**用途**: 检查WebSocket服务是否正常运行

**连接流程**:
1. 连接后立即收到欢迎消息
2. 可发送ping消息测试连接
3. 服务器会响应pong消息

**消息格式**:
```json
// 发送ping
{"type": "ping", "timestamp": 1234567890}

// 接收pong
{"type": "pong", "timestamp": 1234567890, "server_time": "1234567890"}
```

### 2. 审查进度WebSocket

**端点**: `ws://localhost:8000/ws/review/{task_id}`

**用途**: 实时接收合同审查进度更新

**连接流程**:
1. 连接时需要提供有效的任务ID
2. 连接成功后收到连接确认消息
3. 可请求当前任务状态
4. 可发送心跳包保持连接
5. 审查过程中会自动推送进度更新

**支持的消息类型**:

#### 发送消息
```json
// 心跳包
{"type": "ping", "timestamp": 1234567890}
{"type": "heartbeat", "timestamp": 1234567890}

// 请求状态
{"type": "get_status"}
{"type": "status_request"}
```

#### 接收消息
```json
// 连接确认
{
  "type": "connection",
  "message": "已连接到任务 123 的进度推送",
  "task_id": 123
}

// 心跳响应
{"type": "pong", "timestamp": 1234567890}
{"type": "heartbeat_ack", "timestamp": 1234567890}

// 任务状态
{
  "type": "status",
  "task_id": 123,
  "status": "PROCESSING",
  "contract_type": "purchase",
  "role": "buyer",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}

// 进度更新
{
  "stage": "analyzing",
  "progress": 50,
  "message": "正在分析合同条款..."
}

// 完成消息
{
  "stage": "complete",
  "progress": 100,
  "result": {...}
}

// 错误消息
{
  "type": "error",
  "message": "错误描述"
}
```

### 3. 测试WebSocket

**端点**: `ws://localhost:8000/ws/test/{client_id}`

**用途**: 开发和调试WebSocket功能

**连接流程**:
1. 连接时需要提供客户端ID
2. 连接成功后收到欢迎消息
3. 发送的任何消息都会被回显

**消息格式**:
```json
// 欢迎消息
{
  "type": "welcome",
  "client_id": "test_client_001",
  "message": "欢迎客户端 test_client_001"
}

// 回显消息
{
  "type": "echo",
  "client_id": "test_client_001",
  "original_message": "你发送的消息",
  "timestamp": "1234567890"
}
```

## 前端连接示例

### JavaScript/TypeScript

```javascript
// 连接到审查进度WebSocket
class ReviewWebSocket {
  constructor(taskId) {
    this.taskId = taskId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    try {
      this.ws = new WebSocket(`ws://localhost:8000/ws/review/${this.taskId}`);
      
      this.ws.onopen = (event) => {
        console.log('WebSocket连接已建立');
        this.reconnectAttempts = 0;
        
        // 请求当前状态
        this.sendMessage({type: 'get_status'});
        
        // 开始心跳
        this.startHeartbeat();
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          console.error('解析消息失败:', e);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };
      
      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        this.stopHeartbeat();
        
        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.connect();
          }, 3000);
        }
      };
      
    } catch (error) {
      console.error('连接失败:', error);
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  handleMessage(data) {
    switch (data.type) {
      case 'connection':
        console.log('连接确认:', data.message);
        break;
      case 'status':
        console.log('任务状态:', data);
        this.updateTaskStatus(data);
        break;
      case 'pong':
      case 'heartbeat_ack':
        console.log('心跳响应');
        break;
      case 'error':
        console.error('服务器错误:', data.message);
        break;
      default:
        if (data.stage) {
          // 进度更新
          console.log(`进度更新: ${data.stage} - ${data.progress}%`);
          this.updateProgress(data);
        }
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.sendMessage({
        type: 'heartbeat',
        timestamp: Date.now()
      });
    }, 30000); // 每30秒发送一次心跳
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  updateTaskStatus(status) {
    // 更新UI显示任务状态
    document.getElementById('task-status').textContent = status.status;
    document.getElementById('contract-type').textContent = status.contract_type;
  }

  updateProgress(progress) {
    // 更新进度条
    const progressBar = document.getElementById('progress-bar');
    if (progressBar) {
      progressBar.style.width = `${progress.progress}%`;
    }
    
    // 更新状态文本
    const statusText = document.getElementById('status-text');
    if (statusText) {
      statusText.textContent = progress.message || `${progress.stage} - ${progress.progress}%`;
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// 使用示例
const reviewWS = new ReviewWebSocket(123);
reviewWS.connect();

// 页面关闭时断开连接
window.addEventListener('beforeunload', () => {
  reviewWS.disconnect();
});
```

### React Hook示例

```typescript
import { useEffect, useRef, useState } from 'react';

interface ProgressData {
  stage: string;
  progress: number;
  message?: string;
}

interface TaskStatus {
  task_id: number;
  status: string;
  contract_type: string;
  role: string;
}

export const useReviewWebSocket = (taskId: number) => {
  const [isConnected, setIsConnected] = useState(false);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const connect = () => {
      try {
        const ws = new WebSocket(`ws://localhost:8000/ws/review/${taskId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
          
          // 请求状态
          ws.send(JSON.stringify({ type: 'get_status' }));
          
          // 开始心跳
          heartbeatRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({
                type: 'heartbeat',
                timestamp: Date.now()
              }));
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
              case 'status':
                setTaskStatus(data);
                break;
              case 'error':
                setError(data.message);
                break;
              default:
                if (data.stage) {
                  setProgress(data);
                }
            }
          } catch (e) {
            console.error('解析消息失败:', e);
          }
        };

        ws.onerror = () => {
          setError('WebSocket连接错误');
        };

        ws.onclose = () => {
          setIsConnected(false);
          if (heartbeatRef.current) {
            clearInterval(heartbeatRef.current);
            heartbeatRef.current = null;
          }
        };

      } catch (error) {
        setError('连接失败');
      }
    };

    connect();

    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [taskId]);

  return {
    isConnected,
    progress,
    taskStatus,
    error
  };
};
```

## Python客户端示例

```python
import asyncio
import websockets
import json
import logging

class ReviewWebSocketClient:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """连接到WebSocket"""
        uri = f"ws://localhost:8000/ws/review/{self.task_id}"
        
        try:
            self.websocket = await websockets.connect(uri)
            self.running = True
            print(f"已连接到任务 {self.task_id} 的WebSocket")
            
            # 启动消息处理
            await asyncio.gather(
                self.listen_messages(),
                self.send_heartbeat()
            )
            
        except Exception as e:
            print(f"连接失败: {e}")
            
    async def listen_messages(self):
        """监听消息"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("连接已关闭")
        except Exception as e:
            print(f"消息处理错误: {e}")
        finally:
            self.running = False
            
    async def handle_message(self, data: dict):
        """处理接收到的消息"""
        message_type = data.get('type')
        
        if message_type == 'connection':
            print(f"连接确认: {data.get('message')}")
            # 请求当前状态
            await self.send_message({'type': 'get_status'})
            
        elif message_type == 'status':
            print(f"任务状态: {data.get('status')}")
            
        elif message_type in ['pong', 'heartbeat_ack']:
            print("心跳响应")
            
        elif message_type == 'error':
            print(f"错误: {data.get('message')}")
            
        elif 'stage' in data:
            # 进度更新
            stage = data.get('stage')
            progress = data.get('progress', 0)
            message = data.get('message', '')
            print(f"进度更新: {stage} - {progress}% - {message}")
            
    async def send_message(self, message: dict):
        """发送消息"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(message))
            
    async def send_heartbeat(self):
        """发送心跳包"""
        while self.running:
            try:
                await asyncio.sleep(30)  # 每30秒发送一次
                if self.running:
                    await self.send_message({
                        'type': 'heartbeat',
                        'timestamp': int(time.time() * 1000)
                    })
            except Exception as e:
                print(f"心跳发送失败: {e}")
                break
                
    async def disconnect(self):
        """断开连接"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

# 使用示例
async def main():
    client = ReviewWebSocketClient(task_id=123)
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## 常见问题和解决方案

### 1. 连接被拒绝

**问题**: `WebSocket connection failed`

**解决方案**:
- 确认后端服务正在运行: `python run.py`
- 检查端口是否正确 (默认8000)
- 确认防火墙设置

### 2. 消息格式错误

**问题**: 收到错误响应或消息被忽略

**解决方案**:
- 确保发送有效的JSON格式
- 检查消息类型是否正确
- 查看服务器日志获取详细错误信息

### 3. 连接频繁断开

**问题**: WebSocket连接不稳定

**解决方案**:
- 实现心跳机制保持连接活跃
- 添加自动重连逻辑
- 检查网络连接稳定性

### 4. CORS问题

**问题**: 浏览器阻止WebSocket连接

**解决方案**:
- 确认CORS配置正确
- 检查Origin头设置
- 使用HTTPS时确保WebSocket也使用WSS

## 调试建议

1. **查看服务器日志**: 运行后端时会显示详细的连接和消息日志
2. **使用浏览器开发者工具**: Network标签可以查看WebSocket连接状态
3. **测试基本连接**: 先使用健康检查端点测试基本功能
4. **逐步测试**: 从简单的ping/pong开始，逐步测试复杂功能
5. **使用测试工具**: 可以使用提供的HTML测试页面进行调试

## 测试工具

项目提供了以下测试工具:

1. **websocket_test.html**: 浏览器端测试工具
2. **test_websocket.py**: Python命令行测试工具
3. **simple_websocket_test.py**: 简化的Python测试脚本

使用方法:
```bash
# Python测试
python3 test_websocket.py [task_id]

# 浏览器测试
# 在浏览器中打开 websocket_test.html
```

## 性能优化建议

1. **连接池管理**: 避免创建过多并发连接
2. **消息批处理**: 合并多个小消息减少网络开销
3. **心跳间隔**: 根据网络环境调整心跳频率
4. **错误重试**: 实现指数退避重连策略
5. **内存管理**: 及时清理断开的连接和相关资源

## 安全考虑

1. **身份验证**: 生产环境中应添加WebSocket身份验证
2. **输入验证**: 验证所有接收到的消息格式和内容
3. **速率限制**: 防止消息洪水攻击
4. **HTTPS/WSS**: 生产环境使用加密连接
5. **Origin检查**: 验证连接来源的合法性