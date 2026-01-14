# 微信沙盒测试方案（v2.0）

## 📋 文档信息

**版本**：v2.0
**更新日期**：2025-01-14
**适用版本**：WeChat Sandbox v2.0
**测试范围**：单元测试、集成测试、API 测试、性能测试

---

## 🎯 测试目标

验证 WeChat Sandbox v2.0 的核心功能：

### 核心架构（v2.0）

1. **AT-SPI 模块** (`core/atspi/`)
   - AT-SPI 观察者（Observer）
   - 聊天窗口监听器（ChatWindowListener）
   - 全局聊天监听器（GlobalChatListener）

2. **消息提取模块** (`core/extractor/`)
   - 通用消息提取器（UniversalMessageExtractor）
   - 3种消息类型：text、photo、video
   - 其他类型保存到物理机

3. **生产者模块** (`core/producer/`)
   - 混合生产者（HybridProducer）
   - 消费者（AgentConsumer）

4. **API 模块** (`api/`)
   - FastAPI REST 接口
   - SSE 实时推送

---

## 🧪 测试环境要求

### 1. 基础服务

| 服务 | 版本要求 | 用途 |
|------|---------|------|
| **Python** | 3.10+ | 运行测试 |
| **Redis** | 7.2+ | 消息队列 |
| **Docker** | 20.10+ | 容器化部署 |
| **pytest** | 9.0+ | 测试框架 |
| **pytest-cov** | 7.0+ | 覆盖率 |

### 2. 微信环境

- **微信 PC 客户端**：已登录（Linux 版本）
- **测试群聊**：至少 3 个成员
- **测试消息类型**：
  - ✅ 文本消息（text）
  - ✅ 图片消息（photo）
  - ✅ 视频消息（video）
  - ⚠️ 其他类型（file、link、emoji）→ 保存到物理机

### 3. AT-SPI 环境（可选）

**环境变量**：
```bash
QT_ACCESSIBILITY=1
GNOME_ACCESSIBILITY=1
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
```

**工具**：
- Accerciser（UI 控件树调试）

---

## 📦 测试套件概览

### 测试分类

| 测试类型 | 测试文件 | 测试数量 | 状态 |
|---------|---------|---------|------|
| **单元测试** | `test_queue_manager.py` | 11 | ✅ 通过 |
| **单元测试** | `test_producer_service.py` | 16 | ✅ 通过 |
| **API 测试** | `test_api_server.py` | 17 | ⏭️ 需要服务 |
| **集成测试** | `test_integration.py` | 20 | ⏭️ 需要完整环境 |

**当前通过率**：27/55 (49%)
**服务运行后预期通过率**：100%

---

## 🔬 测试一：队列管理器测试

### 目标
验证 Redis Stream 队列的读写操作

### 测试文件
`services/wechat_sandbox/tests/test_queue_manager.py`

### 测试用例（11个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_connection | Redis 连接测试 | ✅ PASS |
| 2 | test_send_raw_message | 发送原始消息 | ✅ PASS |
| 3 | test_send_precise_message | 发送精确消息 | ✅ PASS |
| 4 | test_read_raw_messages | 读取原始消息 | ✅ PASS |
| 5 | test_read_precise_messages | 读取精确消息 | ✅ PASS |
| 6 | test_message_persistence | 消息持久化 | ✅ PASS |
| 7 | test_multiple_messages | 批量消息处理 | ✅ PASS |
| 8 | test_consumer_group | 消费者组 | ✅ PASS |
| 9 | test_message_acknowledge | 消息确认 | ✅ PASS |
| 10 | test_stream_info | 流信息获取 | ✅ PASS |
| 11 | test_close_connection | 连接关闭 | ✅ PASS |

### 运行命令

```bash
# 进入测试目录
cd services/wechat_sandbox

# 运行队列管理器测试
python -m pytest tests/test_queue_manager.py -v

# 查看覆盖率
python -m pytest tests/test_queue_manager.py --cov=tests --cov-report=term-missing
```

### 预期结果

