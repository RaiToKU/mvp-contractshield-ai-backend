# ContractShield AI Backend API 接口文档

## 基础信息
- **服务名称**: ContractShield AI Backend
- **版本**: v1.0.0
- **基础URL**: `/api/v1`
- **文档地址**: `/docs` (Swagger UI), `/redoc` (ReDoc)

## 系统接口

### 1. 根路径
- **接口**: `GET /`
- **描述**: 获取API基本信息
- **响应**:
```json
{
  "name": "ContractShield AI Backend",
  "version": "1.0.0",
  "description": "合同审查AI后端服务",
  "status": "running",
  "endpoints": {
    "docs": "/docs",
    "redoc": "/redoc",
    "health": "/health",
    "api": "/api/v1"
  }
}
```

### 2. 健康检查
- **接口**: `GET /health`
- **描述**: 检查服务健康状态
- **响应**:
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "ContractShield AI Backend",
  "version": "1.0.0",
  "timestamp": "1703123456789"
}
```

### 3. API版本信息
- **接口**: `GET /api/v1`
- **描述**: 获取API版本和端点信息
- **响应**:
```json
{
  "version": "v1",
  "endpoints": {
    "upload": "/api/v1/upload",
    "draft_roles": "/api/v1/draft_roles",
    "confirm_roles": "/api/v1/confirm_roles",
    "review": "/api/v1/review",
    "export": "/api/v1/export/{task_id}",
    "websocket": "/ws/review/{task_id}"
  },
  "supported_formats": {
    "upload": ["pdf", "docx", "doc", "jpg", "jpeg", "png"],
    "export": ["pdf", "docx", "txt"]
  }
}
```

## 文件上传模块

### 1. 上传合同文件
- **接口**: `POST /api/v1/upload`
- **描述**: 上传合同文件并创建审查任务，自动进行文本提取和实体识别
- **请求参数**:
  - `file` (FormData): 文件对象，支持 pdf/docx/doc/jpg/jpeg/png
  - `contract_type` (FormData): 合同类型，默认"其他"
- **文件限制**: 最大50MB
- **功能特性**:
  - 自动文本提取（OCR支持）
  - 自动实体识别和存储
  - 支持多种文件格式
- **响应**:
```json
{
  "task_id": 123,
  "message": "文件上传成功，文本提取完成",
  "filename": "contract.pdf",
  "contract_type": "销售合同",
  "entities_extracted": true,
  "next_step": "请调用 /api/v1/draft_roles 获取角色识别结果"
}
```

### 2. 获取上传状态
- **接口**: `GET /api/v1/upload/status/{task_id}`
- **描述**: 查询上传任务的状态
- **路径参数**:
  - `task_id`: 任务ID
- **响应**:
```json
{
  "task_id": 123,
  "status": "PENDING",
  "contract_type": "销售合同",
  "created_at": "2023-12-01T10:00:00",
  "file_info": {
    "filename": "contract.pdf",
    "file_type": "pdf",
    "has_ocr_text": true
  }
}
```

## 实体识别模块

### 实体数据存储功能
- **功能描述**: 系统在文件上传后自动进行实体识别，提取合同中的公司、人员等关键信息
- **存储字段**: 
  - `entities_data`: JSON格式存储提取的实体信息
  - `entities_extracted_at`: 实体提取时间戳
- **支持的实体类型**:
  - `companies`: 公司/组织名称
  - `persons`: 人员姓名
  - `locations`: 地址/位置信息
  - `dates`: 日期信息
- **自动触发**: 文件上传成功后自动执行
- **用途**: 为角色识别和合同审查提供基础数据

## 审查流程模块

### 1. 获取角色识别草稿
- **接口**: `POST /api/v1/draft_roles`
- **描述**: 基于合同内容和实体识别结果生成角色候选列表
- **请求体**:
```json
{
  "task_id": 123
}
```
- **响应**:
```json
{
  "task_id": 123,
  "candidates": [
    {
      "role": "buyer",
      "label": "采购方",
      "description": "合同中的采购方，负责购买商品或服务",
      "entities": ["甲方公司", "购买方公司"]
    },
    {
      "role": "seller",
      "label": "供应方",
      "description": "合同中的供应方，负责提供商品或服务",
      "entities": ["乙方公司", "销售方公司"]
    }
  ],
  "entities": {
    "companies": ["甲方公司", "乙方公司"],
    "persons": ["张三", "李四"]
  },
  "contract_type": "采购合同"
}
```

### 2. 确认角色信息
- **接口**: `POST /api/v1/confirm_roles`
- **描述**: 确认用户在合同中的角色
- **请求体**:
```json
{
  "task_id": 123,
  "role": "buyer",
  "party_names": ["甲方公司", "购买方"],
  "selected_entity_index": 0
}
```
- **请求参数说明**:
  - `task_id`: 任务ID（必需）
  - `role`: 角色类型（必需）
  - `party_names`: 主体名称列表（可选，如果不提供则从实体数据中自动选择）
  - `selected_entity_index`: 选择的实体索引，默认为0（可选）
- **支持的角色**: buyer, seller, client, provider, party_a, party_b, landlord, tenant
- **响应**:
```json
{
  "task_id": 123,
  "role": "buyer",
  "party_names": ["甲方公司", "购买方"],
  "status": "READY",
  "message": "角色确认成功，可以开始审查"
}
```

### 3. 手动设置主体名称
- **接口**: `POST /api/v1/manual_party_names`
- **描述**: 手动设置主体名称（当实体识别失败时的备选方案）
- **请求体**:
```json
{
  "task_id": 123,
  "role": "buyer",
  "party_names": ["甲方公司", "购买方"]
}
```
- **响应**:
```json
{
  "task_id": 123,
  "role": "buyer",
  "party_names": ["甲方公司", "购买方"],
  "status": "READY",
  "message": "主体名称设置成功，可以开始审查"
}
```

### 4. 开始合同审查
- **接口**: `POST /api/v1/review`
- **描述**: 启动合同审查流程（后台异步执行）
- **请求体**:
```json
{
  "task_id": 123
}
```
- **响应**:
```json
{
  "task_id": 123,
  "status": "IN_PROGRESS",
  "message": "审查已开始，请通过WebSocket监听进度"
}
```

### 5. 获取审查结果
- **接口**: `GET /api/v1/review/{task_id}`
- **描述**: 获取完整的审查结果
- **路径参数**:
  - `task_id`: 任务ID
- **响应**:
```json
{
  "task_id": 123,
  "status": "COMPLETED",
  "contract_type": "销售合同",
  "role": "buyer",
  "summary": {
    "total_risks": 5,
    "high_risks": 2,
    "medium_risks": 2,
    "low_risks": 1,
    "overall_assessment": "中等风险"
  },
  "risks": [
    {
      "clause_id": "CLAUSE_001",
      "title": "付款条款风险",
      "risk_level": "HIGH",
      "summary": "付款期限过于严格...",
      "suggestion": "建议协商延长付款期限...",
      "statutes": [
        {
          "statute_ref": "合同法第XX条",
          "statute_text": "相关法条内容..."
        }
      ]
    }
  ]
}
```

### 6. 获取审查摘要
- **接口**: `GET /api/v1/review/{task_id}/summary`
- **描述**: 获取审查结果摘要（不包含详细风险）
- **路径参数**:
  - `task_id`: 任务ID
- **响应**:
```json
{
  "task_id": 123,
  "status": "COMPLETED",
  "contract_type": "销售合同",
  "role": "buyer",
  "summary": {
    "total_risks": 5,
    "high_risks": 2,
    "medium_risks": 2,
    "low_risks": 1,
    "overall_assessment": "中等风险"
  }
}
```

### 7. 获取任务列表
- **接口**: `GET /api/v1/tasks`
- **描述**: 获取任务列表
- **查询参数**:
  - `status` (可选): 过滤状态
  - `limit` (可选): 限制数量，默认10
  - `offset` (可选): 偏移量，默认0
- **响应**:
```json
{
  "tasks": [
    {
      "id": 123,
      "status": "COMPLETED",
      "contract_type": "销售合同",
      "role": "buyer",
      "created_at": "2023-12-01T10:00:00",
      "updated_at": "2023-12-01T11:00:00"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## 报告导出模块

### 1. 导出审查报告
- **接口**: `GET /api/v1/export/{task_id}`
- **描述**: 导出审查报告文件，支持多种格式下载
- **请求方法**: GET
- **路径参数**:
  - `task_id` (integer, required): 任务ID，必须是已完成的审查任务
- **查询参数**:
  - `format` (string, optional): 导出格式，可选值：
    - `pdf`: PDF文档格式（默认）
    - `docx`: Microsoft Word文档格式
    - `txt`: 纯文本格式
- **请求头**:
  - `Accept`: application/octet-stream 或 application/pdf 或 application/vnd.openxmlformats-officedocument.wordprocessingml.document
- **成功响应** (200 OK):
  - **Content-Type**: 根据格式返回对应的MIME类型
    - PDF: `application/pdf`
    - DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - TXT: `text/plain; charset=utf-8`
  - **Content-Disposition**: `attachment; filename="contract_review_{task_id}_{timestamp}.{format}"`
  - **响应体**: 二进制文件流
- **错误响应**:
  - **404 Not Found**: 任务不存在或报告未生成
  ```json
  {
    "error": true,
    "message": "任务不存在或报告未生成",
    "status_code": 404
  }
  ```
  - **400 Bad Request**: 不支持的导出格式
  ```json
  {
    "error": true,
    "message": "不支持的导出格式: {format}",
    "status_code": 400,
    "supported_formats": ["pdf", "docx", "txt"]
  }
  ```
  - **422 Unprocessable Entity**: 任务状态不允许导出
  ```json
  {
    "error": true,
    "message": "任务状态不允许导出，当前状态: {status}",
    "status_code": 422,
    "required_status": "COMPLETED"
  }
  ```

### 2. 预览报告内容
- **接口**: `GET /api/v1/export/{task_id}/preview`
- **描述**: 预览报告内容（JSON格式），不生成实际文件
- **请求方法**: GET
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **成功响应** (200 OK):
```json
{
  "basic_info": {
    "task_id": 123,
    "contract_type": "销售合同",
    "role": "buyer",
    "status": "COMPLETED",
    "created_at": "2023-12-01T10:00:00Z",
    "updated_at": "2023-12-01T11:00:00Z",
    "generated_at": "2023-12-01T11:05:00Z"
  },
  "summary": {
    "total_risks": 8,
    "high_risks": 3,
    "medium_risks": 3,
    "low_risks": 2,
    "overall_assessment": "高风险",
    "key_concerns": [
      "付款条款过于严格",
      "违约责任不对等",
      "知识产权条款模糊"
    ]
  },
  "risks": [
    {
      "clause_id": "CLAUSE_001",
      "title": "付款条款风险",
      "risk_level": "HIGH",
      "category": "财务风险",
      "summary": "付款期限过于严格，可能导致资金周转困难",
      "detailed_analysis": "合同要求在收到发票后7天内付款，这对买方的资金流动性提出了很高要求...",
      "suggestion": "建议协商延长付款期限至30天，并增加分期付款条款",
      "impact_score": 8.5,
      "probability": "高",
      "statutes": [
        {
          "statute_ref": "《民法典》第509条",
          "statute_text": "当事人应当按照约定全面履行自己的义务",
          "relevance": "直接相关"
        }
      ],
      "clause_text": "买方应在收到发票后7日内支付全部款项",
      "line_numbers": [15, 16]
    }
  ],
  "export_formats": ["pdf", "docx", "txt"],
  "report_metadata": {
    "total_pages": 12,
    "word_count": 3500,
    "language": "zh-CN",
    "template_version": "v2.1"
  }
}
```
- **错误响应**:
  - **404 Not Found**: 任务不存在
  ```json
  {
    "error": true,
    "message": "任务不存在",
    "status_code": 404
  }
  ```
  - **422 Unprocessable Entity**: 任务未完成
  ```json
  {
    "error": true,
    "message": "任务尚未完成，无法预览报告",
    "status_code": 422,
    "current_status": "IN_PROGRESS"
  }
  ```

### 3. 获取导出格式
- **接口**: `GET /api/v1/export/{task_id}/formats`
- **描述**: 获取可用的导出格式及其详细信息
- **请求方法**: GET
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **成功响应** (200 OK):
```json
{
  "task_id": 123,
  "formats": [
    {
      "format": "pdf",
      "name": "PDF文档",
      "description": "便携式文档格式，适合打印和分享",
      "mime_type": "application/pdf",
      "file_extension": ".pdf",
      "available": true,
      "estimated_size": "2.5MB",
      "features": [
        "保持格式不变",
        "支持打印",
        "跨平台兼容",
        "包含书签导航"
      ]
    },
    {
      "format": "docx",
      "name": "Word文档",
      "description": "Microsoft Word格式，可编辑和批注",
      "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "file_extension": ".docx",
      "available": true,
      "estimated_size": "1.8MB",
      "features": [
        "可编辑内容",
        "支持批注",
        "格式丰富",
        "兼容Office套件"
      ]
    },
    {
      "format": "txt",
      "name": "纯文本",
      "description": "简单的文本格式，兼容性最佳",
      "mime_type": "text/plain",
      "file_extension": ".txt",
      "available": true,
      "estimated_size": "150KB",
      "features": [
        "文件小巧",
        "通用兼容",
        "易于处理",
        "纯文本内容"
      ]
    }
  ],
  "default_format": "pdf",
  "total_formats": 3
}
```
- **错误响应**:
  - **404 Not Found**: 任务不存在
  ```json
  {
    "error": true,
    "message": "任务不存在",
    "status_code": 404
  }
  ```

### 4. 生成报告
- **接口**: `POST /api/v1/export/{task_id}/generate`
- **描述**: 手动触发报告生成（通常在审查完成后自动生成）
- **请求方法**: POST
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **请求体**:
```json
{
  "formats": ["pdf", "docx"],
  "force_regenerate": false,
  "include_appendix": true,
  "template_options": {
    "include_cover_page": true,
    "include_toc": true,
    "include_summary": true,
    "risk_detail_level": "detailed"
  }
}
```
- **成功响应** (200 OK):
```json
{
  "task_id": 123,
  "status": "generating",
  "message": "报告生成已启动",
  "estimated_completion": "2023-12-01T11:10:00Z",
  "formats_requested": ["pdf", "docx"],
  "generation_id": "gen_123_20231201_110500"
}
```
- **错误响应**:
  - **409 Conflict**: 报告正在生成中
  ```json
  {
    "error": true,
    "message": "报告正在生成中，请稍后再试",
    "status_code": 409,
    "current_generation_id": "gen_123_20231201_110300"
  }
  ```

### 5. 清理导出文件
- **接口**: `DELETE /api/v1/export/{task_id}/files`
- **描述**: 清理任务相关的导出文件，释放存储空间
- **请求方法**: DELETE
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **查询参数**:
  - `formats` (string, optional): 指定要删除的格式，多个格式用逗号分隔，如 "pdf,docx"
  - `older_than` (string, optional): 删除指定时间之前的文件，格式：ISO 8601
- **成功响应** (200 OK):
```json
{
  "task_id": 123,
  "deleted_files": [
    {
      "filename": "contract_review_123_20231201_110500.pdf",
      "format": "pdf",
      "size": "2.5MB",
      "created_at": "2023-12-01T11:05:00Z"
    },
    {
      "filename": "contract_review_123_20231201_110500.docx",
      "format": "docx",
      "size": "1.8MB",
      "created_at": "2023-12-01T11:05:00Z"
    }
  ],
  "total_deleted": 2,
  "space_freed": "4.3MB"
}
```
- **错误响应**:
  - **404 Not Found**: 没有找到可删除的文件
  ```json
  {
    "error": true,
    "message": "没有找到可删除的文件",
    "status_code": 404
  }
  ```

### 6. 获取报告状态
- **接口**: `GET /api/v1/export/{task_id}/status`
- **描述**: 获取报告生成状态和文件信息
- **请求方法**: GET
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **成功响应** (200 OK):
```json
{
  "task_id": 123,
  "generation_status": "completed",
  "last_generated": "2023-12-01T11:05:00Z",
  "available_files": [
    {
      "format": "pdf",
      "filename": "contract_review_123_20231201_110500.pdf",
      "size": "2.5MB",
      "created_at": "2023-12-01T11:05:00Z",
      "download_url": "/api/v1/export/123?format=pdf",
      "expires_at": "2023-12-08T11:05:00Z"
    },
    {
      "format": "docx",
      "filename": "contract_review_123_20231201_110500.docx",
      "size": "1.8MB",
      "created_at": "2023-12-01T11:05:00Z",
      "download_url": "/api/v1/export/123?format=docx",
      "expires_at": "2023-12-08T11:05:00Z"
    }
  ],
  "total_files": 2,
   "total_size": "4.3MB"
 }
 ```

### 7. 批量导出报告
- **接口**: `POST /api/v1/export/batch`
- **描述**: 批量导出多个任务的报告
- **请求方法**: POST
- **请求体**:
```json
{
  "task_ids": [123, 124, 125],
  "format": "pdf",
  "archive_format": "zip",
  "include_summary": true,
  "custom_filename": "contract_reports_batch_20231201"
}
```
- **成功响应** (202 Accepted):
```json
{
  "batch_id": "batch_20231201_110500",
  "status": "processing",
  "total_tasks": 3,
  "estimated_completion": "2023-12-01T11:15:00Z",
  "download_url": "/api/v1/export/batch/batch_20231201_110500/download",
  "status_url": "/api/v1/export/batch/batch_20231201_110500/status"
}
```

### 8. 获取批量导出状态
- **接口**: `GET /api/v1/export/batch/{batch_id}/status`
- **描述**: 获取批量导出任务的状态
- **请求方法**: GET
- **路径参数**:
  - `batch_id` (string, required): 批量任务ID
- **成功响应** (200 OK):
```json
{
  "batch_id": "batch_20231201_110500",
  "status": "completed",
  "progress": 100,
  "total_tasks": 3,
  "completed_tasks": 3,
  "failed_tasks": 0,
  "created_at": "2023-12-01T11:05:00Z",
  "completed_at": "2023-12-01T11:12:00Z",
  "download_ready": true,
  "archive_size": "8.5MB",
  "expires_at": "2023-12-08T11:12:00Z",
  "task_details": [
    {
      "task_id": 123,
      "status": "completed",
      "filename": "contract_review_123.pdf",
      "size": "2.5MB"
    },
    {
      "task_id": 124,
      "status": "completed",
      "filename": "contract_review_124.pdf",
      "size": "3.2MB"
    },
    {
      "task_id": 125,
      "status": "completed",
      "filename": "contract_review_125.pdf",
      "size": "2.8MB"
    }
  ]
}
```

### 9. 下载批量导出文件
- **接口**: `GET /api/v1/export/batch/{batch_id}/download`
- **描述**: 下载批量导出的压缩文件
- **请求方法**: GET
- **路径参数**:
  - `batch_id` (string, required): 批量任务ID
- **成功响应** (200 OK):
  - **Content-Type**: `application/zip`
  - **Content-Disposition**: `attachment; filename="{custom_filename}.zip"`
  - **响应体**: ZIP压缩文件流

### 10. 报告模板管理
- **接口**: `GET /api/v1/export/templates`
- **描述**: 获取可用的报告模板列表
- **请求方法**: GET
- **成功响应** (200 OK):
```json
{
  "templates": [
    {
      "id": "standard_v2",
      "name": "标准报告模板 v2.1",
      "description": "包含完整风险分析和法规引用的标准模板",
      "version": "2.1.0",
      "supported_formats": ["pdf", "docx", "txt"],
      "features": [
        "风险等级可视化",
        "法规条文引用",
        "修改建议",
        "执行摘要"
      ],
      "is_default": true,
      "created_at": "2023-11-01T00:00:00Z",
      "updated_at": "2023-11-15T00:00:00Z"
    },
    {
      "id": "executive_summary",
      "name": "高管摘要模板",
      "description": "简化版报告，重点突出关键风险和建议",
      "version": "1.0.0",
      "supported_formats": ["pdf", "docx"],
      "features": [
        "关键风险概览",
        "执行建议",
        "风险矩阵图"
      ],
      "is_default": false,
      "created_at": "2023-10-01T00:00:00Z",
      "updated_at": "2023-10-01T00:00:00Z"
    }
  ],
  "total_templates": 2,
  "default_template": "standard_v2"
}
```

### 11. 使用指定模板生成报告
- **接口**: `POST /api/v1/export/{task_id}/generate-with-template`
- **描述**: 使用指定模板生成报告
- **请求方法**: POST
- **路径参数**:
  - `task_id` (integer, required): 任务ID
- **请求体**:
```json
{
  "template_id": "executive_summary",
  "format": "pdf",
  "custom_options": {
    "include_charts": true,
    "risk_threshold": "medium",
    "language": "zh-CN",
    "branding": {
      "company_logo": "base64_encoded_logo",
      "company_name": "示例公司",
      "report_title": "合同风险评估报告"
    }
  }
}
```
- **成功响应** (200 OK):
```json
{
  "task_id": 123,
  "template_id": "executive_summary",
  "generation_id": "gen_123_exec_20231201_110500",
  "status": "generating",
  "estimated_completion": "2023-12-01T11:08:00Z",
  "download_url": "/api/v1/export/123?format=pdf&generation_id=gen_123_exec_20231201_110500"
}
```

## 报告导出错误码说明

| 错误码 | HTTP状态码 | 描述 | 解决方案 |
|--------|------------|------|----------|
| EXPORT_001 | 404 | 任务不存在 | 检查任务ID是否正确 |
| EXPORT_002 | 422 | 任务状态不允许导出 | 等待任务完成后再导出 |
| EXPORT_003 | 400 | 不支持的导出格式 | 使用支持的格式：pdf、docx、txt |
| EXPORT_004 | 409 | 报告正在生成中 | 等待当前生成完成或取消后重试 |
| EXPORT_005 | 500 | 报告生成失败 | 检查服务状态，联系技术支持 |
| EXPORT_006 | 413 | 报告文件过大 | 尝试使用txt格式或联系管理员 |
| EXPORT_007 | 404 | 批量任务不存在 | 检查批量任务ID是否正确 |
| EXPORT_008 | 410 | 文件已过期 | 重新生成报告文件 |

## 报告导出最佳实践

### 1. 格式选择建议
- **PDF**: 适合正式文档、打印、归档
- **DOCX**: 适合需要编辑、批注的场景
- **TXT**: 适合程序处理、快速预览

### 2. 性能优化
- 大批量导出建议使用批量接口
- 定期清理过期的导出文件
- 使用预览接口检查内容后再下载

### 3. 安全考虑
- 导出文件有过期时间限制（默认7天）
- 敏感信息在文件中会被适当脱敏
- 建议下载后及时删除服务器文件

### 4. 集成示例
```javascript
// 导出报告示例
const exportReport = async (taskId, format = 'pdf') => {
  try {
    // 1. 检查报告状态
    const statusResponse = await fetch(`/api/v1/export/${taskId}/status`);
    const status = await statusResponse.json();
    
    if (status.generation_status !== 'completed') {
      // 2. 如果报告未生成，先生成报告
      await fetch(`/api/v1/export/${taskId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ formats: [format] })
      });
      
      // 3. 等待生成完成（实际应用中建议使用WebSocket监听）
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    // 4. 下载报告
    const downloadResponse = await fetch(`/api/v1/export/${taskId}?format=${format}`);
    const blob = await downloadResponse.blob();
    
    // 5. 触发下载
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `contract_review_${taskId}.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
    
  } catch (error) {
    console.error('导出失败:', error);
  }
};
```

