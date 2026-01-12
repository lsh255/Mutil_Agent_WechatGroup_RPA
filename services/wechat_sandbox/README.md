# WeChat 沙箱服务

## 概述

微信沙盒服务是基于 Linux 微信的容器化消息采集系统，支持多种消息采集方案：

### 数据采集方案

1. **AT-SPI 混合方案**（推荐）
   - 主要方案：AT-SPI UI控件监听
   - 兜底方案：视觉技术（自动降级）
   - 优势：速度快、资源占用少、准确率高

2. **双生产者架构**（传统方案）
   - Producer1 (Observer): 检测消息气泡
   - Producer2 (ContentFetcher): 提取精确内容
   - 优势：兼容性好、适用场景广

### 功能特性

- ✅ 实时消息采集（文本、图片、视频、链接）
- ✅ SSE 实时推送
- ✅ Redis Stream 队列
- ✅ FastAPI REST 接口
- ✅ 多实例部署支持
- ✅ AT-SPI 辅助功能集成

## 前置要求

### 基础环境
- **Docker**: 20.10+
- **Redis**: 7.2+
- **Python**: 3.10+

### 构建依赖
- Linux 微信安装包: `build/WeChatLinux_x86_64.deb`
- 中文字体包: `build/fonts-noto-cjk_20240730+repack1-1_all.deb`

### AT-SPI 环境（可选）
- 环境变量：`QT_ACCESSIBILITY=1`, `GNOME_ACCESSIBILITY=1`
- 依赖：pyatspi, at-spi2-core
- 工具：Accerciser（调试工具）

## 目录结构

```
services/wechat_sandbox/
├── README.md                   # 本文件
├── ARCHITECTURE.md             # 架构设计文档
├── QUICKSTART.md               # 快速开始指南
├── BUSINESS_LOGIC_TEST.md      # 业务逻辑测试指南
├── main.py                     # 主启动脚本
├── config.yaml                 # 配置文件
├── config.production.yaml      # 生产环境配置
├── requirements.txt            # Python 依赖
│
├── api/                        # API 模块
│   ├── __init__.py
│   ├── app.py                  # FastAPI 应用
│   ├── routes/                 # API 路由
│   │   ├── __init__.py
│   │   ├── message.py          # 消息路由
│   │   ├── sandbox.py          # 沙盒路由
│   │   └── config.py           # 配置路由
│   └── models/                 # Pydantic 数据模型
│       ├── __init__.py
│       └── schema.py
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── detector/               # 变化检测模块
│   │   ├── __init__.py
│   │   └── bubble_detector.py  # 气泡检测器
│   ├── extractor/              # 内容提取模块
│   │   ├── __init__.py
│   │   ├── text_extractor.py   # 文本提取
│   │   └── media_extractor.py  # 媒体提取
│   ├── producer/               # 生产者模块 ⭐
│   │   ├── __init__.py
│   │   ├── observer.py         # 视觉观察者（基础）
│   │   ├── monitor.py          # 消息监控器
│   │   ├── content_fetcher.py  # 内容提取器
│   │   ├── agent_consumer.py   # Agent 消费者
│   │   ├── atspi_observer.py   # AT-SPI 观察者 ⭐
│   │   ├── chat_window_listener.py   # 聊天窗口监听 ⭐
│   │   ├── global_chat_listener.py   # 全局聊天监听 ⭐
│   │   └── hybrid_producer.py  # 混合生产者 ⭐
│   ├── queue/                  # Redis 队列管理
│   │   ├── __init__.py
│   │   └── stream_manager.py   # Stream 管理器
│   ├── classifier/             # 消息分类器
│   │   ├── __init__.py
│   │   └── message_classifier.py
│   └── platform/               # 平台适配
│       ├── __init__.py
│       └── linux_adapter.py
│
├── utils/                      # 工具类
│   ├── __init__.py
│   ├── config.py               # 配置加载
│   ├── logger.py               # 日志工具
│   └── redis_client.py         # Redis 客户端
│
├── services/                   # 服务模块
│   ├── __init__.py
│   └── ...
│
├── tests/                      # 单元测试
│   ├── __init__.py
│   └── ...
│
├── media/                      # 媒体文件（自动创建）
├── logs/                       # 日志文件（自动创建）
├── data/                       # 数据文件
├── static/                     # 静态文件
└── archive/                    # 归档文件
```

⭐ 标记为 AT-SPI 混合方案相关的新增模块

## 核心模块说明

### Producer 模块 (core/producer/)

消息生产者模块，负责从微信界面采集消息并推送到队列。

