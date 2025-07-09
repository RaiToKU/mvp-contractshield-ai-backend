import os
import shutil
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
import pytesseract
from PIL import Image
from pdf2docx import Converter
from docx import Document
import logging

from ..models import Task, File
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class FileService:
    """文件处理服务"""
    
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_and_enqueue(self, file: UploadFile, contract_type: str, user_id: int = 1) -> int:
        """保存文件并创建任务"""
        db = SessionLocal()
        try:
            # 创建任务
            task = Task(
                user_id=user_id,
                contract_type=contract_type,
                status="PENDING"
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # 保存文件
            file_extension = os.path.splitext(file.filename)[1].lower()
            filename = f"{task.id}_{file.filename}"
            file_path = os.path.join(self.upload_dir, filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 记录文件信息
            file_record = File(
                task_id=task.id,
                filename=file.filename,
                path=file_path,
                file_type=file_extension[1:] if file_extension else "unknown"
            )
            db.add(file_record)
            db.commit()
            
            logger.info(f"File saved: {file_path}, Task ID: {task.id}")
            return task.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving file: {e}")
            raise
        finally:
            db.close()
    
    def extract_text_from_file(self, file_path: str) -> str:
        """从文件中提取文本"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension == '.docx':
                return self._extract_from_docx(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                return self._extract_from_image(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """从PDF提取文本"""
        # 先尝试直接转换为docx再提取
        temp_docx = file_path.replace('.pdf', '_temp.docx')
        try:
            cv = Converter(file_path)
            cv.convert(temp_docx)
            cv.close()
            
            text = self._extract_from_docx(temp_docx)
            os.remove(temp_docx)  # 清理临时文件
            return text
        except Exception as e:
            logger.warning(f"PDF to DOCX conversion failed: {e}, trying OCR")
            if os.path.exists(temp_docx):
                os.remove(temp_docx)
            
            # 如果转换失败，使用OCR
            return self._ocr_pdf(file_path)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """从DOCX提取文本"""
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        return '\n'.join(text_parts)
    
    def _extract_from_image(self, file_path: str) -> str:
        """从图片提取文本（OCR）"""
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text.strip()
    
    def _ocr_pdf(self, file_path: str) -> str:
        """对PDF进行OCR"""
        # 这里需要先将PDF转换为图片，然后OCR
        # 简化实现，实际项目中可能需要使用pdf2image等库
        logger.warning("PDF OCR not fully implemented")
        return ""
    
    def split_text_into_paragraphs(self, text: str) -> list[str]:
        """将文本分割为段落"""
        # 按双换行符分割段落
        paragraphs = text.split('\n\n')
        
        # 清理和过滤段落
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip().replace('\n', ' ')
            if len(para) > 20:  # 过滤太短的段落
                cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def update_file_ocr_text(self, task_id: int, ocr_text: str):
        """更新文件的OCR文本"""
        db = SessionLocal()
        try:
            file_record = db.query(File).filter(File.task_id == task_id).first()
            if file_record:
                file_record.ocr_text = ocr_text
                db.commit()
                logger.info(f"OCR text updated for task {task_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating OCR text: {e}")
        finally:
            db.close()

# 延迟初始化的文件服务实例
_file_service_instance = None

def get_file_service() -> FileService:
    """获取文件服务实例（延迟初始化）"""
    global _file_service_instance
    if _file_service_instance is None:
        _file_service_instance = FileService()
    return _file_service_instance