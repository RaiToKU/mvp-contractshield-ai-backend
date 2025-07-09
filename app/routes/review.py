from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..database import get_db
from ..services.review_service import review_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["review"])

# Pydantic模型
class DraftRolesRequest(BaseModel):
    task_id: int

class ConfirmRolesRequest(BaseModel):
    task_id: int
    role: str
    party_names: Optional[List[str]] = None  # 可选，如果不提供则从实体数据中自动选择
    selected_entity_index: Optional[int] = 0  # 选择的实体索引，默认第一个

class ManualPartyNamesRequest(BaseModel):
    task_id: int
    role: str
    party_names: List[str]  # 手动输入的主体名称

class ReviewRequest(BaseModel):
    task_id: int

@router.post("/draft_roles")
async def get_draft_roles(
    request: DraftRolesRequest,
    db: Session = Depends(get_db)
):
    """
    获取草稿角色识别结果
    
    Args:
        request: 包含task_id的请求
        db: 数据库会话
    
    Returns:
        角色候选列表
    """
    try:
        result = review_service.get_draft_roles(request.task_id)
        
        logger.info(f"Draft roles generated for task {request.task_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting draft roles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取角色识别结果失败: {str(e)}"
        )

@router.post("/confirm_roles")
async def confirm_roles(
    request: ConfirmRolesRequest,
    db: Session = Depends(get_db)
):
    """
    确认角色信息
    
    Args:
        request: 角色确认请求
        db: 数据库会话
    
    Returns:
        确认结果
    """
    try:
        # 记录入参
        logger.info(f"📥 Confirm roles request - task_id: {request.task_id}, role: {request.role}, party_names: {request.party_names}, selected_entity_index: {request.selected_entity_index}")
        
        # 验证角色
        valid_roles = [
            "buyer", "seller", "client", "provider", 
            "party_a", "party_b", "landlord", "tenant"
        ]
        
        if request.role not in valid_roles:
            error_msg = f"无效的角色类型。支持的角色: {', '.join(valid_roles)}"
            logger.error(f"❌ Role validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # 如果没有提供party_names且没有selected_entity_index，才报错
        if not request.party_names and request.selected_entity_index is None:
            error_msg = "需要提供主体名称或选择实体索引"
            logger.error(f"❌ Party names validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        result = review_service.confirm_roles(
            task_id=request.task_id,
            role=request.role,
            party_names=request.party_names,
            selected_entity_index=request.selected_entity_index or 0
        )
        
        # 记录出参
        logger.info(f"📤 Confirm roles response: {result}")
        logger.info(f"✅ Roles confirmed for task {request.task_id}: {request.role}")
        return result
        
    except HTTPException as e:
        logger.error(f"❌ HTTP Exception in confirm_roles: {e.detail}")
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"❌ ValueError in confirm_roles: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"角色确认失败: {str(e)}"
        logger.error(f"❌ Unexpected error in confirm_roles: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/manual_party_names")
async def set_manual_party_names(
    request: ManualPartyNamesRequest,
    db: Session = Depends(get_db)
):
    """
    手动设置主体名称（当实体识别失败时的备选方案）
    
    Args:
        request: 手动主体名称请求
        db: 数据库会话
    
    Returns:
        设置结果
    """
    try:
        # 记录入参
        logger.info(f"📥 Manual party names request - task_id: {request.task_id}, role: {request.role}, party_names: {request.party_names}")
        
        # 验证角色
        valid_roles = [
            "buyer", "seller", "client", "provider", 
            "party_a", "party_b", "landlord", "tenant"
        ]
        
        if request.role not in valid_roles:
            error_msg = f"无效的角色类型。支持的角色: {', '.join(valid_roles)}"
            logger.error(f"❌ Role validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # 验证主体名称
        if not request.party_names or len(request.party_names) == 0:
            error_msg = "主体名称不能为空"
            logger.error(f"❌ Party names validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        # 过滤空字符串
        party_names = [name.strip() for name in request.party_names if name.strip()]
        if not party_names:
            error_msg = "主体名称不能全为空字符串"
            logger.error(f"❌ Party names validation failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        result = review_service.confirm_roles(
            task_id=request.task_id,
            role=request.role,
            party_names=party_names,
            selected_entity_index=None  # 手动输入时不使用索引
        )
        
        # 记录出参
        logger.info(f"📤 Manual party names response: {result}")
        logger.info(f"✅ Manual party names set for task {request.task_id}: {request.role}")
        return result
        
    except HTTPException as e:
        logger.error(f"❌ HTTP Exception in set_manual_party_names: {e.detail}")
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.error(f"❌ ValueError in set_manual_party_names: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = f"设置主体名称失败: {str(e)}"
        logger.error(f"❌ Unexpected error in set_manual_party_names: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/review")
async def start_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    开始合同审查
    
    Args:
        request: 审查请求
        background_tasks: 后台任务
        db: 数据库会话
    
    Returns:
        审查启动确认
    """
    try:
        from ..models import Task
        
        # 检查任务状态
        task = db.query(Task).filter(Task.id == request.task_id).first()
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {request.task_id} 不存在"
            )
        
        if task.status not in ["READY", "PENDING"]:
            raise HTTPException(
                status_code=400,
                detail=f"任务状态不允许开始审查。当前状态: {task.status}"
            )
        
        if not task.role:
            raise HTTPException(
                status_code=400,
                detail="请先确认角色信息"
            )
        
        # 启动后台审查任务
        background_tasks.add_task(
            review_service.start_review,
            request.task_id
        )
        
        logger.info(f"Review started for task {request.task_id}")
        
        return {
            "task_id": request.task_id,
            "status": "IN_PROGRESS",
            "message": "审查已开始，请通过WebSocket监听进度"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting review: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"启动审查失败: {str(e)}"
        )

@router.get("/review/{task_id}")
async def get_review_result(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取审查结果
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        审查结果
    """
    try:
        result = review_service.get_review_result(task_id)
        
        logger.info(f"Review result retrieved for task {task_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting review result: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取审查结果失败: {str(e)}"
        )

@router.get("/review/{task_id}/summary")
async def get_review_summary(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取审查摘要
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        审查摘要
    """
    try:
        result = review_service.get_review_result(task_id)
        
        # 只返回摘要部分
        summary_data = {
            "task_id": result["task_id"],
            "status": result["status"],
            "contract_type": result["contract_type"],
            "role": result["role"],
            "summary": result["summary"]
        }
        
        logger.info(f"Review summary retrieved for task {task_id}")
        return summary_data
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting review summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取审查摘要失败: {str(e)}"
        )

@router.get("/tasks")
async def list_tasks(
    status: str = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    
    Args:
        status: 过滤状态
        limit: 限制数量
        offset: 偏移量
        db: 数据库会话
    
    Returns:
        任务列表
    """
    try:
        from ..models import Task
        
        query = db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        tasks = query.offset(offset).limit(limit).all()
        
        task_list = []
        for task in tasks:
            task_data = {
                "id": task.id,
                "status": task.status,
                "contract_type": task.contract_type,
                "role": task.role,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
            task_list.append(task_data)
        
        return {
            "tasks": task_list,
            "total": len(task_list),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务列表失败: {str(e)}"
        )