## WebSocket 实时通信

### 1. 审查进度推送
- **接口**: `WebSocket /ws/review/{task_id}`
- **描述**: 实时推送审查进度
- **路径参数**:
  - `task_id`: 任务ID
- **支持的客户端消息类型**:
  - `ping`: 心跳包
  - `heartbeat`: 心跳包（另一种格式）
  - `get_status` / `status_request`: 请求当前任务状态

**消息格式**:

**连接确认**:
```json
{
  "type": "connection",
  "message": "已连接到任务 123 的进度推送",
  "task_id": 123
}
```

**进度更新**:
```json
{
  "type": "progress",
  "task_id": 123,
  "stage": "analyzing_risks",
  "progress": 60,
  "message": "正在分析风险条款..."
}
```

**状态查询响应**:
```json
{
  "type": "status",
  "task_id": 123,
  "status": "IN_PROGRESS",
  "contract_type": "销售合同",
  "role": "buyer",
  "created_at": "2023-12-01T10:00:00",
  "updated_at": "2023-12-01T10:30:00"
}
```

**心跳包**:
```json
// 客户端发送 (方式1)
{"type": "ping", "timestamp": "1703123456789"}
// 服务端响应
{"type": "pong", "timestamp": "1703123456789"}

// 客户端发送 (方式2)
{"type": "heartbeat", "timestamp": "1703123456789"}
// 服务端响应
{"type": "heartbeat_ack", "timestamp": "1703123456789"}
```