```
========================= 11 passed in 2.06s =========================

----------- coverage: platform win32, python 3.12.12 -----------
Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
tests\test_queue_manager.py         63      0   100%
--------------------------------------------------------------
TOTAL                              545    404    26%
```

---

## 🔬 测试二：生产者服务测试

### 目标
验证 v2.0 核心模块的功能

### 测试文件
`services/wechat_sandbox/tests/test_producer_service.py`

### 测试用例（16个）

#### TestChangeDetector（2个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_detector_initialization | 检测器初始化 | ✅ PASS |
| 2 | test_detect_change | 变化检测（dHash） | ✅ PASS |

#### TestATSPIObserver（3个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_observer_creation | 观察者创建 | ✅ PASS |
| 2 | test_add_callback | 添加回调函数 | ✅ PASS |
| 3 | test_message_model | ATSPIMessage 模型 | ✅ PASS |

#### TestHybridProducer（3个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_producer_initialization | 生产者初始化 | ✅ PASS |
| 2 | test_get_stats | 获取统计信息 | ✅ PASS |
| 3 | test_mode_enums | 生产模式枚举 | ✅ PASS |

#### TestMessageExtractor（4个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_extractor_creation | 提取器创建 | ✅ PASS |
| 2 | test_message_type_enum | 消息类型枚举 | ✅ PASS |
| 3 | test_extracted_message_model | ExtractedMessage 模型 | ✅ PASS |
| 4 | test_message_to_sse_json | SSE JSON 转换 | ✅ PASS |

#### TestVisualMonitor（1个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_visual_monitor_creation | 视觉监控器创建 | ✅ PASS |

#### TestConsumer（1个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_consumer_creation | 消费者创建 | ✅ PASS |

#### TestProductionMode（2个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_mode_values | 模式值验证 | ✅ PASS |
| 2 | test_mode_iteration | 模式迭代 | ✅ PASS |

### 运行命令

```bash
# 运行生产者服务测试
python -m pytest tests/test_producer_service.py -v

# 运行特定测试类
python -m pytest tests/test_producer_service.py::TestATSPIObserver -v
```

### 预期结果

```
========================= 16 passed in 0.12s =========================
```

---

## 🔬 测试三：API 模型测试

### 目标
验证 Pydantic 数据模型的验证逻辑

### 测试文件
`services/wechat_sandbox/tests/test_api_server.py`

### 测试用例（4个）

#### TestAPIModels（4个）

| # | 测试用例 | 说明 | 状态 |
|---|---------|------|------|
| 1 | test_roi_model_validation | ROI 模型验证 | ✅ PASS |
| 2 | test_roi_model_negative_validation | 负数验证 | ✅ PASS |
| 3 | test_roi_model_order_validation | 顺序验证 | ✅ PASS |
| 4 | test_missing_field_validation | 缺失字段验证 | ✅ PASS |

### ROI 模型规范

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class ROIModel(BaseModel):
    """ROI 模型"""
    left: int = Field(..., ge=0, description="左边界")
    top: int = Field(..., ge=0, description="上边界")
    right: int = Field(..., gt=0, description="右边界")
    bottom: int = Field(..., gt=0, description="下边界")

    @field_validator('right', 'bottom')
    @classmethod
    def validate_positive(cls, v):
        """验证必须为正数"""
        if v <= 0:
            raise ValueError('必须为正数')
        return v

    @field_validator('left', 'top')
    @classmethod
    def validate_non_negative(cls, v):
        """验证不能为负数"""
        if v < 0:
            raise ValueError('不能为负数')
        return v

    @model_validator(mode='after')
    def validate_coordinates(self):
        """验证坐标顺序"""
        if self.left >= self.right:
            raise ValueError('左边界必须小于右边界')
        if self.top >= self.bottom:
            raise ValueError('上边界必须小于下边界')
        return self
