import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO

from tests.conftest import SAMPLE_UPLOAD_FILE, SAMPLE_CONTRACT_TEXT


class TestUploadAPI:
    """测试文件上传API"""
    
    def test_upload_file_success(self, client):
        """测试文件上传成功"""
        files = {
            "file": ("test.pdf", BytesIO(b"test content"), "application/pdf")
        }
        data = {
            "contract_type": "purchase"
        }
        
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.return_value = (1, "/test/path/test.pdf")
            
            response = client.post("/api/v1/upload", files=files, data=data)
            
            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result
            assert "message" in result
    
    def test_upload_file_invalid_type(self, client):
        """测试上传无效文件类型"""
        files = {
            "file": ("test.txt", BytesIO(b"test content"), "text/plain")
        }
        data = {
            "contract_type": "purchase"
        }
        
        response = client.post("/api/v1/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]
    
    def test_upload_file_too_large(self, client):
        """测试上传文件过大"""
        large_content = b"x" * (50 * 1024 * 1024 + 1)  # 超过50MB
        files = {
            "file": ("large.pdf", BytesIO(large_content), "application/pdf")
        }
        data = {
            "contract_type": "purchase"
        }
        
        response = client.post("/api/v1/upload", files=files, data=data)
        
        assert response.status_code == 400
        assert "文件大小超过限制" in response.json()["detail"]
    
    def test_get_upload_status(self, client, sample_task):
        """测试获取上传状态"""
        response = client.get(f"/api/v1/upload/status/{sample_task.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["task_id"] == sample_task.id
        assert "status" in result


class TestReviewAPI:
    """测试合同审查API"""
    
    def test_draft_roles_success(self, client, sample_task, sample_file):
        """测试获取草稿角色成功"""
        with patch('app.services.review_service.ReviewService.get_draft_roles') as mock_draft:
            mock_draft.return_value = {
                "detected_parties": ["甲方公司", "乙方公司"],
                "suggested_role": "buyer",
                "confidence": 0.8
            }
            
            response = client.post("/api/v1/draft_roles", json={"task_id": sample_task.id})
            
            assert response.status_code == 200
            result = response.json()
            assert "detected_parties" in result
            assert "suggested_role" in result
    
    def test_confirm_roles_success(self, client, sample_task):
        """测试确认角色成功"""
        with patch('app.services.review_service.ReviewService.confirm_roles') as mock_confirm:
            mock_confirm.return_value = True
            
            response = client.post("/api/v1/confirm_roles", json={
                "task_id": sample_task.id,
                "role": "buyer",
                "party_names": ["测试公司"]
            })
            
            assert response.status_code == 200
            result = response.json()
            assert result["message"] == "角色确认成功"
    
    def test_confirm_roles_invalid_role(self, client, sample_task):
        """测试确认无效角色"""
        response = client.post("/api/v1/confirm_roles", json={
            "task_id": sample_task.id,
            "role": "invalid_role",
            "party_names": ["测试公司"]
        })
        
        assert response.status_code == 400
        assert "无效的角色类型" in response.json()["detail"]
    
    def test_start_review_success(self, client, sample_task, sample_role):
        """测试开始审查成功"""
        with patch('app.services.review_service.ReviewService.start_review') as mock_review:
            mock_review.return_value = None
            
            response = client.post("/api/v1/review", json={"task_id": sample_task.id})
            
            assert response.status_code == 200
            result = response.json()
            assert result["message"] == "审查已开始"
    
    def test_get_review_results(self, client, sample_task, sample_risk):
        """测试获取审查结果"""
        with patch('app.services.review_service.ReviewService.get_review_results') as mock_results:
            mock_results.return_value = {
                "risks": [{
                    "id": sample_risk.id,
                    "risk_type": sample_risk.risk_type,
                    "risk_level": sample_risk.risk_level,
                    "description": sample_risk.description
                }],
                "total_risks": 1,
                "high_risks": 1,
                "medium_risks": 0,
                "low_risks": 0
            }
            
            response = client.get(f"/api/v1/review/{sample_task.id}")
            
            assert response.status_code == 200
            result = response.json()
            assert "risks" in result
            assert result["total_risks"] == 1
    
    def test_get_review_summary(self, client, sample_task):
        """测试获取审查摘要"""
        with patch('app.services.review_service.ReviewService.get_review_summary') as mock_summary:
            mock_summary.return_value = {
                "summary": "合同审查完成，发现1个高风险项目",
                "recommendations": ["建议修改付款条款"]
            }
            
            response = client.get(f"/api/v1/review/{sample_task.id}/summary")
            
            assert response.status_code == 200
            result = response.json()
            assert "summary" in result
            assert "recommendations" in result
    
    def test_get_tasks_list(self, client, sample_task):
        """测试获取任务列表"""
        response = client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        result = response.json()
        assert "tasks" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result


class TestExportAPI:
    """测试报告导出API"""
    
    def test_export_report_pdf(self, client, sample_task, sample_risk):
        """测试导出PDF报告"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/test/path/report.pdf"
            
            response = client.get(f"/api/v1/export/{sample_task.id}?format=pdf")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
    
    def test_export_report_docx(self, client, sample_task, sample_risk):
        """测试导出DOCX报告"""
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = "/test/path/report.docx"
            
            response = client.get(f"/api/v1/export/{sample_task.id}?format=docx")
            
            assert response.status_code == 200
            assert "application/vnd.openxmlformats" in response.headers["content-type"]
    
    def test_export_report_txt(self, client, sample_task, sample_risk):
        """测试导出TXT报告"""
        with patch('app.services.export_service.ExportService.generate_simple_report') as mock_export:
            mock_export.return_value = "简化报告内容"
            
            response = client.get(f"/api/v1/export/{sample_task.id}?format=txt")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    def test_preview_report(self, client, sample_task, sample_risk):
        """测试预览报告"""
        with patch('app.services.export_service.ExportService.get_report_data') as mock_preview:
            mock_preview.return_value = {
                "task_info": {"id": sample_task.id},
                "risks": [{"id": sample_risk.id}]
            }
            
            response = client.get(f"/api/v1/export/{sample_task.id}/preview")
            
            assert response.status_code == 200
            result = response.json()
            assert "task_info" in result
            assert "risks" in result
    
    def test_get_export_formats(self, client, sample_task):
        """测试获取导出格式"""
        response = client.get(f"/api/v1/export/{sample_task.id}/formats")
        
        assert response.status_code == 200
        result = response.json()
        assert "formats" in result
        assert "pdf" in result["formats"]
        assert "docx" in result["formats"]
        assert "txt" in result["formats"]
    
    def test_cleanup_export_files(self, client, sample_task):
        """测试清理导出文件"""
        with patch('app.services.export_service.ExportService.cleanup_files') as mock_cleanup:
            mock_cleanup.return_value = True
            
            response = client.delete(f"/api/v1/export/{sample_task.id}/files")
            
            assert response.status_code == 200
            result = response.json()
            assert result["message"] == "导出文件已清理"


class TestHealthAPI:
    """测试健康检查API"""
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "ContractShield AI Backend"
        assert "version" in result
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "healthy"
        assert "timestamp" in result