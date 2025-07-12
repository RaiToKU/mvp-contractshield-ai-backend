import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import os
from io import BytesIO
from datetime import datetime

from app.services.file_service import FileService
from app.services.ai_service import AIService
from app.services.review_service import ReviewService
from app.services.export_service import ExportService
from tests.conftest import SAMPLE_CONTRACT_TEXT


@pytest.mark.unit
class TestFileService:
    """文件服务单元测试"""
    
    @pytest.mark.asyncio
    async def test_save_and_enqueue_success(self, file_service, sample_upload_file, mock_file_operations):
        """测试文件保存和任务创建成功"""
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            
            # 模拟Task创建
            def mock_add_side_effect(obj):
                if hasattr(obj, 'id'):
                    obj.id = 123
            mock_db.add.side_effect = mock_add_side_effect
            
            task_id = await file_service.save_and_enqueue(sample_upload_file, "purchase", 1)
            
            assert mock_db.add.call_count >= 1
            assert mock_db.commit.call_count >= 1
            mock_file_operations['copy'].assert_called_once()
    
    def test_extract_text_from_pdf(self, file_service):
        """测试PDF文本提取"""
        file_path = "/test/path/test.pdf"
        
        # 模拟 pdfplumber 提取
        with patch('app.services.file_service.PDF_LIBRARY', 'pdfplumber'), \
             patch('pdfplumber.open') as mock_open:
            
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "PDF页面文本内容"
            mock_pdf.pages = [mock_page]
            mock_open.return_value.__enter__.return_value = mock_pdf
            
            text = file_service.extract_text_from_file(file_path)
            
            assert "PDF页面文本内容" in text
    
    def test_extract_text_from_docx(self, file_service):
        """测试DOCX文本提取"""
        file_path = "/test/path/test.docx"
        
        with patch('docx.Document') as mock_doc:
            mock_doc.return_value.paragraphs = [
                MagicMock(text="DOCX段落1"),
                MagicMock(text="DOCX段落2")
            ]
            
            text = file_service.extract_text_from_file(file_path)
            
            assert "DOCX段落1" in text
            assert "DOCX段落2" in text
    
    def test_extract_text_from_image_with_ocr(self, file_service):
        """测试图片OCR文本提取"""
        file_path = "/test/path/test.jpg"
        
        with patch('PIL.Image.open') as mock_image, \
             patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "OCR提取的文本"
            
            text = file_service.extract_text_from_file(file_path)
            
            assert text == "OCR提取的文本"
    
    def test_split_into_paragraphs(self, file_service):
        """测试文本分段"""
        text = "第一段内容比较长的内容。\n\n第二段内容也比较长的内容。\n\n第三段内容同样比较长的内容。"
        
        paragraphs = file_service.split_text_into_paragraphs(text)
        
        assert len(paragraphs) == 3
        assert "第一段" in paragraphs[0]
        assert "第二段" in paragraphs[1]
        assert "第三段" in paragraphs[2]
    
    def test_extract_text_unsupported_format(self, file_service):
        """测试不支持的文件格式"""
        file_path = "/test/path/test.xyz"
        
        text = file_service.extract_text_from_file(file_path)
        
        assert text == ""
    
    def test_extract_from_image_error_handling(self, file_service):
        """测试图片OCR错误处理"""
        file_path = "/test/path/test.jpg"
        
        with patch('PIL.Image.open') as mock_image, \
             patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.side_effect = Exception("OCR failed")
            
            text = file_service.extract_text_from_file(file_path)
            
            assert text == ""


@pytest.mark.unit
class TestAIService:
    """AI服务单元测试"""
    
    @pytest.mark.asyncio
    async def test_get_embedding_async(self, ai_service):
        """测试异步获取嵌入向量"""
        result = await ai_service.get_embedding("测试文本")
        
        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)
    
    def test_get_embedding_sync(self, ai_service):
        """测试同步获取嵌入向量"""
        result = ai_service.get_embedding_sync("测试文本")
        
        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)
    
    def test_embedding_consistency(self, ai_service):
        """测试嵌入向量一致性"""
        text = "测试文本"
        result1 = ai_service.get_embedding_sync(text)
        result2 = ai_service.get_embedding_sync(text)
        
        assert result1 == result2  # 相同文本应该产生相同的向量
    
    def test_different_texts_different_embeddings(self, ai_service):
        """测试不同文本产生不同向量"""
        text1 = "文本一"
        text2 = "文本二"
        
        result1 = ai_service.get_embedding_sync(text1)
        result2 = ai_service.get_embedding_sync(text2)
        
        assert result1 != result2  # 不同文本应该产生不同的向量


