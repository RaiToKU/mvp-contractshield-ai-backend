#!/usr/bin/env python3
"""
API端点集成测试
"""

import pytest
import json
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models import User, Task, File
from app.database import get_db


@pytest.mark.integration
class TestAPIEndpoints:
    """API端点集成测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_api_docs_access(self, client):
        """测试API文档访问"""
        # 测试Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # 测试OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_upload_and_extract_entities_flow(self, client, db_session, sample_user):
        """测试文件上传和实体提取完整流程"""
        # 创建测试文件
        test_content = b"Test contract content with important clauses"
        test_file = io.BytesIO(test_content)
        
        # 上传文件
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.return_value = "test_file_path.pdf"
            
            with patch('app.services.file_service.FileService.extract_text') as mock_extract:
                mock_extract.return_value = "Extracted contract text"
                
                response = client.post(
                    "/api/upload",
                    files={"file": ("test.pdf", test_file, "application/pdf")},
                    data={"user_id": str(sample_user.id)}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "task_id" in data
                assert data["status"] == "uploaded"
                
                # 验证返回的task_id是有效的
                assert isinstance(data["task_id"], (int, str))

    def test_get_draft_roles_flow(self, client, db_session, sample_user, sample_file):
        """测试获取草稿角色完整流程"""
        # 创建任务
        task = Task(
            user_id=sample_user.id,
            file_id=sample_file.id,
            status="processing"
        )
        db_session.add(task)
        db_session.commit()
        
        with patch('app.services.ai_service.AIService.get_draft_roles') as mock_roles:
            mock_roles.return_value = {
                "roles": [
                    {"name": "甲方", "description": "合同主体"},
                    {"name": "乙方", "description": "合同对方"}
                ]
            }
            
            response = client.get(f"/api/tasks/{task.id}/draft-roles")
            
            assert response.status_code == 200
            data = response.json()
            assert "roles" in data
            assert len(data["roles"]) == 2
            
            # 验证角色数据结构
            for role in data["roles"]:
                assert "name" in role
                assert "description" in role

    def test_confirm_roles_flow(self, client, db_session, sample_user, sample_file):
        """测试确认角色完整流程"""
        # 创建任务
        task = Task(
            user_id=sample_user.id,
            file_id=sample_file.id,
            status="draft_roles_ready"
        )
        db_session.add(task)
        db_session.commit()
        
        roles_data = {
            "roles": [
                {"name": "甲方", "description": "合同主体"},
                {"name": "乙方", "description": "合同对方"}
            ]
        }
        
        with patch('app.services.review_service.ReviewService.start_review') as mock_review:
            mock_review.return_value = {"status": "review_started"}
            
            response = client.post(
                f"/api/tasks/{task.id}/confirm-roles",
                json=roles_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "review_started"
    
    def test_export_report_flow(self, client, db_session, sample_user, sample_file):
        """测试导出报告流程"""
        # 创建已完成的任务
        task = Task(
            user_id=sample_user.id,
            file_id=sample_file.id,
            status="completed"
        )
        db_session.add(task)
        db_session.commit()
        
        with patch('app.services.export_service.ExportService.generate_report') as mock_export:
            mock_export.return_value = b"PDF report content"
            
            response = client.get(f"/api/tasks/{task.id}/export")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert len(response.content) > 0


@pytest.mark.integration
class TestAPIErrorHandling:
    """API错误处理测试"""
    
    def test_api_not_found_errors(self, client):
        """测试404错误处理"""
        # 测试不存在的端点
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # 测试无效的任务ID
        response = client.get("/api/tasks/999999/draft-roles")
        assert response.status_code == 404
    
    def test_api_validation_errors(self, client):
        """测试请求验证错误"""
        # 测试无效的请求数据
        response = client.post("/api/tasks/1/confirm-roles", json={})
        assert response.status_code in [400, 422]
        
        # 测试缺少必需字段的文件上传
        response = client.post("/api/upload", files={})
        assert response.status_code in [400, 422]
    
    def test_api_method_not_allowed(self, client):
        """测试方法不允许错误"""
        # 对只支持GET的端点发送POST请求
        response = client.post("/health")
        assert response.status_code == 405
    
    def test_api_internal_server_error(self, client, db_session, sample_user):
        """测试内部服务器错误处理"""
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.side_effect = Exception("Internal error")
            
            test_file = io.BytesIO(b"test content")
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", test_file, "application/pdf")},
                data={"user_id": str(sample_user.id)}
            )
            
            assert response.status_code == 500


@pytest.mark.integration
class TestAPIAuthentication:
    """API认证测试"""
    
    def test_api_no_authentication_required(self, client):
        """测试无需认证的端点"""
        # 健康检查不需要认证
        response = client.get("/health")
        assert response.status_code == 200
        
        # API文档不需要认证
        response = client.get("/docs")
        assert response.status_code == 200
    
    @pytest.mark.skip(reason="认证功能尚未实现")
    def test_api_authentication_required(self, client):
        """测试需要认证的端点（预留）"""
        # 这里可以添加需要认证的端点测试
        pass


@pytest.mark.integration
class TestAPIPerformance:
    """API性能测试"""
    
    def test_api_response_time(self, client):
        """测试API响应时间"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # 响应时间应小于1秒
    
    @pytest.mark.slow
    def test_api_rate_limiting(self, client):
        """测试API速率限制（如果有的话）"""
        # 连续发送多个请求
        responses = []
        for i in range(10):
            response = client.get("/health")
            responses.append(response)
        
        # 目前假设没有速率限制，所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
    
    @pytest.mark.slow
    def test_api_concurrent_requests(self, client):
        """测试API并发请求处理"""
        import concurrent.futures
        import threading
        
        def make_request():
            return client.get("/health")
        
        # 使用线程池发送并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200