| 模块 | 说明 | 方案 | 状态 |
|------|------|------|------|
| `observer.py` | 视觉观察者 | 双生产者 | ✅ 稳定 |
| `monitor.py` | 消息监控器 | 双生产者 | ✅ 稳定 |
| `content_fetcher.py` | 内容提取器 | 双生产者 | ✅ 稳定 |
| `agent_consumer.py` | Agent 消费者 | 通用 | ✅ 稳定 |
| `atspi_observer.py` | AT-SPI 观察者 | AT-SPI | ⭐ 新增 |
| `chat_window_listener.py` | 聊天窗口监听 | AT-SPI | ⭐ 新增 |
| `global_chat_listener.py` | 全局聊天监听 | AT-SPI | ⭐ 新增 |
| `hybrid_producer.py` | 混合生产者 | 混合 | ⭐ 新增 |

### API 模块 (api/)

FastAPI 应用，提供 REST 接口和 SSE 流。

| 路由 | 端点 | 说明 |
|------|------|------|
| `message.py` | `/api/stream/messages` | SSE 消息流 |
| `sandbox.py` | `/api/sandbox/*` | 沙盒管理接口 |
| `config.py` | `/api/config/*` | 配置管理接口 |

### Detector 模块 (core/detector/)

变化检测模块，用于检测界面变化和新消息。

| 模块 | 功能 |
|------|------|
| `bubble_detector.py` | 气泡检测（dHash 算法）|

### Extractor 模块 (core/extractor/)

内容提取模块，从界面提取文本和媒体内容。

| 模块 | 功能 |
|------|------|
| `text_extractor.py` | OCR 文本提取 |
| `media_extractor.py` | 媒体文件截图 |

## 配置说明

### config.yaml

主要配置项：

```yaml
wechat:
  instance_id: default
  group_name: "测试群"

monitor:
  screenshot_interval: 1
  check_interval: 0.5

roi:
  x: 0
  y: 0
  width: 400
  height: 800

redis:
  host: localhost
  port: 6379
  db: 0
```

### AT-SPI 配置（测试环境）

AT-SPI 相关的环境变量：

```yaml
# 环境变量（在 Dockerfile.test 中设置）
QT_ACCESSIBILITY: 1
GNOME_ACCESSIBILITY: 1
QT_LINUX_ACCESSIBILITY_ALWAYS_ON: 1
TZ: Asia/Shanghai
```

## 使用方法

### 1. 构建镜像

**基础镜像（生产环境）：**
```bash
docker build -f docker/sandbox/Dockerfile -t wechat_sandbox:latest ../..
```

**测试镜像（带 AT-SPI）：**
```bash
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest ../..
```

### 2. 启动服务

**使用 Docker Compose（推荐）：**
```bash
# 测试环境（AT-SPI 支持）
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 生产环境
docker-compose -f docker/compose/docker-compose.prod.yml up -d
```

**手动运行容器：**
```bash
docker run -d --name wechat_sandbox \
  --privileged \
  -p 8000:8000 \
  -p 6080:6080 \
  -p 5900:5900 \
  -v $(pwd)/media:/app/media \
  -v $(pwd)/logs:/app/logs \
  -e DISPLAY=:99 \
  wechat_sandbox:latest
```

### 3. 启动消息生产者

**AT-SPI 混合方案：**
```bash
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer
```

**双生产者架构：**
```bash
# Producer1: Observer
docker exec -it wechat_sandbox python3 -m core.producer.observer

# Producer2: ContentFetcher
docker exec -it wechat_sandbox python3 -m core.producer.content_fetcher
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| noVNC | http://localhost:6080 | Web 界面 |
| API 文档 | http://localhost:8000/docs | Swagger |
| SSE 流 | http://localhost:8000/api/stream/messages | 消息流 |
| 健康检查 | http://localhost:8000/health | 健康状态 |

## AT-SPI 混合方案使用

### 快速测试

```bash
# 1. 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 2. 运行 AT-SPI 简单测试
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py

# 3. 运行 AT-SPI 完整测试
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh

# 4. 启动混合生产者
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer
```

### 启动脚本

容器内可用的启动脚本（位于 `/app/docker/scripts/`）：

**通用脚本：**
- `common/start_all.sh` - 启动所有服务
- `common/start_sandbox.sh` - 启动沙盒容器
- `common/start_wechat.sh` - 启动微信应用

**AT-SPI 脚本：**
- `atspi/restart_wechat_with_dbus.sh` - 重启微信（使用 DBus）
- `atspi/run_atspi_observer.sh` - 运行 AT-SPI 观察者
- `atspi/test_atspi_simple.py` - AT-SPI 简单测试
- `atspi/test_atspi_solution.sh` - AT-SPI 完整测试

## 数据流

### AT-SPI 混合方案

```
┌─────────────────┐
│  WeChat App     │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ AT-SPI   │ (UI 控件监听)
    │ Observer  │
    └────┬─────┘
         │
    ┌────▼──────┐
    │  Hybrid   │ (混合生产者)
    │ Producer  │
    └────┬──────┘
         │
    ┌────▼────────────┐
    │  Redis Stream   │
    │  (precise)      │
    └─────────────────┘