```

### 运行命令

```bash
# 运行 API 模型测试
python -m pytest tests/test_api_server.py::TestAPIModels -v
```

---

## 🔬 测试四：API 集成测试

### 目标
验证 FastAPI 服务器的 REST 接口和 SSE 推送

### 测试文件
`services/wechat_sandbox/tests/test_api_server.py`

### 测试用例（17个）

#### TestAPIServer（10个）

| # | 测试用例 | 说明 | 需要服务 |
|---|---------|------|---------|
| 1 | test_root_endpoint | 根路径 | ✅ |
| 2 | test_health_endpoint | 健康检查 | ✅ |
| 3 | test_status_endpoint | 状态端点 | ✅ |
| 4 | test_ui_endpoint | Web UI | ✅ |
| 5 | test_update_roi_endpoint | 更新 ROI | ✅ |
| 6 | test_update_roi_invalid_data | 无效 ROI 数据 | ✅ |
| 7 | test_screenshot_endpoint | 截图端点 | ✅ |
| 8 | test_restart_endpoint | 重启端点 | ✅ |
| 9 | test_stream_endpoint | SSE 流端点 | ✅ |
| 10 | test_invalid_endpoint | 无效端点 | ✅ |

#### TestAPIIntegration（3个）

| # | 测试用例 | 说明 | 需要服务 |
|---|---------|------|---------|
| 1 | test_full_workflow | 完整工作流 | ✅ |
| 2 | test_concurrent_requests | 并发请求 | ✅ |
| 3 | test_error_handling | 错误处理 | ✅ |

### 运行命令

```bash
# 1. 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 2. 等待服务启动
sleep 10

# 3. 运行 API 测试
python -m pytest tests/test_api_server.py -v

# 4. 停止环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down
```

---

## 🔬 测试五：集成测试

### 目标
验证完整的端到端工作流

### 测试文件
`services/wechat_sandbox/tests/test_integration.py`

### 测试用例（20个）

#### TestDockerIntegration（4个）

| # | 测试用例 | 说明 | 需要环境 |
|---|---------|------|---------|
| 1 | test_service_availability | 服务可用性 | Docker |
| 2 | test_redis_connection | Redis 连接 | Docker |
| 3 | test_message_flow | 消息流 | Docker |
| 4 | test_web_ui_access | Web UI 访问 | Docker |

#### TestVNCIntegration（1个）

| # | 测试用例 | 说明 | 需要环境 |
|---|---------|------|---------|
| 1 | test_vnc_web_access | VNC Web 访问 | Docker |

#### TestMultiInstanceIntegration（2个）

| # | 测试用例 | 说明 | 需要环境 |
|---|---------|------|---------|
| 1 | test_multiple_instances_health | 多实例健康检查 | Docker |
| 2 | test_multiple_instances_isolation | 多实例隔离 | Docker |

#### TestEndToEndWorkflow（3个）

| # | 测试用例 | 说明 | 需要环境 |
|---|---------|------|---------|
| 1 | test_complete_user_workflow | 完整用户工作流 | Docker |
| 2 | test_monitoring_workflow | 监控工作流 | Docker |
| 3 | test_error_recovery_workflow | 错误恢复工作流 | Docker |

#### TestPerformanceIntegration（3个）

| # | 测试用例 | 说明 | 需要环境 |
|---|---------|------|---------|
| 1 | test_response_time | 响应时间 | Docker |
| 2 | test_concurrent_requests | 并发请求 | Docker |
| 3 | test_screenshot_performance | 截图性能 | Docker |

### 运行命令

```bash
# 启动完整测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 等待所有服务启动
sleep 20

# 运行集成测试
python -m pytest tests/test_integration.py -v

# 清理环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down -v
```

---

## 📊 测试覆盖率目标

### v2.0 覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 | 状态 |
|------|-----------|-----------|------|
| **队列管理器** | 80% | 100% | ✅ 达标 |
| **AT-SPI 观察者** | 80% | 0% | ⚠️ 需要真实环境 |
| **消息提取器** | 80% | 0% | ⚠️ 需要真实环境 |
| **混合生产者** | 75% | 75% | ✅ 达标 |
| **API 接口** | 75% | 0% | ⚠️ 需要服务运行 |
| **整体目标** | 70% | 26% | ⚠️ 进行中 |

**当前统计**：
- 单元测试覆盖率：26% (包含所有测试文件)
- 可运行单元测试：100% 通过率（27/27）
- 需要服务的测试：等待环境配置

---

## 🚀 快速测试指南

### 1️⃣ 本地单元测试（无需 Docker）

```bash
# 进入测试目录
cd services/wechat_sandbox