@pytest.mark.unit
class TestReviewService:
    """审查服务单元测试"""
    
    def test_get_draft_roles_with_entities(self, review_service, sample_task):
        """测试获取草稿角色（有实体数据）"""
        # 设置任务实体数据
        sample_task.entities_data = {
            "companies": ["测试公司A", "测试公司B"],
            "persons": ["张三", "李四"],
            "organizations": ["政府机构"]
        }
        
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            
            result = review_service.get_draft_roles(sample_task.id)
            
            assert "candidates" in result
            assert "entities" in result
            assert len(result["candidates"]) > 0
            assert "companies" in result["entities"]
    
    def test_get_draft_roles_no_entities(self, review_service, sample_task):
        """测试获取草稿角色（无实体数据）"""
        sample_task.entities_data = None
        
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            
            result = review_service.get_draft_roles(sample_task.id)
            
            assert "candidates" in result
            assert "entities" in result
            assert len(result["candidates"]) > 0
            assert result["entities"] == {}
    
    def test_confirm_roles_auto_selection(self, review_service, sample_task):
        """测试角色确认自动选择"""
        sample_task.entities_data = {
            "companies": ["测试公司A", "测试公司B"]
        }
        
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            
            result = review_service.confirm_roles(
                task_id=sample_task.id,
                role="buyer",
                party_names=None,
                selected_entity_index=0
            )
            
            assert result["status"] == "success"
            assert result["role"] == "buyer"
            assert result["party_names"] == ["测试公司A"]
            assert result["auto_selected"] is True
    
    def test_confirm_roles_manual_selection(self, review_service, sample_task):
        """测试角色确认手动选择"""
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            
            result = review_service.confirm_roles(
                task_id=sample_task.id,
                role="supplier",
                party_names=["手动输入公司"]
            )
            
            assert result["status"] == "success"
            assert result["role"] == "supplier"
            assert result["party_names"] == ["手动输入公司"]
            assert result["auto_selected"] is False


@pytest.mark.unit
class TestExportService:
    """导出服务单元测试"""
    
    def test_generate_report_pdf(self, export_service, sample_task, sample_risk, temp_dir):
        """测试生成PDF报告"""
        with patch('app.database.SessionLocal') as mock_session, \
             patch('app.services.export_service.ExportService._create_pdf_report') as mock_pdf:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            
            # 模拟查询结果
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            mock_db.query.return_value.filter.return_value.all.return_value = [sample_risk]
            
            # 模拟PDF创建
            pdf_path = temp_dir / "test_report.pdf"
            mock_pdf.return_value = str(pdf_path)
            
            result = export_service.generate_report(sample_task.id, "pdf")
            
            assert result is not None
            mock_pdf.assert_called_once()
    
    def test_generate_report_docx(self, export_service, sample_task, sample_risk, temp_dir):
        """测试生成DOCX报告"""
        with patch('app.database.SessionLocal') as mock_session, \
             patch('app.services.export_service.ExportService._create_docx_report') as mock_docx:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            
            # 模拟查询结果
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            mock_db.query.return_value.filter.return_value.all.return_value = [sample_risk]
            
            # 模拟DOCX创建
            docx_path = temp_dir / "test_report.docx"
            mock_docx.return_value = str(docx_path)
            
            result = export_service.generate_report(sample_task.id, "docx")
            
            assert result is not None
            mock_docx.assert_called_once()
    
    def test_generate_report_txt(self, export_service, sample_task, sample_risk, temp_dir):
        """测试生成TXT报告"""
        with patch('app.database.SessionLocal') as mock_session, \
             patch('app.services.export_service.ExportService._create_txt_report') as mock_txt:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            
            # 模拟查询结果
            mock_db.query.return_value.filter.return_value.first.return_value = sample_task
            mock_db.query.return_value.filter.return_value.all.return_value = [sample_risk]
            
            # 模拟TXT创建
            txt_path = temp_dir / "test_report.txt"
            mock_txt.return_value = str(txt_path)
            
            result = export_service.generate_report(sample_task.id, "txt")
            
            assert result is not None
            mock_txt.assert_called_once()
    
    def test_generate_report_invalid_format(self, export_service, sample_task):
        """测试生成报告无效格式"""
        with pytest.raises(ValueError, match="不支持的导出格式"):
            export_service.generate_report(sample_task.id, "invalid")
    
    def test_generate_report_task_not_found(self, export_service):
        """测试生成报告任务不存在"""
        with patch('app.database.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(ValueError, match="任务不存在"):
                export_service.generate_report(999, "pdf")