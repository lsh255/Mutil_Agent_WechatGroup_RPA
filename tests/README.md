# 测试目录说明

本目录包含项目的所有测试脚本和测试工具，按功能模块组织。

## 目录结构

```
tests/
├── README.md                   # 本文件
├── atspi/                      # AT-SPI 相关测试
│   ├── test_atspi_observer.py  # AT-SPI 观察者单元测试
│   └── test_atspi_integration.py  # AT-SPI 集成测试（待创建）
└── wechat_sandbox/             # 微信沙盒测试
    ├── README.md               # 沙盒测试说明
    ├── sse_client.py           # SSE 客户端工具
    ├── sse_performance_test.py # SSE 性能测试工具
    ├── queue_monitor.py        # Redis 队列监控工具
    ├── queue_monitor.sh        # Redis 队列监控脚本
    ├── quick_test.sh           # 快速测试脚本
    ├── quick_test.bat          # Windows 快速测试脚本
    └── test_results/           # 测试结果输出目录
```

## 快速开始

### 前置条件

1. **启动测试环境**:
```bash
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d
```

2. **验证环境**:
```bash
# 检查容器状态
docker ps | grep wechat_sandbox_test

# 检查 AT-SPI 环境
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py
```

### AT-SPI 测试

**1. 运行 AT-SPI 单元测试**:
```bash
cd tests
pytest atspi/test_atspi_observer.py -v
```

**2. 运行 AT-SPI 集成测试**:
```bash
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh
```

**3. 启动 AT-SPI 观察者**:
```bash
docker exec -it wechat_sandbox_test python3 -m core.producer.atspi_observer
```

### 微信沙盒测试

**1. 监听 SSE 流**:
```bash
cd tests/wechat_sandbox
python sse_client.py
```

**2. 监控 Redis 队列**:
```bash
cd tests/wechat_sandbox
python queue_monitor.py
```

**3. 运行性能测试**:
```bash
cd tests/wechat_sandbox
python sse_performance_test.py --messages 100 --interval 1
```

**4. 快速测试脚本**:
```bash
cd tests/wechat_sandbox
./quick_test.sh
```

## 测试分类

### AT-SPI 测试 (tests/atspi/)

测试 AT-SPI 辅助功能框架相关功能：

| 测试文件 | 测试内容 | 运行方式 |
|---------|---------|----------|
| `test_atspi_observer.py` | AT-SPI 观察者单元测试 | pytest |
| `test_atspi_integration.py` | AT-SPI 集成测试 | docker exec |

**测试覆盖**:
- AT-SPI 初始化
- 微信窗口查找
- UI 控件树遍历
- 消息提取
- 实时监听
- 错误处理

### 微信沙盒测试 (tests/wechat_sandbox/)

测试微信沙盒的数据采集和SSE推送功能：

| 测试文件 | 测试内容 | 运行方式 |
|---------|---------|----------|
| `sse_client.py` | SSE 流监听 | python |
| `sse_performance_test.py` | SSE 性能测试 | python |
| `queue_monitor.py` | Redis 队列监控 | python |
| `quick_test.sh` | 快速端到端测试 | bash |

**测试覆盖**:
- 双生产者架构
- AT-SPI 混合方案
- SSE 实时推送
- Redis 队列流转
- 性能和稳定性

## 测试结果

所有测试结果保存在 `tests/wechat_sandbox/test_results/` 目录：

```
test_results/
├── messages_20250112_120000.json  # SSE 消息记录
├── queue_export_raw.json          # 原始队列导出
├── queue_export_precise.json      # 精确队列导出
└── performance_report_20250112.json  # 性能测试报告
```

## 编写新测试

### AT-SPI 测试模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AT-SPI 测试模板"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.producer.atspi_observer import ATSPIObserver

class TestATSPIFeature:
    """AT-SPI 功能测试"""

    def test_initialization(self):
        """测试 AT-SPI 初始化"""
        observer = ATSPIObserver()
        assert observer.initialize() is True

    def test_window_finding(self):
        """测试窗口查找"""
        observer = ATSPIObserver()
        observer.initialize()
        assert observer.wechat_window is not None
```

### 集成测试模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集成测试模板"""

import time
import redis
from pathlib import Path

def test_hybrid_producer():
    """测试混合生产者"""

    # 1. 连接 Redis
    r = redis.Redis(host='localhost', port=6379, db=0)

    # 2. 清空队列
    r.delete('wechat:messages:precise')

    # 3. 发送测试消息
    # (在微信群中发送消息)

    # 4. 等待处理
    time.sleep(2)

    # 5. 验证队列
    length = r.xlen('wechat:messages:precise')
    assert length > 0
```

## 调试技巧

### 1. 使用 Accerciser 调试 UI 控件树

```bash
# 启动 Accerciser
docker exec -it wechat_sandbox_test bash -c "DISPLAY=:99 accerciser &"

# 在 noVNC 中访问
# http://localhost:6080
```

### 2. 监控 Redis 队列

```bash
# 实时监控队列长度
watch -n 1 'docker exec -it wechat_redis_test redis-cli XLEN wechat:messages:precise'

# 查看最新消息
docker exec -it wechat_redis_test redis-cli XREVRANGE wechat:messages:precise - + COUNT 1
```

### 3. 查看容器日志

```bash
# 查看沙盒日志
docker logs -f wechat_sandbox_test

# 查看特定模块日志
docker logs wechat_sandbox_test | grep -i atspi
```

### 4. 进入容器调试

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 手动运行测试
python3 -c "
from core.producer.atspi_observer import ATSPIObserver
observer = ATSPIObserver()
observer.initialize()
print(observer.get_message_list_snapshot())
"
```

## 常见问题

### 问题1: pytest 找不到模块

**解决方案**:
```bash
# 确保在项目根目录运行
cd /path/to/project
pytest tests/atspi/test_atspi_observer.py -v

# 或设置 PYTHONPATH
export PYTHONPATH=/path/to/project:$PYTHONPATH
pytest tests/atspi/test_atspi_observer.py -v
```

### 问题2: Redis 连接失败

**解决方案**:
```bash
# 检查 Redis 容器
docker ps | grep redis

# 检查 Redis 端口
docker exec -it wechat_redis_test redis-cli ping
```

### 问题3: AT-SPI 初始化失败

**解决方案**:
```bash
# 检查环境变量
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"

# 重启微信
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/restart_wechat_with_dbus.sh
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run AT-SPI tests
        run: |
          docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d
          pytest tests/atspi/
      - name: Run integration tests
        run: |
          python tests/wechat_sandbox/sse_performance_test.py
```

## 相关文档

- [测试方案文档](../docs/wechat_sandbox_test_plan.md)
- [AT-SPI 混合方案](../docs/atspi_hybrid_solution.md)
- [Docker 文档](../docker/README.md)
- [微信沙盒架构](../services/wechat_sandbox/ARCHITECTURE.md)

## 贡献指南

添加新测试时，请遵循以下规则：

1. **命名规范**:
   - 单元测试: `test_<module>_<feature>.py`
   - 集成测试: `test_<feature>_integration.py`

2. **文档注释**:
   - 每个测试类和测试方法添加 docstring
   - 说明测试目的和预期结果

3. **断言清晰**:
   - 使用明确的断言消息
   - 测试失败时提供有用的错误信息

4. **测试隔离**:
   - 每个测试独立运行
   - 使用 setup/teardown 清理资源

5. **结果记录**:
   - 测试结果保存到 `test_results/` 目录
   - 包含时间戳和详细日志
