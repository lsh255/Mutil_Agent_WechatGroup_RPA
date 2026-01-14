# 测试文档

## 测试概览（v2.0）

本项目包含完整的测试套件，覆盖 AT-SPI 观察者、消息提取、生产者服务、API 接口和集成测试。

### v2.0 测试架构更新

- ✅ AT-SPI 模块测试：`tests/atspi/test_atspi_observer.py`
- ✅ 消息提取器测试：`tests/extractor/`（待添加）
- ✅ 生产者服务测试：`tests/test_producer_service.py`
- ✅ API 接口测试：`tests/test_api_server.py`
- ✅ 集成测试：`tests/test_integration.py`

## 测试类型

### 1. 单元测试
测试单个组件的功能：
- `tests/atspi/test_atspi_observer.py` - AT-SPI 观察者测试 ⭐ 新路径
- `tests/test_producer_service.py` - 生产者服务测试（混合生产者、消费者）
- `tests/extractor/test_message_extractor.py` - 消息提取器测试（待添加）

### 2. API测试
测试FastAPI接口：
- `tests/test_api_server.py` - API端点测试
- 测试所有REST API的请求和响应（健康检查、实例管理、SSE 流）

### 3. 集成测试
测试完整的服务流程：
- `tests/test_integration.py` - 端到端工作流测试
- Docker服务测试
- 多实例测试
- AT-SPI 环境测试

## 运行测试

### 本地运行

#### 安装测试依赖
```bash
cd services/wechat_sandbox
pip install -r requirements.txt
```

#### 运行所有测试
```bash
# 方式1：使用 pytest（推荐）
pytest tests/ -v

# 方式2：从项目根目录运行
pytest services/wechat_sandbox/tests/ -v
```

#### 运行特定测试文件
```bash
# AT-SPI 观察者测试 ⭐ 新路径
pytest tests/atspi/test_atspi_observer.py -v

# 生产者服务测试
pytest tests/test_producer_service.py -v

# API 服务器测试
pytest tests/test_api_server.py -v

# 集成测试
pytest tests/test_integration.py -v
```

#### 运行特定测试类或函数
```bash
# 运行特定测试类
pytest tests/test_producer_service.py::TestHybridProducer -v

# 运行特定测试函数
pytest tests/atspi/test_atspi_observer.py::TestATSPIObserver::test_initialization_without_atspi -v

# 只运行单元测试
pytest tests/ -m unit -v

# 只运行集成测试
pytest tests/ -m integration -v
```

#### 生成覆盖率报告
```bash
# 生成 HTML 报告
pytest tests/ --cov=services.wechat_sandbox --cov-report=html

# 生成终端报告
pytest tests/ --cov=services.wechat_sandbox --cov-report=term-missing

# 指定覆盖率阈值
pytest tests/ --cov=services.wechat_sandbox --cov-fail-under=70
```

### Docker中运行

#### 测试环境（推荐）
```bash
cd services/wechat_sandbox

# 启动测试环境（含 AT-SPI 支持）
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 等待服务启动
sleep 10

# 运行测试
docker exec -it wechat_sandbox_test bash
pytest tests/ -v
```

#### 生产环境测试
```bash
cd services/wechat_sandbox

# 单实例部署
docker-compose -f docker/compose/docker-compose.yml up -d

# 运行测试
docker exec -it wechat_producer_service pytest tests/ -v
```

#### 多实例测试
```bash
cd services/wechat_sandbox
docker-compose -f docker/compose/docker-compose.multi.yml up -d

# 等待服务启动
sleep 20

# 测试实例1
docker exec -it wechat_producer_service_1 pytest tests/ -v

# 测试实例2
docker exec -it wechat_producer_service_2 pytest tests/ -v

# 测试实例3
docker exec -it wechat_producer_service_3 pytest tests/ -v
```

## 测试配置（v2.0）

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

