from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, task_id: int, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logger.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, task_id: int, websocket: WebSocket):
        """断开WebSocket连接"""
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_progress(self, task_id: int, message: dict):
        """发送进度消息"""
        if task_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to websocket: {e}")
                    disconnected.append(websocket)
            
            # 清理断开的连接
            for ws in disconnected:
                self.disconnect(task_id, ws)
    
    async def send_completion(self, task_id: int, result: dict):
        """发送完成消息"""
        message = {
            "stage": "complete",
            "progress": 100,
            "result": result
        }
        await self.send_progress(task_id, message)
    
    async def send_error(self, task_id: int, error: str):
        """发送错误消息"""
        message = {
            "stage": "error",
            "progress": 0,
            "error": error
        }
        await self.send_progress(task_id, message)

# 全局连接管理器实例
manager = ConnectionManager()