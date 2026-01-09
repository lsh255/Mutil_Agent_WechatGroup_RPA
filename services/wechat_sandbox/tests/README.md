# 测试文档

## 测试概览

本项目包含完整的测试套件，覆盖Redis队列管理、生产者服务、API接口和集成测试。

## 测试类型

### 1. 单元测试
测试单个组件的功能：
- `test_queue_manager.py` - Redis队列管理器测试
- `test_producer_service.py` - 生产者服务测试（监控器、检测器、分类器）

### 2. API测试
测试FastAPI接口：
- `test_api_server.py` - API端点测试
- 测试所有REST API的请求和响应

### 3. 集成测试
测试完整的服务流程：
- `test_integration.py` - 端到端工作流测试
- Docker服务测试
- 多实例测试
- 性能测试

## 运行测试

### 本地运行

#### 安装测试依赖
```bash
cd services/wechat_sandbox
pip install -r requirements.txt
```

#### 运行所有测试
```bash
python run_tests.py all
```

#### 运行特定类型测试
```bash
# 单元测试
python run_tests.py unit

# API测试
python run_tests.py api

# 集成测试
python run_tests.py integration

# Docker测试
python run_tests.py docker
```

#### 直接使用pytest
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_queue_manager.py -v

# 运行特定测试类
pytest tests/test_producer_service.py::TestMonitor -v

# 运行特定测试函数
pytest tests/test_queue_manager.py::TestQueueManager::test_connection -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

### Docker中运行

#### 单实例测试
```bash
cd services/wechat_sandbox
docker-compose up -d

# 等待服务启动
sleep 10

# 运行测试
docker-compose exec producer_service python run_tests.py all
```

#### 多实例测试
```bash
cd services/wechat_sandbox
docker-compose -f docker-compose.multi.yml up -d

# 等待服务启动
sleep 20

# 测试实例1
docker-compose -f docker-compose.multi.yml exec producer_service_1 python run_tests.py all

# 测试实例2
docker-compose -f docker-compose.multi.yml exec producer_service_2 python run_tests.py all

# 测试实例3
docker-compose -f docker-compose.multi.yml exec producer_service_3 python run_tests.py all
```

## 测试配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `REDIS_HOST` | localhost | Redis主机地址 |
| `REDIS_PORT` | 6379 | Redis端口 |
| `REDIS_DB` | 0 | Redis数据库编号 |
| `API_HOST` | localhost | API主机地址 |
| `API_PORT` | 8000 | API端口 |
| `VNC_HOST` | localhost | VNC主机地址 |
| `VNC_PORT` | 6080 | VNC端口 |

### pytest配置

测试配置文件：`tests/pytest.ini`

```ini
[pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short --disable-warnings
```

## 测试标记

测试使用pytest标记进行分类：

| 标记 | 说明 |
|------|------|
| `unit` | 单元测试 |
| `integration` | 集成测试 |
| `slow` | 慢速测试 |
| `docker` | Docker相关测试 |
| `api` | API相关测试 |
| `redis` | Redis相关测试 |

### 按标记运行测试
```bash
# 只运行单元测试
pytest tests/ -m unit -v

# 只运行集成测试
pytest tests/ -m integration -v

# 排除慢速测试
pytest tests/ -m "not slow" -v
```

## 测试覆盖率

生成覆盖率报告：

```bash
# 生成HTML报告
pytest tests/ --cov=. --cov-report=html

# 生成终端报告
pytest tests/ --cov=. --cov-report=term-missing

# 指定覆盖率阈值
pytest tests/ --cov=. --cov-fail-under=80
```

覆盖率报告会生成在 `htmlcov/` 目录下，使用浏览器打开 `htmlcov/index.html` 查看。

## CI/CD集成

### GitHub Actions示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        cd services/wechat_sandbox
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd services/wechat_sandbox
        python run_tests.py all
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
```

## 常见问题

### 测试失败：Redis连接失败

**问题**：测试跳过，提示"Redis连接失败"

**解决方案**：
```bash
# 启动Redis
docker-compose up -d redis

# 或使用本地Redis
redis-server
```

### 测试失败：API服务未启动

**问题**：API测试超时

**解决方案**：
```bash
# 启动生产者服务
docker-compose up -d producer_service

# 等待服务启动
sleep 10
```

### VNC测试失败

**问题**：VNC服务未启动

**解决方案**：
```bash
# 检查Docker容器状态
docker ps

# 查看容器日志
docker logs wechat_producer_service

# 重启容器
docker-compose restart producer_service
```

## 测试最佳实践

1. **隔离性**：每个测试应该独立运行，不依赖其他测试
2. **清理**：使用fixture清理测试数据
3. **Mock**：使用Mock模拟外部依赖（文件系统、网络等）
4. **异步**：使用pytest-asyncio处理异步测试
5. **覆盖率**：保持测试覆盖率在80%以上

## 添加新测试

### 创建测试文件

```bash
cd tests
touch test_new_feature.py
```

### 编写测试

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """新功能测试类"""
    
    @pytest.fixture
    def setup_data(self):
        """测试数据fixture"""
        return {"key": "value"}
    
    def test_new_functionality(self, setup_data):
        """测试新功能"""
        assert setup_data["key"] == "value"
```

### 运行新测试

```bash
pytest tests/test_new_feature.py -v
```

## 测试报告

测试报告包括：

1. **单元测试报告**：组件级别的功能测试
2. **API测试报告**：接口级别的测试
3. **集成测试报告**：端到端工作流测试
4. **覆盖率报告**：代码覆盖率统计
5. **性能测试报告**：响应时间和并发测试

## 维护建议

1. 定期运行测试套件
2. 保持测试更新，与新功能同步
3. 修复失败的测试
4. 优化慢速测试
5. 提高代码覆盖率

## 联系支持

如有测试相关问题，请参考：
- [pytest官方文档](https://docs.pytest.org/)
- 项目README.md
- QUICKSTART.md