@pytest.mark.integration
class TestAPIWorkflow:
    """API工作流程测试"""

    def test_complete_workflow(self, client, db_session, sample_user):
        """测试完整的工作流程"""
        # 1. 上传文件
        test_content = b"Complete workflow test contract"
        test_file = io.BytesIO(test_content)
        
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.return_value = "workflow_test.pdf"
            
            with patch('app.services.file_service.FileService.extract_text') as mock_extract:
                mock_extract.return_value = "Workflow test contract text"
                
                upload_response = client.post(
                    "/api/upload",
                    files={"file": ("workflow.pdf", test_file, "application/pdf")},
                    data={"user_id": str(sample_user.id)}
                )
                
                assert upload_response.status_code == 200
                task_id = upload_response.json()["task_id"]
        
        # 2. 获取草稿角色
        with patch('app.services.ai_service.AIService.get_draft_roles') as mock_roles:
            mock_roles.return_value = {
                "roles": [{"name": "甲方", "description": "测试角色"}]
            }
            
            roles_response = client.get(f"/api/tasks/{task_id}/draft-roles")
            assert roles_response.status_code == 200
            roles_data = roles_response.json()
        
        # 3. 确认角色
        confirm_data = {
            "roles": [{"name": "甲方", "description": "确认的角色"}]
        }
        
        with patch('app.services.review_service.ReviewService.start_review') as mock_review:
            mock_review.return_value = {"status": "review_started"}
            
            confirm_response = client.post(
                f"/api/tasks/{task_id}/confirm-roles",
                json=confirm_data
            )
            
            assert confirm_response.status_code == 200
            
        # 4. 检查任务状态（模拟完成）
        with patch('app.services.review_service.ReviewService.get_task_status') as mock_status:
            mock_status.return_value = {"status": "completed"}
            
            status_response = client.get(f"/api/tasks/{task_id}/status")
            if status_response.status_code == 200:
                assert status_response.json()["status"] in ["completed", "processing"]
    
    def test_workflow_error_recovery(self, client, db_session, sample_user):
        """测试工作流程错误恢复"""
        # 模拟上传失败后的重试
        test_file = io.BytesIO(b"test content")
        
        # 第一次上传失败
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.side_effect = Exception("Upload failed")
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", test_file, "application/pdf")},
                data={"user_id": str(sample_user.id)}
            )
            
            assert response.status_code == 500
        
        # 第二次上传成功
        test_file.seek(0)  # 重置文件指针
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.return_value = "recovered_file.pdf"
            
            with patch('app.services.file_service.FileService.extract_text') as mock_extract:
                mock_extract.return_value = "Recovered file text"
                
                response = client.post(
                    "/api/upload",
                    files={"file": ("test.pdf", test_file, "application/pdf")},
                    data={"user_id": str(sample_user.id)}
                )
                
                assert response.status_code == 200
    
    def test_workflow_data_consistency(self, client, db_session, sample_user):
        """测试工作流程数据一致性"""
        # 上传文件并验证数据库状态
        test_file = io.BytesIO(b"consistency test")
        
        with patch('app.services.file_service.FileService.save_file') as mock_save:
            mock_save.return_value = "consistency_test.pdf"
            
            with patch('app.services.file_service.FileService.extract_text') as mock_extract:
                mock_extract.return_value = "Consistency test content"
                
                response = client.post(
                    "/api/upload",
                    files={"file": ("test.pdf", test_file, "application/pdf")},
                    data={"user_id": str(sample_user.id)}
                )
                
                assert response.status_code == 200
                task_id = response.json()["task_id"]
                
                # 验证数据库中的任务状态
                task = db_session.query(Task).filter(Task.id == task_id).first()
                assert task is not None
                assert task.user_id == sample_user.id
                assert task.status in ["uploaded", "processing"]