# 测试文档

本目录包含了 ContractShield AI Backend 项目的完整测试套件。

## 测试结构

```
tests/
├── __init__.py                 # 测试包初始化
├── conftest.py                 # Pytest 配置和共享 fixtures
├── pytest.ini                 # Pytest 配置文件
├── run_tests.py               # 测试运行脚本
├── README.md                  # 测试文档（本文件）
├── test_api.py                # API 单元测试
├── test_api_endpoints.py      # API 端点集成测试
├── test_services.py           # 服务层单元测试
├── test_websocket.py          # WebSocket 测试
├── test_implementation.py     # 实现功能测试
├── simple_api_test.py         # 简化的 API 测试
├── simple_websocket_test.py   # 简化的 WebSocket 测试
├── create_test_pdf.py         # 测试数据生成脚本
└── websocket_test.html        # WebSocket 前端测试页面
```

## 测试分类

### 按测试类型分类

- **单元测试** (`@pytest.mark.unit`): 测试单个函数或类的功能
- **集成测试** (`@pytest.mark.integration`): 测试多个组件之间的交互
- **API测试** (`@pytest.mark.api`): 测试 REST API 端点
- **WebSocket测试** (`@pytest.mark.websocket`): 测试 WebSocket 连接和消息
- **数据库测试** (`@pytest.mark.database`): 测试数据库操作
- **慢速测试** (`@pytest.mark.slow`): 执行时间较长的测试
- **外部服务测试** (`@pytest.mark.external`): 测试外部服务集成
- **模拟测试** (`@pytest.mark.mock`): 使用模拟对象的测试

### 按功能模块分类

1. **文件服务测试** (`test_services.py`)
   - 文件保存和读取
   - 文本提取
   - OCR 处理
   - 文件格式验证

2. **AI服务测试** (`test_services.py`)
   - 嵌入向量生成
   - 相似度搜索
   - 草稿角色生成
   - OpenAI API 集成

3. **审查服务测试** (`test_services.py`)
   - 合同审查流程
   - 风险识别
   - 角色确认
   - 审查状态管理

4. **导出服务测试** (`test_services.py`)
   - 报告生成
   - PDF 导出
   - 数据格式化

5. **API端点测试** (`test_api.py`, `test_api_endpoints.py`)
   - 文件上传
   - 合同审查
   - 报告导出
   - 错误处理
   - 认证和授权

6. **WebSocket测试** (`test_websocket.py`)
   - 连接管理
   - 消息传递
   - 进度更新
   - 错误处理

## 快速开始

### 环境准备

1. 安装测试依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
export TEST_DATABASE_URL="sqlite:///test.db"
export OPENAI_API_KEY="your-test-api-key"
```

### 运行测试

#### 使用测试脚本（推荐）

```bash
# 运行所有测试
python tests/run_tests.py all

# 运行单元测试
python tests/run_tests.py unit

# 运行集成测试
python tests/run_tests.py integration

# 运行 API 测试
python tests/run_tests.py api

# 运行 WebSocket 测试
python tests/run_tests.py websocket

# 运行特定测试文件
python tests/run_tests.py --file tests/test_services.py

# 生成覆盖率报告
python tests/run_tests.py coverage

# 并行运行测试
python tests/run_tests.py parallel

# 代码质量检查
python tests/run_tests.py lint
```

#### 直接使用 Pytest

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定标记的测试
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m "not slow" -v

# 运行特定文件
pytest tests/test_services.py -v

# 运行特定测试函数
pytest tests/test_services.py::TestFileService::test_save_file -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# 并行运行测试
pytest tests/ -n auto

# 只运行失败的测试
pytest --lf
```

## 测试配置

### Pytest 配置 (`pytest.ini`)

- 测试发现规则
- 输出格式设置
- 覆盖率配置
- 测试标记定义
- 警告过滤

### 共享 Fixtures (`conftest.py`)

- **数据库相关**:
  - `db_session`: 测试数据库会话
  - `test_db`: 测试数据库引擎

