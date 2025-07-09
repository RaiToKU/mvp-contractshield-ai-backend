from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging

from ..database import get_db
from ..services.review_service import review_service
from ..services.export_service import export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["export"])

@router.get("/export/{task_id}")
async def export_report(
    task_id: int,
    format: str = Query(default="docx", regex="^(pdf|docx|txt)$"),
    db: Session = Depends(get_db)
):
    """
    导出审查报告
    
    Args:
        task_id: 任务ID
        format: 导出格式 (pdf, docx, txt)
        db: 数据库会话
    
    Returns:
        文件下载响应
    """
    try:
        # 获取审查结果
        review_data = review_service.get_review_result(task_id)
        
        # 检查任务状态
        if review_data["status"] != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"任务尚未完成，当前状态: {review_data['status']}"
            )
        
        # 生成报告
        if format.lower() == "txt":
            file_path = export_service.generate_simple_report(review_data)
        else:
            file_path = export_service.generate_report(review_data, format)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=500,
                detail="报告生成失败"
            )
        
        # 设置文件名
        filename = os.path.basename(file_path)
        
        # 设置媒体类型
        media_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain"
        }
        
        media_type = media_type_map.get(format.lower(), "application/octet-stream")
        
        logger.info(f"Report exported for task {task_id}, format: {format}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"导出报告失败: {str(e)}"
        )

@router.get("/export/{task_id}/preview")
async def preview_report(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    预览报告内容（JSON格式）
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        报告预览数据
    """
    try:
        # 获取审查结果
        review_data = review_service.get_review_result(task_id)
        
        # 检查任务状态
        if review_data["status"] != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"任务尚未完成，当前状态: {review_data['status']}"
            )
        
        # 构建预览数据
        preview_data = {
            "basic_info": {
                "task_id": review_data["task_id"],
                "contract_type": review_data["contract_type"],
                "role": review_data["role"],
                "status": review_data["status"]
            },
            "summary": review_data["summary"],
            "risks": review_data["risks"],
            "export_formats": ["pdf", "docx", "txt"]
        }
        
        logger.info(f"Report preview generated for task {task_id}")
        return preview_data
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report preview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成报告预览失败: {str(e)}"
        )

@router.get("/export/{task_id}/formats")
async def get_export_formats(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    获取可用的导出格式
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        可用的导出格式列表
    """
    try:
        # 检查任务是否存在
        review_data = review_service.get_review_result(task_id)
        
        formats = [
            {
                "format": "pdf",
                "name": "PDF文档",
                "description": "便携式文档格式，适合打印和分享",
                "available": True
            },
            {
                "format": "docx",
                "name": "Word文档",
                "description": "Microsoft Word格式，可编辑",
                "available": True
            },
            {
                "format": "txt",
                "name": "纯文本",
                "description": "简单的文本格式",
                "available": True
            }
        ]
        
        return {
            "task_id": task_id,
            "formats": formats
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting export formats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取导出格式失败: {str(e)}"
        )

@router.delete("/export/{task_id}/files")
async def cleanup_export_files(
    task_id: int,
    db: Session = Depends(get_db)
):
    """
    清理导出文件
    
    Args:
        task_id: 任务ID
        db: 数据库会话
    
    Returns:
        清理结果
    """
    try:
        import glob
        
        # 查找相关的导出文件
        export_dir = export_service.export_dir
        pattern = os.path.join(export_dir, f"contract_review_{task_id}_*")
        files = glob.glob(pattern)
        
        deleted_files = []
        for file_path in files:
            try:
                os.remove(file_path)
                deleted_files.append(os.path.basename(file_path))
                logger.info(f"Deleted export file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        return {
            "task_id": task_id,
            "deleted_files": deleted_files,
            "count": len(deleted_files)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up export files: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清理导出文件失败: {str(e)}"
        )