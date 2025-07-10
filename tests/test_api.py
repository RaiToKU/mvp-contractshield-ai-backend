import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
from io import BytesIO

from app.main import app
from tests.conftest import SAMPLE_CONTRACT_TEXT


@pytest.mark.api
class TestFileUploadAPI:
    """文件上传API测试"""
    
    def test_upload_file_success(self, client, sample_upload_file):
        """测试文件上传成功"""
        with patch('app.services.file_service.FileService.save_and_enqueue') as mock_save:
            mock_save.return_value = 123
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", sample_upload_file.file, "application/pdf")},
                data={"contract_type": "purchase", "user_id": "1"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == 123
            assert data["status"] == "uploaded"
    
    def test_upload_file_invalid_type(self, client):
        """测试上传无效文件类型"""
        file_content = b"test content"
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
            data={"contract_type": "purchase", "user_id": "1"}
        )
        
        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]
    
    def test_upload_file_missing_params(self, client, sample_upload_file):
        """测试上传文件缺少参数"""
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", sample_upload_file.file, "application/pdf")}
            # 缺少contract_type和user_id
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_file_service_error(self, client, sample_upload_file):
        """测试文件服务错误"""
        with patch('app.services.file_service.FileService.save_and_enqueue') as mock_save:
            mock_save.side_effect = Exception("Service error")
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", sample_upload_file.file, "application/pdf")},
                data={"contract_type": "purchase", "user_id": "1"}
            )
            
            assert response.status_code == 500


