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

3. **通用消息提取**（新增⭐）
   - 点击所有消息判断类型
   - 根据窗口标题自动分类（text/photo/video/file/link）
   - 自动保存文件到物理机

### 功能特性

- ✅ 实时消息采集（文本、图片、视频、文件、链接）
- ✅ SSE 实时推送（JSONL 格式）
- ✅ Redis Stream 队列
- ✅ FastAPI REST 接口
- ✅ 多实例部署支持
- ✅ AT-SPI 辅助功能集成
- ✅ 通用消息提取（点击消息判断类型）
- ✅ 文件自动保存到物理机

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

### 通用消息提取工具
- xdotool：点击工具
- scrot：截图工具（可选）

## 目录结构

```
services/wechat_sandbox/
├── README.md                        # 本文件
├── DIRECTORY_STRUCTURE.md           # 目录结构详细说明 ⭐
├── ARCHITECTURE.md                  # 架构设计文档
├── QUICKSTART.md                    # 快速开始指南
├── BUSINESS_LOGIC_TEST.md           # 业务逻辑测试指南
├── main.py                          # 主启动脚本
├── config.yaml                      # 配置文件
├── config.production.yaml           # 生产环境配置
├── requirements.txt                 # Python 依赖
│
├── api/                             # API 模块
│   ├── __init__.py
│   ├── app.py                       # FastAPI 应用
│   ├── config.py                    # 配置 API
│   ├── health.py                    # 健康检查
│   ├── instance.py                  # 实例管理
│   └── stream.py                    # SSE 流接口
│
├── core/                            # 核心业务逻辑
│   ├── __init__.py
│   │
│   ├── atspi/                       # AT-SPI 模块 ⭐ 新结构
│   │   ├── __init__.py
│   │   ├── observer.py              # AT-SPI 观察者
│   │   ├── chat_listener.py         # 聊天窗口监听器
│   │   └── global_listener.py       # 全局聊天监听器
│   │
│   ├── message/                     # 消息处理模块 ⭐ 新结构
│   │   ├── __init__.py
│   │   ├── extractor.py             # 通用消息提取器
│   │   └── models.py                # 消息数据模型
│   │
│   ├── window/                      # 窗口管理模块 ⭐ 新结构
│   │   ├── __init__.py
│   │   ├── manager.py               # 窗口管理器
│   │   └── interaction.py           # 窗口交互
│   │
│   ├── producer/                    # 生产者模块（重构）
│   │   ├── __init__.py
│   │   ├── hybrid_producer.py       # 混合生产者
│   │   ├── observer.py              # 视觉观察者（基础）
│   │   ├── monitor.py               # 消息监控器
│   │   ├── content_fetcher.py       # 内容提取器
│   │   └── agent_consumer.py        # Agent 消费者
│   │
│   ├── detector/                    # 视觉检测模块
│   │   ├── __init__.py
│   │   ├── detector.py              # 气泡检测器
│   │   ├── visual_monitor.py        # 视觉监控
│   │   └── change_detector.py       # 变化检测器
│   │
│   ├── extractor/                   # 内容提取模块（视觉方案）
│   │   ├── __init__.py
│   │   ├── extractor.py             # 基础提取器
│   │   └── text_extractor.py        # 文本提取器
│   │
│   ├── classifier/                  # 消息分类器
│   │   └── classifier.py
│   │
│   ├── platform/                    # 平台适配
│   │   └── adapter.py
│   │
│   └── queue/                       # Redis 队列管理
│       ├── __init__.py
│       └── manager.py
│
├── services/                        # 服务模块
│   ├── __init__.py
│   └── producer_service.py
│
├── utils/                           # 工具类
│   ├── __init__.py
│   ├── config.py                    # 配置加载
│   ├── logger.py                    # 日志工具
│   └── platform_adapter.py          # 平台适配
│
├── tests/                           # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api_server.py
│   ├── test_integration.py
│   ├── test_producer_service.py
│   └── test_queue_manager.py
│
├── docs/                            # 文档（部分移到 core/）
│   ├── atspi_hybrid_solution.md
│   └── wechat_sandbox_test_plan.md
│
├── media/                           # 媒体文件（自动创建）
├── logs/                            # 日志文件（自动创建）
├── data/                            # 数据文件
└── static/                          # 静态文件
```

⭐ 标记为目录结构重组后的新模块

详细的目录结构说明请查看 [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)

## 核心模块说明

### AT-SPI 模块 (core/atspi/)

AT-SPI 相关功能模块，提供基于 UI 控件树的消息监听。

| 模块 | 说明 | 方案 | 状态 |
|------|------|------|------|
| `observer.py` | AT-SPI 观察者 | AT-SPI | ✅ 稳定 |
| `chat_listener.py` | 指定聊天窗口监听 | AT-SPI | ✅ 稳定 |
| `global_listener.py` | 全局聊天监听 | AT-SPI | ✅ 稳定 |