测试配置文件：`tests/conftest.py` 和项目根目录 `pytest.ini`

```ini
[pytest]
testpaths = services/wechat_sandbox/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    atspi: AT-SPI related tests
```

## 测试标记（v2.0）

测试使用 pytest 标记进行分类：

| 标记 | 说明 | 示例 |
|------|------|------|
| `unit` | 单元测试 | AT-SPI 观察者初始化测试 |
| `integration` | 集成测试 | 完整工作流测试 |
| `slow` | 慢速测试 | Docker 容器测试 |
| `atspi` | AT-SPI 相关测试 | AT-SPI 环境测试 |
| `api` | API 相关测试 | FastAPI 接口测试 |
| `redis` | Redis 相关测试 | Redis Stream 队列测试 |

### 按标记运行测试
```bash
# 只运行单元测试
pytest tests/ -m unit -v

# 只运行集成测试
pytest tests/ -m integration -v

# 只运行 AT-SPI 测试
pytest tests/ -m atspi -v

# 排除慢速测试
pytest tests/ -m "not slow" -v
```

## 测试覆盖率（v2.0）

生成覆盖率报告：

```bash
# 生成 HTML 报告（推荐）
pytest tests/ --cov=services.wechat_sandbox --cov-report=html

# 生成终端报告
pytest tests/ --cov=services.wechat_sandbox --cov-report=term-missing

# 指定覆盖率阈值（建议 70%）
pytest tests/ --cov=services.wechat_sandbox --cov-fail-under=70

# 生成 XML 报告（用于 CI/CD）
pytest tests/ --cov=services.wechat_sandbox --cov-report=xml
```

覆盖率报告会生成在 `htmlcov/` 目录下，使用浏览器打开 `htmlcov/index.html` 查看。

### 覆盖率目标

- **整体目标**：≥ 70%
- **核心模块**：≥ 80%（AT-SPI 观察者、消息提取器）
- **API 模块**：≥ 75%
- **工具模块**：≥ 60%

## CI/CD集成

### GitHub Actions示例（v2.0）

```yaml
name: WeChat Sandbox Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd services/wechat_sandbox
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run unit tests
      run: |
        pytest services/wechat_sandbox/tests/ -m unit -v

    - name: Run tests with coverage
      run: |
        pytest services/wechat_sandbox/tests/ --cov=services.wechat_sandbox --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
        flags: wechat-sandbox
        name: wechat-sandbox-coverage
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
# 启动测试环境
cd services/wechat_sandbox
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 等待服务启动
sleep 10

# 检查服务状态
curl http://localhost:8000/health
```

### AT-SPI 测试失败

**问题**：AT-SPI 环境未初始化

**解决方案**：
```bash
# 使用测试镜像（包含 AT-SPI 支持）
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest ../..

# 确认环境变量
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"

# 手动测试 AT-SPI
docker exec -it wechat_sandbox_test python3 -c "
from core.atspi.observer import ATSPIObserver
observer = ATSPIObserver()
print(observer.initialize())
"
```

### VNC测试失败

**问题**：VNC服务未启动

**解决方案**：
```bash
# 检查Docker容器状态
docker ps | grep wechat_sandbox

# 查看容器日志
docker logs wechat_sandbox_test

# 重启容器
docker-compose -f docker/compose/docker-compose.sandbox.test.yml restart
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
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
# 从项目根目录运行
pytest services/wechat_sandbox/tests/test_new_feature.py -v

# 或从 wechat_sandbox 目录运行
cd services/wechat_sandbox
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
- [pytest 官方文档](https://docs.pytest.org/)
- [项目 README.md](../README.md) ⭐ v2.0
- [快速开始指南](../QUICKSTART.md) ⭐ v2.0
- [文档索引](../docs/INDEX.md) ⭐ 新建
- [变更日志](../CHANGELOG_v2.0.md) ⭐ v2.0

---

**最后更新**：2025-01-14（v2.0）