@pytest.mark.api
class TestContractReviewAPI:
    """合同审查API测试"""
    
    def test_get_draft_roles_success(self, client, sample_task):
        """测试获取草稿角色成功"""
        with patch('app.services.review_service.ReviewService.get_draft_roles') as mock_get_roles:
            mock_get_roles.return_value = {
                "candidates": [
                    {"role": "buyer", "description": "买方"},
                    {"role": "supplier", "description": "供应商"}
                ],
                "entities": {
                    "companies": ["测试公司A", "测试公司B"]
                }
            }
            
            response = client.get(f"/api/tasks/{sample_task.id}/draft-roles")
            
            assert response.status_code == 200
            data = response.json()
            assert "candidates" in data
            assert "entities" in data
            assert len(data["candidates"]) == 2
    
    def test_get_draft_roles_task_not_found(self, client):
        """测试获取草稿角色任务不存在"""
        with patch('app.services.review_service.ReviewService.get_draft_roles') as mock_get_roles:
            mock_get_roles.side_effect = ValueError("任务不存在")
            
            response = client.get("/api/tasks/999/draft-roles")
            
            assert response.status_code == 404
    
    def test_confirm_roles_success(self, client, sample_task):
        """测试确认角色成功"""
        with patch('app.services.review_service.ReviewService.confirm_roles') as mock_confirm:
            mock_confirm.return_value = {
                "status": "success",
                "role": "buyer",
                "party_names": ["测试公司A"],
                "auto_selected": True
            }
            
            response = client.post(
                f"/api/tasks/{sample_task.id}/confirm-roles",
                json={
                    "role": "buyer",
                    "selected_entity_index": 0
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["role"] == "buyer"
    
    def test_confirm_roles_manual_input(self, client, sample_task):
        """测试手动输入角色确认"""
        with patch('app.services.review_service.ReviewService.confirm_roles') as mock_confirm:
            mock_confirm.return_value = {
                "status": "success",
                "role": "supplier",
                "party_names": ["手动输入公司"],
                "auto_selected": False
            }
            
            response = client.post(
                f"/api/tasks/{sample_task.id}/confirm-roles",
                json={
                    "role": "supplier",
                    "party_names": ["手动输入公司"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["auto_selected"] is False
    
    @pytest.mark.asyncio
    async def test_start_review_success(self, client, sample_task):
        """测试开始审查成功"""
        with patch('app.services.review_service.ReviewService.start_review') as mock_start:
            mock_start.return_value = None
            
            response = client.post(f"/api/tasks/{sample_task.id}/start-review")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "审查已开始"
    
    def test_get_review_result_success(self, client, sample_task, sample_risk):
        """测试获取审查结果成功"""
        with patch('app.services.review_service.ReviewService.get_review_result') as mock_get_result:
            mock_get_result.return_value = {
                "task_id": sample_task.id,
                "status": "COMPLETED",
                "risks": [{
                    "title": sample_risk.title,
                    "risk_level": sample_risk.risk_level,
                    "summary": sample_risk.summary
                }],
                "summary": {
                    "total_risks": 1,
                    "high_risks": 1,
                    "medium_risks": 0,
                    "low_risks": 0
                }
            }
            
            response = client.get(f"/api/tasks/{sample_task.id}/result")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == sample_task.id
            assert "risks" in data
            assert "summary" in data


@pytest.mark.api
class TestReportExportAPI:
    """报告导出API测试"""
    
    def test_export_report_pdf_success(self, client, sample_task):
        """测试导出PDF报告成功"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/path/to/report.pdf"
            
            response = client.post(
                f"/api/tasks/{sample_task.id}/export",
                json={"format": "pdf"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["format"] == "pdf"
    
    def test_export_report_docx_success(self, client, sample_task):
        """测试导出DOCX报告成功"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/path/to/report.docx"
            
            response = client.post(
                f"/api/tasks/{sample_task.id}/export",
                json={"format": "docx"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["format"] == "docx"
    
    def test_export_report_txt_success(self, client, sample_task):
        """测试导出TXT报告成功"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/path/to/report.txt"
            
            response = client.post(
                f"/api/tasks/{sample_task.id}/export",
                json={"format": "txt"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data
            assert data["format"] == "txt"
    
    def test_export_report_invalid_format(self, client, sample_task):
        """测试导出无效格式报告"""
        response = client.post(
            f"/api/tasks/{sample_task.id}/export",
            json={"format": "invalid"}
        )
        
        assert response.status_code == 400
    
    def test_export_report_task_not_found(self, client):
        """测试导出报告任务不存在"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.side_effect = ValueError("任务不存在")
            
            response = client.post(
                "/api/tasks/999/export",
                json={"format": "pdf"}
            )
            
            assert response.status_code == 404
    
    def test_download_report_success(self, client, temp_dir):
        """测试下载报告成功"""
        # 创建临时文件
        test_file = temp_dir / "test_report.pdf"
        test_file.write_text("test content")
        
        with patch('app.api.export.os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = b"test content"
            
            response = client.get(f"/api/download/{test_file.name}")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
    
    def test_download_report_not_found(self, client):
        """测试下载报告文件不存在"""
        with patch('app.api.export.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.get("/api/download/nonexistent.pdf")
            
            assert response.status_code == 404


@pytest.mark.api
class TestHealthCheckAPI:
    """健康检查API测试"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_docs_accessible(self, client):
        """测试API文档可访问"""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_json_accessible(self, client):
        """测试OpenAPI JSON可访问"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data


@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试"""
    
    def test_full_workflow_success(self, client, sample_upload_file):
        """测试完整工作流程"""
        # 1. 上传文件
        with patch('app.services.file_service.FileService.save_and_enqueue') as mock_save:
            mock_save.return_value = 123
            
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", sample_upload_file.file, "application/pdf")},
                data={"contract_type": "purchase", "user_id": "1"}
            )
            
            assert upload_response.status_code == 200
            task_id = upload_response.json()["task_id"]
        
        # 2. 获取草稿角色
        with patch('app.services.review_service.ReviewService.get_draft_roles') as mock_get_roles:
            mock_get_roles.return_value = {
                "candidates": [{"role": "buyer", "description": "买方"}],
                "entities": {"companies": ["测试公司"]}
            }
            
            roles_response = client.get(f"/api/tasks/{task_id}/draft-roles")
            assert roles_response.status_code == 200
        
        # 3. 确认角色
        with patch('app.services.review_service.ReviewService.confirm_roles') as mock_confirm:
            mock_confirm.return_value = {
                "status": "success",
                "role": "buyer",
                "party_names": ["测试公司"]
            }
            
            confirm_response = client.post(
                f"/api/tasks/{task_id}/confirm-roles",
                json={"role": "buyer", "selected_entity_index": 0}
            )
            assert confirm_response.status_code == 200
        
        # 4. 开始审查
        with patch('app.services.review_service.ReviewService.start_review') as mock_start:
            mock_start.return_value = None
            
            review_response = client.post(f"/api/tasks/{task_id}/start-review")
            assert review_response.status_code == 200
        
        # 5. 导出报告
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/path/to/report.pdf"
            
            export_response = client.post(
                f"/api/tasks/{task_id}/export",
                json={"format": "pdf"}
            )
            assert export_response.status_code == 200
    
    def test_error_handling_chain(self, client, sample_upload_file):
        """测试错误处理链"""
        # 测试服务层错误如何传播到API层
        with patch('app.services.file_service.FileService.save_and_enqueue') as mock_save:
            mock_save.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", sample_upload_file.file, "application/pdf")},
                data={"contract_type": "purchase", "user_id": "1"}
            )
            
            assert response.status_code == 500
            assert "error" in response.json()