**导入路径：**
```python
from core.atspi.observer import ATSPIObserver
from core.atspi.chat_listener import ChatWindowListener
from core.atspi.global_listener import GlobalChatListener
```

### 消息处理模块 (core/message/)

消息提取和处理模块，支持通用消息提取。

| 模块 | 说明 | 特性 | 状态 |
|------|------|------|------|
| `extractor.py` | 通用消息提取器 | 点击消息判断类型 | ⭐ 新增 |
| `models.py` | 消息数据模型 | SSE JSONL 格式 | ⭐ 新增 |

**导入路径：**
```python
from core.message.extractor import UniversalMessageExtractor, MessageType
from core.message.models import ExtractedMessage
```

### 窗口管理模块 (core/window/)

窗口相关操作模块（待扩展）。

| 模块 | 说明 | 状态 |
|------|------|------|
| `manager.py` | 窗口管理器 | 🚧 待实现 |
| `interaction.py` | 窗口交互 | 🚧 待实现 |

### Producer 模块 (core/producer/)

消息生产者模块，负责任务编排和队列管理。

| 模块 | 说明 | 方案 | 状态 |
|------|------|------|------|
| `hybrid_producer.py` | 混合生产者 | AT-SPI + 视觉 | ✅ 推荐 |
| `observer.py` | 视觉观察者 | 双生产者 | ✅ 稳定 |
| `monitor.py` | 消息监控器 | 双生产者 | ✅ 稳定 |
| `content_fetcher.py` | 内容提取器 | 双生产者 | ✅ 稳定 |
| `agent_consumer.py` | Agent 消费者 | 通用 | ✅ 稳定 |

**导入路径：**
```python
from core.producer.hybrid_producer import HybridProducer, ProductionMode
```

### API 模块 (api/)

FastAPI 应用，提供 REST 接口和 SSE 流。

| 路由 | 端点 | 说明 |
|------|------|------|
| `config.py` | `/api/config/*` | 配置管理 |
| `health.py` | `/health` | 健康检查 |
| `instance.py` | `/api/instances/*` | 实例管理 |
| `stream.py` | `/api/stream/messages` | SSE 消息流 |

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

# 通用消息提取配置 ⭐ 新增
message_extraction:
  enabled: true
  save_dir: /host/data
  click_timeout: 2.0
  window_wait_timeout: 5.0
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

### Docker 挂载配置

物理机文件保存目录：

```yaml
# docker-compose.yml
services:
  wechat_sandbox:
    volumes:
      - /path/on/host:/host/data
    environment:
      - SAVE_DIR=/host/data
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
  -v /path/on/host:/host/data \
  -e DISPLAY=:99 \
  wechat_sandbox:latest
```

### 3. 启动消息生产者

**使用混合生产者（推荐）：**
```bash
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer
```

**使用通用消息提取：**
```python
from core.atspi.observer import ATSPIObserver

observer = ATSPIObserver(
    enable_universal_extraction=True,
    save_dir="/host/data"
)

if observer.initialize():
    observer.start_monitoring(interval=0.5)
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

## 通用消息提取

### 工作流程

```
1. 检测新消息
   ↓
2. 点击消息（所有消息）
   ↓
3. 检测是否唤起新窗口
   ├─ 否 → 文本消息
   └─ 是 → 继续判断
           ↓
       获取窗口标题
           ↓
       ├─ "Photos and Videos" → 图片/视频
       ├─ "File Transfer" → 文件
       ├─ "Browser" → 链接
       └─ 其他 → 其他类型
                  ↓
              保存到物理机 (/host/data/)
```

### 消息类型映射

| 窗口标题 | 消息类型 | 保存目录 |
|---------|---------|---------|
| (无窗口) | text | 不保存 |
| Photos and Videos | photo/video | /host/data/photos/ 或 /host/data/videos/ |
| File Transfer | file | /host/data/files/ |
| Browser | link | /host/data/links/ |
| 其他 | other | /host/data/others/ |

### 使用示例

```python
from core.message.extractor import UniversalMessageExtractor

# 创建提取器
extractor = UniversalMessageExtractor(save_dir="/host/data")

# 初始化
if extractor.initialize():
    # 提取消息
    result = extractor.extract_message(message_item, sender="张三")

    if result:
        print(f"类型: {result.msg_type.value}")
        print(f"窗口: {result.window_title}")
        print(f"路径: {result.high_res_media_path}")

        # 转换为 SSE JSONL
        sse_json = result.to_sse_json()
        print(sse_json)