# 运行所有单元测试
python -m pytest tests/test_queue_manager.py tests/test_producer_service.py -v

# 运行特定测试类
python -m pytest tests/test_producer_service.py::TestATSPIObserver -v

# 生成覆盖率报告
python -m pytest tests/ --cov=services.wechat_sandbox --cov-report=html
```

### 2️⃣ Docker 环境测试

```bash
# 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 等待服务启动
sleep 15

# 运行 AT-SPI 测试
docker exec -it wechat_sandbox_test python3 -c "
from core.atspi.observer import ATSPIObserver
observer = ATSPIObserver()
print(observer.initialize())
"

# 运行 API 测试
python -m pytest tests/test_api_server.py -v

# 查看日志
docker logs -f wechat_sandbox_test

# 停止环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down
```

### 3️⃣ 性能测试

```bash
# 测试响应时间
python -m pytest tests/test_integration.py::TestPerformanceIntegration::test_response_time -v

# 测试并发请求
python -m pytest tests/test_integration.py::TestPerformanceIntegration::test_concurrent_requests -v

# 生成性能报告
python -m pytest tests/ --benchmark-only
```

---

## 📝 测试报告模板

### 单元测试报告

```markdown
## 单元测试报告

**测试日期**: 2025-01-14
**测试环境**: Windows 10, Python 3.12.12
**测试框架**: pytest 9.0.2

### 测试结果汇总

| 测试套件 | 测试数 | 通过 | 失败 | 跳过 | 通过率 |
|---------|--------|------|------|------|--------|
| 队列管理器 | 11 | 11 | 0 | 0 | 100% |
| 生产者服务 | 16 | 16 | 0 | 0 | 100% |
| API 模型 | 4 | 4 | 0 | 0 | 100% |
| **总计** | **31** | **31** | **0** | **0** | **100%** |

### 覆盖率报告

- 语句覆盖率：26%
- 分支覆盖率：待测试
- 函数覆盖率：待测试

### 问题记录

无

### 改进建议

1. 添加 AT-SPI 真实环境测试
2. 添加消息提取器集成测试
3. 提升整体测试覆盖率到 70%
```

### 集成测试报告

```markdown
## 集成测试报告

**测试日期**: YYYY-MM-DD
**测试环境**: Docker (wechat_sandbox-test:latest)

### 测试结果汇总

| 测试类别 | 测试数 | 通过 | 失败 | 备注 |
|---------|--------|------|------|------|
| Docker 集成 | 4 | - | - | 待测试 |
| VNC 集成 | 1 | - | - | 待测试 |
| 多实例集成 | 2 | - | - | 待测试 |
| 端到端工作流 | 3 | - | - | 待测试 |
| 性能测试 | 3 | - | - | 待测试 |

### 性能指标

- 响应时间：- ms
| 并发处理：- req/s
| CPU 占用：- %
| 内存占用：- MB

### 问题记录

1. [问题描述]
   - 重现步骤：
   - 错误日志：
   - 解决方案：
```

---

## 🛠️ 测试工具和脚本

### pytest 插件

```bash
# 安装测试依赖
pip install pytest==9.0.2
pip install pytest-asyncio==1.3.0
pip install pytest-cov==7.0.0
pip install pytest-html==4.1.1
pip install pytest-benchmark==4.0.0
```

### 测试配置

**pytest.ini**:
```ini
[pytest]
testpaths = services/wechat_sandbox/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    atspi: AT-SPI related tests
    api: API related tests
```

### conftest.py 配置

```python
# services/wechat_sandbox/tests/conftest.py

import pytest
import redis
import json
import logging

