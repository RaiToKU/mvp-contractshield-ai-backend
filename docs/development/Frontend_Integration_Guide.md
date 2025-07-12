# 前端对接业务流程指南

## 概述

ContractShield AI 合同审查系统的完整业务流程，从文件上传到生成报告并通知前端的全过程。

## 🔄 完整业务流程

### 流程图
```
文件上传 → OCR解析 → 实体提取 → 角色确认 → AI分析 → 生成报告 → 通知前端
    ↓         ↓        ↓        ↓       ↓       ↓        ↓
  任务创建   文本提取   甲乙方识别  角色选择  风险分析  报告导出   WebSocket推送
```

## 📋 详细步骤说明

### 步骤1: 文件上传

**API端点**: `POST /api/v1/upload`

**请求格式**:
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('contract_type', 'purchase'); // 合同类型

fetch('/api/v1/upload', {
  method: 'POST',
  body: formData
})
```

**响应示例**:
```json
{
  "task_id": 123,
  "filename": "contract.pdf",
  "contract_type": "purchase",
  "status": "UPLOADED",
  "message": "文件上传成功"
}
```

**前端处理**:
- 获取 `task_id`，用于后续所有操作
- 立即建立WebSocket连接监听进度
- 显示上传成功状态

### 步骤2: 建立WebSocket连接

**连接端点**: `ws://localhost:8000/ws/review/{task_id}`

**连接代码**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/review/${taskId}`);

ws.onopen = () => {
  console.log('WebSocket连接已建立');
  // 请求当前任务状态
  ws.send(JSON.stringify({type: 'get_status'}));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleWebSocketMessage(data);
};
```

### 步骤3: 获取角色候选

**API端点**: `GET /api/v1/review/{task_id}/draft-roles`

**请求示例**:
```javascript
fetch(`/api/v1/review/${taskId}/draft-roles`)
  .then(response => response.json())
  .then(data => {
    // 显示角色选择界面
    showRoleSelection(data.candidates);
  });
```

**响应示例**:
```json
{
  "task_id": 123,
  "contract_type": "purchase",
  "candidates": [
    {
      "role": "buyer",
      "label": "采购方",
      "description": "合同中的采购方，负责购买商品或服务",
      "entities": ["ABC公司", "XYZ集团"]
    },
    {
      "role": "seller",
      "label": "供应方",
      "description": "合同中的供应方，负责提供商品或服务",
      "entities": ["供应商A", "服务商B"]
    }
  ],
  "entities_extracted_at": "2024-01-01T10:00:00"
}
```

**前端处理**:
- 展示角色选择界面
- 显示每个角色对应的实体候选
- 允许用户选择角色和对应的主体名称

### 步骤4: 确认角色信息

**API端点**: `POST /api/v1/review/{task_id}/confirm-roles`

**请求示例**:
```javascript
fetch(`/api/v1/review/${taskId}/confirm-roles`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    role: 'buyer',
    party_names: ['ABC公司'],
    selected_entity_index: 0
  })
})
```

**响应示例**:
```json
{
  "status": "READY",
  "role": "buyer",
  "party_names": ["ABC公司"],
  "auto_selected": false,
  "message": "角色确认成功"
}
```

**前端处理**:
- 显示角色确认成功
- 准备启动AI分析
- 更新UI状态为"准备分析"

### 步骤5: 启动AI分析

**API端点**: `POST /api/v1/review/{task_id}/start`

**请求示例**:
```javascript
fetch(`/api/v1/review/${taskId}/start`, {
  method: 'POST'
})
```

**响应示例**:
```json
{
  "message": "审查已开始",
  "task_id": 123,
  "status": "IN_PROGRESS"
}
```

**WebSocket进度推送**:
分析过程中会通过WebSocket实时推送进度：