**错误响应**:
```json
{
  "type": "error",
  "message": "错误描述",
  "supported_types": ["ping", "heartbeat", "get_status", "status_request"]
}
```

### 2. 健康检查WebSocket
- **接口**: `WebSocket /ws/health`
- **描述**: WebSocket服务健康检查
- **连接响应**:
```json
{
  "type": "health",
  "status": "healthy",
  "message": "WebSocket服务正常运行"
}
```
- **心跳响应**:
```json
{
  "type": "pong",
  "timestamp": "客户端时间戳",
  "server_time": "服务器时间戳"
}
```

### 3. 测试WebSocket
- **接口**: `WebSocket /ws/test/{client_id}`
- **描述**: 用于测试的WebSocket连接
- **路径参数**:
  - `client_id`: 客户端ID
- **欢迎消息**:
```json
{
  "type": "welcome",
  "client_id": "test_client_1",
  "message": "欢迎客户端 test_client_1"
}
```
- **回显消息**:
```json
{
  "type": "echo",
  "client_id": "test_client_1",
  "original_message": "客户端发送的消息",
  "timestamp": "1703123456789"
}
```

## 错误响应格式

所有API错误都遵循统一格式：
```json
{
  "error": true,
  "message": "错误描述",
  "status_code": 400
}
```

## 任务状态说明

- `PENDING`: 待处理（文件已上传，等待角色确认）
- `READY`: 就绪（角色已确认，可以开始审查）
- `IN_PROGRESS`: 审查中
- `COMPLETED`: 已完成
- `FAILED`: 失败

## 使用流程

1. **上传文件**: `POST /api/v1/upload`
2. **获取角色建议**: `POST /api/v1/draft_roles`
3. **确认角色**: `POST /api/v1/confirm_roles` 或 `POST /api/v1/manual_party_names`
4. **开始审查**: `POST /api/v1/review`
5. **监听进度**: `WebSocket /ws/review/{task_id}`
6. **获取结果**: `GET /api/v1/review/{task_id}`
7. **导出报告**: `GET /api/v1/export/{task_id}`

### 角色确认流程说明

- **自动识别场景**: 使用 `POST /api/v1/confirm_roles`，基于系统自动提取的实体进行角色确认
- **手动输入场景**: 使用 `POST /api/v1/manual_party_names`，当自动实体识别失败或不准确时手动设置主体名称

## 前端集成建议

### 1. 文件上传组件
```javascript
// 示例：文件上传
const uploadFile = async (file, contractType) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('contract_type', contractType);
  
  const response = await fetch('/api/v1/upload', {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

### 2. WebSocket连接管理
```javascript
// 示例：WebSocket连接
const connectToReview = (taskId) => {
  const ws = new WebSocket(`ws://localhost:8000/ws/review/${taskId}`);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
      case 'progress':
        updateProgress(data.progress, data.message);
        break;
      case 'status':
        updateStatus(data.status);
        break;
    }
  };
  
  // 心跳包
  setInterval(() => {
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: Date.now().toString()
    }));
  }, 30000);
};
```

### 3. 错误处理
```javascript
// 示例：统一错误处理
const handleApiError = (response) => {
  if (!response.ok) {
    return response.json().then(error => {
      throw new Error(error.message || '请求失败');
    });
  }
  return response.json();
};
```

## 注意事项

1. **文件大小限制**: 上传文件不能超过50MB
2. **WebSocket心跳**: 建议每30秒发送一次心跳包保持连接
3. **错误处理**: 所有接口都可能返回错误，需要统一处理
4. **状态轮询**: 如果不使用WebSocket，可以定期调用状态查询接口
5. **文件清理**: 导出的文件会占用服务器空间，建议定期清理

---

**文档版本**: v1.1.0  
**最后更新**: 2024-12-19  
**更新内容**: 
- 新增实体识别模块说明
- 更新角色确认接口参数
- 完善文件上传功能描述
- 更新角色识别响应格式
**联系方式**: 开发团队