- **客户端相关**:
  - `client`: FastAPI 测试客户端
  - `async_client`: 异步测试客户端

- **服务实例**:
  - `file_service`: 文件服务实例
  - `ai_service`: AI 服务实例
  - `review_service`: 审查服务实例
  - `export_service`: 导出服务实例

- **测试数据**:
  - `sample_user`: 示例用户
  - `sample_file`: 示例文件
  - `sample_task`: 示例任务
  - `sample_upload_file`: 示例上传文件

- **模拟对象**:
  - `mock_openai_api`: 模拟 OpenAI API
  - `mock_file_operations`: 模拟文件操作

## 测试最佳实践

### 1. 测试命名

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试函数以 `test_` 开头
- 使用描述性的名称，说明测试的功能

### 2. 测试结构

```python
def test_function_name():
    # Arrange: 准备测试数据
    input_data = "test input"
    expected_result = "expected output"
    
    # Act: 执行被测试的功能
    actual_result = function_under_test(input_data)
    
    # Assert: 验证结果
    assert actual_result == expected_result
```

### 3. 使用模拟对象

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    with patch('app.services.external_service') as mock_service:
        mock_service.return_value = "mocked result"
        
        result = function_that_uses_external_service()
        
        assert result == "mocked result"
        mock_service.assert_called_once()
```

### 4. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 5. 参数化测试

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_inputs(input_value, expected):
    result = function_under_test(input_value)
    assert result == expected
```

## 持续集成

测试套件已集成到 GitHub Actions CI/CD 流水线中：

- **自动触发**: 每次 push 和 pull request
- **多环境测试**: Python 3.9+
- **覆盖率检查**: 最低 80% 覆盖率
- **代码质量**: Flake8, Black, isort 检查
- **安全扫描**: Bandit 安全检查

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 检查 `TEST_DATABASE_URL` 环境变量
   - 确保测试数据库可访问

2. **导入错误**
   - 检查 Python 路径设置
   - 确保所有依赖已安装

3. **异步测试失败**
   - 确保安装了 `pytest-asyncio`
   - 检查异步函数的 `@pytest.mark.asyncio` 装饰器

4. **模拟对象不工作**
   - 检查模拟的路径是否正确
   - 确保在正确的作用域内使用模拟

### 调试技巧

1. **使用 `-s` 参数查看打印输出**:
   ```bash
   pytest tests/test_services.py -s
   ```

2. **使用 `--pdb` 进入调试器**:
   ```bash
   pytest tests/test_services.py --pdb
   ```

3. **查看详细的失败信息**:
   ```bash
   pytest tests/test_services.py -v --tb=long
   ```

4. **只运行失败的测试**:
   ```bash
   pytest --lf -v
   ```

## 贡献指南

### 添加新测试

1. 确定测试类型和所属模块
2. 在相应的测试文件中添加测试
3. 使用适当的测试标记
4. 编写清晰的测试文档
5. 确保测试可以独立运行

### 测试覆盖率

- 新功能必须有相应的测试
- 保持整体覆盖率在 80% 以上
- 重点测试核心业务逻辑
- 包含正常和异常情况的测试

### 代码质量

- 遵循项目的代码风格
- 使用有意义的变量和函数名
- 添加必要的注释和文档
- 保持测试代码的简洁性

## 性能测试

对于性能敏感的功能，可以添加性能测试：

```python
import time
import pytest

@pytest.mark.slow
def test_performance():
    start_time = time.time()
    
    # 执行性能测试
    result = expensive_operation()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert result is not None
    assert execution_time < 5.0  # 应在5秒内完成
```

## 测试数据管理

- 使用 fixtures 创建可重用的测试数据
- 每个测试后清理数据
- 使用工厂模式创建复杂的测试对象
- 避免测试之间的数据依赖

## 总结

这个测试套件提供了全面的测试覆盖，包括单元测试、集成测试、API测试和WebSocket测试。通过合理的测试结构和配置，确保了代码质量和系统稳定性。

如有问题或建议，请查看项目文档或联系开发团队。