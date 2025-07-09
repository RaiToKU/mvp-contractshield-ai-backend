from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..services.file_service import get_file_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])

@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    contract_type: str = Form(default="其他"),
    db: Session = Depends(get_db)
):
    """
    上传合同文件
    
    Args:
        file: 上传的文件
        contract_type: 合同类型
        db: 数据库会话
    
    Returns:
        包含task_id的响应
    """
    try:
        # 验证文件类型
        allowed_extensions = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png']
        file_extension = None
        if file.filename:
            file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if not file_extension or file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 验证文件大小（50MB限制）
        max_size = 50 * 1024 * 1024  # 50MB
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头
        
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail="文件大小超过50MB限制"
            )
        
        # 保存文件并创建任务
        task_id = await get_file_service().save_and_enqueue(
            file=file,
            contract_type=contract_type,
            user_id=1  # 暂时使用固定用户ID
        )
        
        # 自动进行文本提取和实体提取
        try:
            from ..models import File as FileModel, Task
            from ..services.ai_service import get_ai_service
            from sqlalchemy import func
            
            file_record = db.query(FileModel).filter(FileModel.task_id == task_id).first()
            if file_record:
                # 更新任务状态为提取中
                task = db.query(Task).filter(Task.id == task_id).first()
                if task:
                    task.status = "EXTRACTING"
                    db.commit()
                
                # OCR文本提取
                ocr_text = get_file_service().extract_text_from_file(file_record.path)
                get_file_service().update_file_ocr_text(task_id, ocr_text)
                logger.info(f"Text extracted for task {task_id}")
                
                # 实体提取
                if ocr_text and len(ocr_text.strip()) > 50:  # 确保有足够的文本内容
                    entities = get_ai_service().extract_entities_ner(ocr_text)
                    
                    # 保存实体数据到任务表
                    task.entities_data = entities
                    task.entities_extracted_at = func.now()
                    task.status = "ENTITY_READY"
                    db.commit()
                    logger.info(f"Entities extracted for task {task_id}: {entities}")
                else:
                    logger.warning(f"Insufficient text content for entity extraction: {len(ocr_text) if ocr_text else 0} chars")
                    task.status = "ENTITY_READY"  # 即使没有实体也标记为准备好
                    db.commit()
        except Exception as e:
            logger.warning(f"Text/Entity extraction failed for task {task_id}: {e}")
            # 确保任务状态不会卡在EXTRACTING
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if task and task.status == "EXTRACTING":
                    task.status = "PENDING"
                    db.commit()
            except:
                pass
        
        logger.info(f"File uploaded successfully, task_id: {task_id}")
        
        return {
            "task_id": task_id,
            "message": "文件上传成功，文本提取完成",
            "filename": file.filename,
            "contract_type": contract_type,
            "next_step": "请调用 /api/v1/draft_roles 获取角色识别结果"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/upload/status/{task_id}")
async def get_upload_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取上传任务状态
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        任务状态信息
    """
    try:
        from ..models import Task, File
        
        # 查询任务
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"任务 {task_id} 不存在"
            )
        
        # 查询文件信息
        file_record = db.query(File).filter(File.task_id == task_id).first()
        
        return {
            "task_id": task_id,
            "status": task.status,
            "contract_type": task.contract_type,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "file_info": {
                "filename": file_record.filename if file_record else None,
                "file_type": file_record.file_type if file_record else None,
                "has_ocr_text": bool(file_record.ocr_text) if file_record else False
            } if file_record else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upload status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )