from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Path
import logging
import json
import time

from ..websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/review/{task_id}")
async def review_websocket(
    websocket: WebSocket,
    task_id: int = Path(..., description="任务ID")
):
    """
    审查进度WebSocket连接
    
    Args:
        websocket: WebSocket连接
        task_id: 任务ID
    """
    await manager.connect(task_id, websocket)
    
    try:
        # 发送连接确认消息
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": f"已连接到任务 {task_id} 的进度推送",
            "task_id": task_id
        }))
        
        # 保持连接活跃
        while True:
            try:
                # 接收客户端消息（心跳包等）
                data = await websocket.receive_text()
                
                # 解析消息
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # 响应心跳包
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": message.get("timestamp")
                        }))
                    elif message_type == "heartbeat":
                        # 响应心跳包（另一种格式）
                        await websocket.send_text(json.dumps({
                            "type": "heartbeat_ack",
                            "timestamp": message.get("timestamp")
                        }))
                    elif message_type in ["status_request", "get_status"]:
                        # 客户端请求当前状态
                        await _send_current_status(websocket, task_id)
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        # 发送错误响应给客户端
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"未知的消息类型: {message_type}",
                            "supported_types": ["ping", "heartbeat", "get_status", "status_request"]
                        }))
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {data}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        manager.disconnect(task_id, websocket)

async def _send_current_status(websocket: WebSocket, task_id: int):
    """
    发送当前任务状态
    
    Args:
        websocket: WebSocket连接
        task_id: 任务ID
    """
    try:
        from ..database import SessionLocal
        from ..models import Task
        
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                status_message = {
                    "type": "status",
                    "task_id": task_id,
                    "status": task.status,
                    "contract_type": task.contract_type,
                    "role": task.role,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None
                }
                
                await websocket.send_text(json.dumps(status_message))
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"任务 {task_id} 不存在"
                }))
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error sending current status: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "获取状态失败"
        }))

@router.websocket("/ws/health")
async def health_websocket(websocket: WebSocket):
    """
    健康检查WebSocket连接
    
    Args:
        websocket: WebSocket连接
    """
    await websocket.accept()
    
    try:
        await websocket.send_text(json.dumps({
            "type": "health",
            "status": "healthy",
            "message": "WebSocket服务正常运行"
        }))
        
        # 保持连接用于测试
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp"),
                        "server_time": str(int(time.time() * 1000))
                    }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
                
    except WebSocketDisconnect:
        logger.info("Health check WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health check WebSocket error: {e}")

# 用于测试的WebSocket端点
@router.websocket("/ws/test/{client_id}")
async def test_websocket(
    websocket: WebSocket,
    client_id: str = Path(..., description="客户端ID")
):
    """
    测试WebSocket连接
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
    """
    await websocket.accept()
    
    try:
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "client_id": client_id,
            "message": f"欢迎客户端 {client_id}"
        }))
        
        while True:
            data = await websocket.receive_text()
            
            # 回显消息
            await websocket.send_text(json.dumps({
                "type": "echo",
                "client_id": client_id,
                "original_message": data,
                "timestamp": str(int(time.time() * 1000))
            }))
            
    except WebSocketDisconnect:
        logger.info(f"Test WebSocket disconnected for client {client_id}")
    except Exception as e:
        logger.error(f"Test WebSocket error for client {client_id}: {e}")

# 导入time模块
import time