```json
// 阶段1: OCR文本提取 (20%)
{
  "stage": "ocr",
  "progress": 20,
  "message": "正在提取文本内容"
}

// 阶段2: 段落分割 (40%)
{
  "stage": "segmentation",
  "progress": 40,
  "message": "正在分割段落"
}

// 阶段3: 向量化处理 (60%)
{
  "stage": "vectorize",
  "progress": 60,
  "message": "正在进行向量化处理"
}

// 阶段4: AI风险分析 (80%)
{
  "stage": "analysis",
  "progress": 80,
  "message": "正在进行风险分析"
}

// 阶段5: 分析完成 (100%)
{
  "stage": "complete",
  "progress": 100,
  "message": "审查完成"
}
```

**前端处理**:
- 显示进度条和当前阶段
- 更新状态文本
- 在完成时准备获取结果

### 步骤6: 获取分析结果

**API端点**: `GET /api/v1/review/{task_id}/result`

**请求示例**:
```javascript
fetch(`/api/v1/review/${taskId}/result`)
  .then(response => response.json())
  .then(data => {
    displayAnalysisResult(data);
  });
```

**响应示例**:
```json
{
  "task_id": 123,
  "status": "COMPLETED",
  "contract_type": "purchase",
  "role": "buyer",
  "risks": [
    {
      "id": 1,
      "clause_id": "第3条",
      "title": "付款条款风险",
      "risk_level": "HIGH",
      "summary": "付款期限过短，可能影响资金安排",
      "suggestion": "建议延长付款期限至30天",
      "statutes": [
        {
          "ref": "合同法第61条",
          "text": "当事人应当按照约定履行义务"
        }
      ]
    }
  ],
  "summary": {
    "total_risks": 5,
    "high_risks": 2,
    "medium_risks": 2,
    "low_risks": 1,
    "risk_distribution": {
      "HIGH": 2,
      "MEDIUM": 2,
      "LOW": 1
    }
  }
}
```

**前端处理**:
- 显示风险概览统计
- 展示详细风险列表
- 提供报告导出选项
- 显示相关法规引用

### 步骤7: 导出报告

**API端点**: `GET /api/v1/export/{task_id}?format={format}`

**支持格式**: `pdf`, `docx`, `txt`

**请求示例**:
```javascript
// 导出PDF报告
fetch(`/api/v1/export/${taskId}?format=pdf`)
  .then(response => response.blob())
  .then(blob => {
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `contract_report_${taskId}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  });
```

**预览报告**:
```javascript
// 获取报告预览
fetch(`/api/v1/export/${taskId}/preview`)
  .then(response => response.json())
  .then(data => {
    showReportPreview(data);
  });
```

## 🔧 前端实现示例

### 完整的React组件示例

```typescript
import React, { useState, useEffect } from 'react';

interface ContractAnalysisProps {
  onComplete?: (result: any) => void;
}

const ContractAnalysis: React.FC<ContractAnalysisProps> = ({ onComplete }) => {
  const [taskId, setTaskId] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('upload');
  const [progress, setProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [roleCandidates, setRoleCandidates] = useState<any[]>([]);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // 文件上传
  const handleFileUpload = async (file: File, contractType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('contract_type', contractType);

    try {
      const response = await fetch('/api/v1/upload', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      
      setTaskId(data.task_id);
      setCurrentStep('connecting');
      
      // 建立WebSocket连接
      connectWebSocket(data.task_id);
      
      // 获取角色候选
      await fetchRoleCandidates(data.task_id);
      
    } catch (error) {
      console.error('文件上传失败:', error);
    }
  };

  // 建立WebSocket连接
  const connectWebSocket = (taskId: number) => {
    const websocket = new WebSocket(`ws://localhost:8000/ws/review/${taskId}`);
    
    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
      websocket.send(JSON.stringify({type: 'get_status'}));
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
    };
    
    setWs(websocket);
  };

  // 处理WebSocket消息
  const handleWebSocketMessage = (data: any) => {
    if (data.stage) {
      setProgress(data.progress);
      setStatusMessage(data.message);
      
      if (data.stage === 'complete') {
        setCurrentStep('completed');
        fetchAnalysisResult();
      }
    }
  };

  // 获取角色候选
  const fetchRoleCandidates = async (taskId: number) => {
    try {
      const response = await fetch(`/api/v1/review/${taskId}/draft-roles`);
      const data = await response.json();
      setRoleCandidates(data.candidates);
      setCurrentStep('role-selection');
    } catch (error) {
      console.error('获取角色候选失败:', error);
    }
  };

  // 确认角色
  const confirmRole = async (role: string, partyNames: string[]) => {
    if (!taskId) return;
    
    try {
      const response = await fetch(`/api/v1/review/${taskId}/confirm-roles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          role,
          party_names: partyNames
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'READY') {
        setCurrentStep('ready-to-analyze');
        // 自动启动分析
        startAnalysis();
      }
    } catch (error) {
      console.error('角色确认失败:', error);
    }
  };

  // 启动分析
  const startAnalysis = async () => {
    if (!taskId) return;
    
    try {
      await fetch(`/api/v1/review/${taskId}/start`, {
        method: 'POST'
      });
      
      setCurrentStep('analyzing');
      setProgress(0);
      setStatusMessage('开始分析...');
    } catch (error) {
      console.error('启动分析失败:', error);
    }
  };

  // 获取分析结果
  const fetchAnalysisResult = async () => {
    if (!taskId) return;
    
    try {
      const response = await fetch(`/api/v1/review/${taskId}/result`);
      const data = await response.json();
      setAnalysisResult(data);
      onComplete?.(data);
    } catch (error) {
      console.error('获取分析结果失败:', error);
    }
  };

  // 导出报告
  const exportReport = async (format: string) => {
    if (!taskId) return;
    
    try {
      const response = await fetch(`/api/v1/export/${taskId}?format=${format}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contract_report_${taskId}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出报告失败:', error);
    }
  };

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  // 渲染不同步骤的UI
  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'upload':
        return <FileUploadComponent onUpload={handleFileUpload} />;
      
      case 'role-selection':
        return (
          <RoleSelectionComponent 
            candidates={roleCandidates}
            onConfirm={confirmRole}
          />
        );
      
      case 'analyzing':
        return (
          <ProgressComponent 
            progress={progress}
            message={statusMessage}
          />
        );
      
      case 'completed':
        return (
          <ResultComponent 
            result={analysisResult}
            onExport={exportReport}
          />
        );
      
      default:
        return <div>加载中...</div>;
    }
  };

  return (
    <div className="contract-analysis">
      <h2>合同风险分析</h2>
      {renderCurrentStep()}
    </div>
  );
};

export default ContractAnalysis;
```

## 🚨 错误处理

### 常见错误及处理方式

1. **文件上传失败**
   - 检查文件格式和大小
   - 显示具体错误信息
   - 提供重新上传选项

2. **WebSocket连接失败**
   - 实现自动重连机制
   - 显示连接状态
   - 提供手动重连按钮

3. **分析超时**
   - 设置合理的超时时间
   - 显示超时提示
   - 提供重新分析选项

4. **API请求失败**
   - 统一错误处理
   - 显示用户友好的错误信息
   - 记录详细错误日志

## 📝 前端对接清单

- [ ] 实现文件上传功能
- [ ] 建立WebSocket连接监听进度
- [ ] 实现角色选择界面
- [ ] 显示分析进度和状态
- [ ] 展示分析结果
- [ ] 提供报告导出功能
- [ ] 实现错误处理和重试机制
- [ ] 添加用户体验优化（加载动画、状态提示等）

## 🔗 相关文档

- [API文档](./API_Documentation.md)
- [WebSocket指南](./WebSocket_Guide.md)
- [项目结构说明](./PROJECT_STRUCTURE.md)

按照此指南实现前端对接，可以确保与后端的完整业务流程对接。