```

## SSE 推送格式

### JSONL 格式

SSE 推送使用 JSONL（JSON Lines）格式，每行一个完整的 JSON 对象。

```bash
curl -N http://localhost:8000/api/stream/messages
```

### 示例输出

```javascript
// 文本消息
data: {"id":"msg_20250112_143022_001","timestamp":1736653822.123,"type":"text","sender":"张三","content":{"type":"text","text":"今天作业w1作业前"},"group_name":"测试群聊","window_detected":false,"window_title":null,"metadata":{"producer":"universal_extractor","production_mode":"atspi","processed_at":"2025-01-12T14:30:22.123456"}}

// 图片消息
data: {"id":"msg_20250112_143025_002","timestamp":1736653825.456,"type":"photo","sender":"李四","content":{"type":"photo","text":"[Photo]","high_res_media_path":"/host/data/photos/photo_20250112_143025.png"},"group_name":"测试群聊","window_detected":true,"window_title":"Photos and Videos","metadata":{"producer":"universal_extractor","production_mode":"atspi","processed_at":"2025-01-12T14:30:25.456789","window_opened":true,"save_path":"/host/data/photos/photo_20250112_143025.png"}}
```

### 数据模型

完整的数据模型定义请查看：
- [SSE_MESSAGE_MODEL.md](core/producer/SSE_MESSAGE_MODEL.md) - 数据模型详细定义
- [sse_message_model.jsonl](core/producer/sse_message_model.jsonl) - JSONL 格式示例

## API 接口

### SSE 消息流

```bash
curl -N http://localhost:8000/api/stream/messages
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

### 实例管理

```bash
# 获取所有实例
curl http://localhost:8000/api/instances

# 获取实例状态
curl http://localhost:8000/api/instances/{instance_id}/status

# 启动实例
curl -X POST http://localhost:8000/api/instances/{instance_id}/start

# 停止实例
curl -X POST http://localhost:8000/api/instances/{instance_id}/stop
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

### 通用消息提取测试

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 测试通用提取器
python3 -m core.message.extractor

# 测试 ATSPI 观察者
python3 -m core.atspi.observer
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

### 通用消息提取问题

**问题1: 点击操作失败**
```bash
# 检查 xdotool
docker exec -it wechat_sandbox_test which xdotool

# 安装 xdotool
docker exec -it wechat_sandbox_test apt-get install -y xdotool
```

**问题2: 文件保存失败**
```bash
# 检查挂载目录
docker exec -it wechat_sandbox_test ls -la /host/data

# 检查写权限
docker exec -it wechat_sandbox_test touch /host/data/test.txt
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
- [故障排查文档](../../docs/wechat_sandbox_test_plan.md#常见问题和解决方案)
- [Docker 主文档](../../docker/README.md#故障排查)
- [AT-SPI 部署配置](../../docs/atspi_deployment_config.md#故障排查)

## 相关文档

### 项目文档
- [目录结构详细说明](DIRECTORY_STRUCTURE.md) ⭐ 新增
- [项目架构文档](ARCHITECTURE.md)
- [快速开始](QUICKSTART.md)
- [业务逻辑测试](BUSINESS_LOGIC_TEST.md)

### 技术文档
- [AT-SPI 混合方案说明](../../docs/atspi_hybrid_solution.md)
- [AT-SPI 部署配置](../../docs/atspi_deployment_config.md)
- [SSE 消息数据模型](core/producer/SSE_MESSAGE_MODEL.md) ⭐ 新增
- [通用消息提取说明](core/producer/UNIVERSAL_MESSAGE_EXTRACTION.md) ⭐ 新增
- [测试方案](../../docs/wechat_sandbox_test_plan.md)

### Docker 文档
- [Docker 主文档](../../docker/README.md)
- [脚本说明](../../docker/scripts/README.md)

## 版本历史

### 2025-01-12 (v2.0)
  - ⭐ **目录结构重组**
    - 新建 `core/atspi/` 模块
    - 新建 `core/message/` 模块
    - 新建 `core/window/` 模块
    - 保留旧文件作为备份
  - ⭐ **通用消息提取**
    - 实现点击消息判断类型的逻辑
    - 支持根据窗口标题自动分类
    - 文件自动保存到物理机
  - ⭐ **SSE JSONL 格式**
    - 推送格式改为 JSONL
    - 新增完整的数据模型定义
  - 更新导入路径
  - 更新文档

### 早期版本
  - 实现双生产者架构
  - 实现 SSE 推送
  - 实现消息分类和提取
  - 添加 AT-SPI 混合方案支持

## 贡献指南

### 添加新的 Producer

1. 在 `core/producer/` 创建新文件
2. 继承基础接口或参考现有实现
3. 添加单元测试
4. 更新本文档

### 添加新的消息类型

1. 在 `core/message/` 中扩展 `MessageType`
2. 更新 `extractor.py` 中的类型判断逻辑
3. 添加对应的数据模型
4. 更新 SSE 数据模型文档

### 代码规范

- 使用类型注解
- 添加文档字符串
- 遵循 PEP 8 规范
- 添加日志记录
- 保持模块职责单一

## 许可证

本项目遵循项目主许可证。
