# WeChat Sandbox 测试用例（v2.0）

## 📋 概述

本目录包含 WeChat Sandbox 的集成测试和端到端测试用例。

## 🗂️ 目录结构

```
test/
├── README.md                       # 本文件
├── atspi/                          # AT-SPI 集成测试
│   ├── __init__.py
│   ├── test_atspi_observer.py    # AT-SPI 观察者集成测试
│   └── test_atspi_integration.py  # AT-SPI 完整工作流测试
├── integration/                   # 集成测试
│   ├── __init__.py
│   ├── test_docker_integration.py # Docker 集成测试
│   ├── test_api_integration.py    # API 集成测试
│   └── test_e2e_workflow.py       # 端到端工作流测试
├── performance/                    # 性能测试
│   ├── __init__.py
│   ├── test_load_test.py         # 负载测试
│   ├── test_stress_test.py       # 压力测试
│   └── test_benchmark.py         # 基准测试
└── utils/                         # 测试工具
    ├── __init__.py
    ├── sse_client.py             # SSE 客户端工具
    ├── redis_monitor.py          # Redis 监控工具
    └── test_helpers.py           # 测试辅助函数
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入项目根目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 安装测试依赖
pip install -r services/wechat_sandbox/requirements.txt

# 确认 Redis 运行
redis-cli ping
```

### 2. 运行测试

```bash
# 运行所有集成测试
pytest test/ -v

# 运行特定类型的测试
pytest test/atspi/ -v
pytest test/integration/ -v
pytest test/performance/ -v

# 运行特定测试文件
pytest test/atspi/test_atspi_observer.py -v

# 生成覆盖率报告
pytest test/ --cov=services.wechat_sandbox --cov-report=html
```

### 3. Docker 环境

```bash
# 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 运行集成测试
pytest test/integration/ -v

# 查看日志
docker logs -f wechat_sandbox_test

# 停止环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down
```

## 📝 测试用例说明

### AT-SPI 集成测试

**文件**: `test/atspi/test_atspi_observer.py`

**目的**: 验证 AT-SPI 观察者在真实环境中的功能

**测试用例**:
- `test_atspi_initialization()` - AT-SPI 初始化
- `test_find_wechat_window()` - 查找微信窗口
- `test_get_message_list()` - 获取消息列表
- `test_monitor_new_messages()` - 监听新消息（10秒）
- `test_callback_invocation()` - 回调函数调用

**依赖**: 需要运行中的微信和 AT-SPI 支持

### API 集成测试

**文件**: `test/integration/test_api_integration.py`

**目的**: 验证 FastAPI 服务器的功能

**测试用例**:
- `test_health_check()` - 健康检查
- `test_sse_connection()` - SSE 连接
- `test_sse_message_format()` - SSE 消息格式
- `test_update_roi()` - 更新 ROI 配置
- `test_screenshot()` - 截图功能

**依赖**: 需要运行的 FastAPI 服务

### 端到端工作流测试

**文件**: `test/integration/test_e2e_workflow.py`

**目的**: 验证完整的消息流

**测试场景**:
1. 发送文本消息 → AT-SPI 提取 → SSE 推送
2. 发送图片消息 → AT-SPI 提取 → 保存文件 → SSE 推送
3. 发送视频消息 → AT-SPI 提取 → 保存文件 → SSE 推送
4. 发送文件消息 → 保存到物理机（无 SSE）

**依赖**: 完整的 Docker 环境

### 性能测试

**文件**: `test/performance/test_load_test.py`

**目的**: 验证系统在高负载下的表现

**测试指标**:
- 消息处理延迟
- SSE 推送延迟
- 内存占用
- CPU 占用

**测试场景**:
- 100 条消息/分钟
- 1000 条消息/分钟
- 并发连接数

## 🛠️ 测试工具

### SSE 客户端

```bash
# 使用 SSE 客户端监听消息
python test/utils/sse_client.py --url http://localhost:8000/api/stream/messages

# 监听 30 秒
python test/utils/sse_client.py --url http://localhost:8000/api/stream/messages --duration 30
```

### Redis 监控

```bash
# 监控 Redis 队列
python test/utils/redis_monitor.py --stream wechat:messages:precise

# 查看队列长度
python test/utils/redis_monitor.py --length wechat:messages:precise
```

## 📊 测试报告

测试完成后，生成以下报告：

1. **覆盖率报告**: `test/htmlcov/index.html`
2. **性能报告**: `test/reports/performance_report.html`
3. **测试日志**: `test/logs/test_run.log`

## 🔧 故障排查

### 问题 1: AT-SPI 测试失败

**症状**: `ModuleNotFoundError: pyatspi`

**解决方案**:
```bash
# 使用包含 AT-SPI 的测试镜像
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest ../..

# 确认环境变量
docker exec -it wechat_sandbox_test env | grep QT_ACCESSIBILITY
```

### 问题 2: API 测试失败

**症状**: `Connection refused`

**解决方案**:
```bash
# 确认服务运行
curl http://localhost:8000/health

# 启动服务
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 查看日志
docker logs wechat_sandbox_test
```

### 问题 3: Redis 连接失败

**症状**: `Redis connection error`

**解决方案**:
```bash
# 检查 Redis
redis-cli ping

# 启动 Redis
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d redis
```

## 📚 相关文档

- [测试方案](../../docs/wechat_sandbox_test_plan.md) - 完整测试方案
- [项目 README](../../services/wechat_sandbox/README.md) - 项目说明
- [快速开始](../../services/wechat_sandbox/QUICKSTART.md) - 快速开始指南

---

**最后更新**: 2025-01-14（v2.0）
**维护者**: Claude Code