```

### 双生产者架构

```
┌─────────────────┐
│  WeChat App     │
└────────┬────────┘
         │
    ┌────▼─────────┐
    │   Observer    │ (检测气泡)
    │  Producer1    │
    └────┬─────────┘
         │
    ┌────▼──────────┐
    │  Redis Stream │
    │   (raw)       │
    └────┬──────────┘
         │
    ┌────▼─────────────┐
    │ ContentFetcher   │ (提取内容)
    │   Producer2      │
    └────┬─────────────┘
         │
    ┌────▼────────────┐
    │  Redis Stream   │
    │   (precise)     │
    └─────────────────┘
```

## API 接口

### SSE 消息流

```bash
curl -N http://localhost:8000/api/stream/messages
```

响应格式：
```
event: message
data: {"sender":"张三","content":"测试消息","type":"text","timestamp":"2025-01-12T12:00:00"}

event: heartbeat
data: {"timestamp":"2025-01-12T12:00:05"}
```

### 沙盒管理

```bash
# 获取沙盒状态
curl http://localhost:8000/api/sandbox/status

# 启动沙盒
curl -X POST http://localhost:8000/api/sandbox/start

# 停止沙盒
curl -X POST http://localhost:8000/api/sandbox/stop

# 重启沙盒
curl -X POST http://localhost:8000/api/sandbox/restart
```

## 测试

### 运行单元测试

```bash
# 运行所有测试
pytest services/wechat_sandbox/tests/

# 运行特定测试
pytest services/wechat_sandbox/tests/test_producer.py -v

# 查看覆盖率
pytest --cov=services/wechat_sandbox services/wechat_sandbox/tests/
```

### 运行集成测试

```bash
# 在项目根目录
pytest tests/atspi/test_atspi_observer.py -v
```

## 故障排查

### AT-SPI 相关问题

**问题1: AT-SPI 找不到微信窗口**
```bash
# 检查环境变量
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"

# 重启微信（使用 DBus）
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/restart_wechat_with_dbus.sh
```

**问题2: AT-SPI 服务未运行**
```bash
# 检查 AT-SPI 进程
docker exec -it wechat_sandbox_test ps aux | grep at-spi

# 使用 Accerciser 调试
docker exec -it wechat_sandbox_test bash -c "accerciser &"
```

### Redis 连接问题

```bash
# 检查 Redis 连接
docker exec -it wechat_sandbox_test python3 -c "
from utils.redis_client import get_redis_client
r = get_redis_client()
print(r.ping())
"
```

### 其他问题

详见：
- [故障排查文档](../docs/wechat_sandbox_test_plan.md#常见问题和解决方案)
- [Docker 主文档](../../docker/README.md#故障排查)

## 相关文档

### 项目文档
- [项目架构文档](ARCHITECTURE.md)
- [快速开始](QUICKSTART.md)
- [业务逻辑测试](BUSINESS_LOGIC_TEST.md)

### 技术文档
- [AT-SPI 混合方案说明](../../docs/atspi_hybrid_solution.md)
- [AT-SPI 部署配置](../../docs/atspi_deployment_config.md)
- [测试方案](../../docs/wechat_sandbox_test_plan.md)

### Docker 文档
- [Docker 主文档](../../docker/README.md)
- [脚本说明](../../docker/scripts/README.md)

## 版本历史

- **2025-01-12**:
  - 添加 AT-SPI 混合方案支持
  - 新增 `atspi_observer.py`, `chat_window_listener.py`, `global_chat_listener.py`, `hybrid_producer.py`
  - 更新 Docker 镜像分层结构
  - 整理启动脚本到 `docker/scripts/common/` 和 `docker/scripts/atspi/`

- **早期版本**:
  - 实现双生产者架构
  - 实现 SSE 推送
  - 实现消息分类和提取

## 贡献指南

### 添加新的 Producer

1. 在 `core/producer/` 创建新文件
2. 继承基础接口或参考现有实现
3. 添加单元测试
4. 更新本文档

### 代码规范

- 使用类型注解
- 添加文档字符串
- 遵循 PEP 8 规范
- 添加日志记录

## 许可证

本项目遵循项目主许可证。