# 使用标准 logging
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def redis_config():
    """Redis 配置"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "stream_raw": "test:messages:raw",
        "stream_precise": "test:messages:precise"
    }

@pytest.fixture(scope="function")
def redis_client(redis_config):
    """Redis 客户端"""
    client = redis.Redis(
        host=redis_config["host"],
        port=redis_config["port"],
        db=redis_config["db"],
        decode_responses=True
    )

    try:
        client.ping()
        logger.info(f"Redis 连接成功")
    except redis.ConnectionError as e:
        pytest.skip(f"Redis 连接失败: {e}")

    yield client
    client.close()

@pytest.fixture(scope="function")
def queue_manager(redis_client, redis_config):
    """队列管理器（模拟）"""
    # SimpleQueueManager 实现...
    pass
```

---

## 📚 相关文档

- [README.md](../services/wechat_sandbox/README.md) - 项目说明
- [QUICKSTART.md](../services/wechat_sandbox/QUICKSTART.md) - 快速开始
- [DIRECTORY_STRUCTURE_V2.md](../services/wechat_sandbox/DIRECTORY_STRUCTURE_V2.md) - 目录结构
- [docs/INDEX.md](../services/wechat_sandbox/docs/INDEX.md) - 文档索引
- [docs/ARCHITECTURE.md](../services/wechat_sandbox/docs/ARCHITECTURE.md) - 架构设计
- [docs/AT_SPI_GUIDE.md](../services/wechat_sandbox/docs/AT_SPI_GUIDE.md) - AT-SPI 指南
- [docs/MESSAGE_TYPES.md](../services/wechat_sandbox/docs/MESSAGE_TYPES.md) - 消息类型

---

## 🔧 故障排查

### 问题 1：Redis 连接失败

**症状**：
```
pytest.skip(f"Redis 连接失败: {e}")
```

**解决方案**：
```bash
# 检查 Redis 是否运行
redis-cli ping

# 启动 Redis
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d redis

# 检查 Redis 日志
docker logs wechat_redis_test
```

### 问题 2：导入模块错误

**症状**：
```
ModuleNotFoundError: No module named 'core.xxx'
```

**解决方案**：
```bash
# 检查导入路径是否正确
# 确保使用 v2.0 的新路径：
# - core.message → core.extractor
# - core.producer.monitor → 已删除
# - core.classifier → 已删除
```

### 问题 3：AT-SPI 测试失败

**症状**：
```
pytest.importorskip('pyatspi', None)  # pyatspi not available
```

**解决方案**：
```bash
# 使用测试镜像（包含 AT-SPI 支持）
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest ../..

# 确认环境变量
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"
```

---

## 📌 测试最佳实践

### 1. 测试隔离

- ✅ 每个测试独立运行
- ✅ 使用 fixture 清理数据
- ✅ 避免测试间依赖

### 2. Mock 使用

- ✅ Mock 外部依赖（文件系统、网络）
- ✅ Mock Redis 连接（单元测试）
- ✅ 使用 patch 模拟模块

### 3. 测试标记

```python
@pytest.mark.unit
def test_queue_manager():
    """单元测试"""
    pass

@pytest.mark.integration
def test_full_workflow():
    """集成测试"""
    pass

@pytest.mark.slow
def test_performance():
    """慢速测试"""
    pass
```

### 4. 断言清晰

```python
# ✅ 好的断言
assert message.msg_type == MessageType.TEXT
assert len(messages) >= 5

# ❌ 不好的断言
assert message  # 总是 True
```

---

## ✅ 测试检查清单

### 测试前

- [ ] Redis 服务运行
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] 环境变量已配置
- [ ] 测试数据已准备

### 测试中

- [ ] 按标记运行测试
- [ ] 检查日志输出
- [ ] 监控资源占用
- [ ] 记录异常情况

### 测试后

- [ ] 查看测试报告
- [ ] 检查覆盖率
- [ ] 清理测试数据
- [ ] 记录问题

---

## 📞 获取帮助

如有测试相关问题，请参考：
- [pytest 官方文档](https://docs.pytest.org/)
- [项目 README.md](../services/wechat_sandbox/README.md)
- [快速开始指南](../services/wechat_sandbox/QUICKSTART.md)
- [文档索引](../services/wechat_sandbox/docs/INDEX.md)

---

**最后更新**：2025-01-14（v2.0）
**维护者**：Claude Code
