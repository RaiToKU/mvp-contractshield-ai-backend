import os
import shutil
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
import pytesseract
from PIL import Image
import logging

# 使用更轻量的 PDF 处理库
try:
    import pdfplumber
    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        PDF_LIBRARY = None

from docx import Document

from ..models import Task, File
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class FileService:
    """文件处理服务"""
    
    def __init__(self):
        self.upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_and_enqueue(self, file: UploadFile, contract_type: str, user_id: int = None) -> int:
        """保存文件并创建任务"""
        db = SessionLocal()
        try:
            # 获取文件信息
            file_extension = os.path.splitext(file.filename)[1].lower()
            file_type = file_extension[1:] if file_extension else "unknown"
            
            # 获取文件大小
            file.file.seek(0, 2)  # 移动到文件末尾
            file_size = file.file.tell()
            file.file.seek(0)  # 重置到文件开头
            
            # 先创建一个临时任务来获取ID
            temp_task = Task(
                user_id=user_id,  # 允许为None
                file_name=file.filename,
                file_path="temp",  # 临时路径，稍后更新
                file_size=file_size,
                file_type=file_type,
                contract_type=contract_type,
                status="uploaded"
            )
            db.add(temp_task)
            db.commit()
            db.refresh(temp_task)
            
            # 现在我们有了任务ID，可以创建正确的文件路径
            file_extension = os.path.splitext(file.filename)[1].lower()
            filename = f"{temp_task.id}_{file.filename}"
            file_path = os.path.join(self.upload_dir, filename)
            
            # 更新任务的file_path
            temp_task.file_path = file_path
            db.commit()
            
            task = temp_task  # 重命名以保持后续代码一致
            
            # 保存文件
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
        if PDF_LIBRARY == "pdfplumber":
            return self._extract_with_pdfplumber(file_path)
        elif PDF_LIBRARY == "PyPDF2":
            return self._extract_with_pypdf2(file_path)
        else:
            logger.warning("No PDF library available, trying OCR")
            return self._ocr_pdf(file_path)
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """使用 pdfplumber 提取 PDF 文本"""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text.strip())
            return '\n\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}, trying OCR")
            return self._ocr_pdf(file_path)
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """使用 PyPDF2 提取 PDF 文本"""
        try:
            text_parts = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text.strip())
            return '\n\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}, trying OCR")
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