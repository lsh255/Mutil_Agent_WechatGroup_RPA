# WeChat 沙箱服务

## 概述

微信沙盒服务是基于 Linux 微信的容器化消息采集系统，支持多种消息采集方案。

### 数据采集方案

1. **AT-SPI 混合方案**（推荐）
   - 主要方案：AT-SPI UI控件监听
   - 兜底方案：视觉技术（自动降级）
   - 优势：速度快、资源占用少、准确率高

2. **通用消息提取**（新增⭐）
   - 点击所有消息判断类型
   - 根据窗口标题自动分类
   - **仅支持3种类型**：text、photo、video
   - 其他类型（file、link、表情包等）直接保存到物理机，不推送SSE

### 功能特性

- ✅ 实时消息采集（文本、图片、视频）
- ✅ SSE 实时推送（JSONL 格式）
- ✅ Redis Stream 队列
- ✅ FastAPI REST 接口
- ✅ 多实例部署支持
- ✅ AT-SPI 辅助功能集成
- ✅ 文件自动保存到物理机
- ✅ 沙盒独立性（独立配置和文档）

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
├── README.md                       # 本文件
├── QUICKSTART.md                   # 快速开始指南
├── CHANGELOG_v2.0.md               # 变更日志
├── DIRECTORY_STRUCTURE_V2.md       # 目录结构详细说明
├── main.py                         # 主启动脚本
├── config.yaml                     # 配置文件（已移至config/）
├── config.production.yaml          # 生产环境配置（已移至config/）
├── requirements.txt                # Python 依赖
│
├── config/                         # 配置管理 ⭐ 独立
│   ├── __init__.py
│   ├── config.py                   # 配置类
│   ├── config.yaml                 # 开发配置
│   └── config.production.yaml      # 生产配置
│
├── core/                           # 核心业务逻辑
│   ├── __init__.py
│   │
│   ├── atspi/                      # AT-SPI 模块
│   │   ├── __init__.py
│   │   ├── observer.py              # AT-SPI 观察者
│   │   ├── chat_listener.py         # 聊天窗口监听器
│   │   └── global_listener.py       # 全局聊天监听器
│   │
│   ├── extractor/                  # 消息提取模块 ⭐ 整合
│   │   ├── __init__.py
│   │   ├── message_extractor.py    # 通用消息提取器（主要实现）
│   │   ├── models.py                # 消息数据模型
│   │   ├── text_extractor.py        # 文本提取器（辅助）
│   │   └── extractor.py             # 已废弃 ⚠️
│   │
│   ├── producer/                   # 生产者模块（简化）
│   │   ├── __init__.py
│   │   ├── hybrid_producer.py      # 混合生产者
│   │   ├── consumer.py              # 消息消费者
│   │   ├── atspi_observer.py        # AT-SPI观察者（Producer版本）
│   │   ├── chat_window_listener.py  # 聊天窗口监听（Producer版本）
│   │   └── global_chat_listener.py  # 全局监听（Producer版本）
│   │
│   └── detector/                   # 视觉检测模块
│       ├── __init__.py
│       ├── change_detector.py       # 变化检测（区分图片/视频）⭐v2.1
│       ├── classifier.py            # 视觉分类器（已废弃）
│       ├── detector.py              # 气泡检测器（BubbleDetector）⭐v2.1
│       └── visual_monitor.py        # 视觉监控（窗口区域截图）⭐v2.1
│
├── api/                            # API 模块
│   ├── __init__.py
│   ├── config.py                   # 配置 API
│   ├── health.py                   # 健康检查
│   ├── instance.py                 # 实例管理
│   └── stream.py                   # SSE 流接口
│
├── services/                       # 服务模块
│   ├── __init__.py
│   └── producer_service.py         # 生产者服务（已废弃）⚠️
│
├── utils/                          # 工具类
│   ├── __init__.py
│   ├── logger.py                   # 日志工具
│   └── platform_adapter.py         # 平台适配
│
├── tests/                          # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api_server.py
│   ├── test_integration.py
│   ├── test_producer_service.py
│   └── README.md                   # 测试说明
│
├── docs/                           # 文档 ⭐ 整合
│   ├── ARCHITECTURE.md             # 架构设计文档
│   ├── AT_SPI_GUIDE.md             # AT-SPI使用指南
│   └── MESSAGE_TYPES.md            # 消息类型说明（v2.0）
│
├── data/                           # 数据文件
├── media/                          # 媒体文件（自动创建）
├── logs/                           # 日志文件（自动创建）
└── static/                         # 静态文件
```

**详细说明**: [DIRECTORY_STRUCTURE_V2.md](DIRECTORY_STRUCTURE_V2.md)

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

### 消息提取模块 (core/extractor/)

消息提取和处理模块，支持通用消息提取（视觉方案）。

| 模块 | 说明 | 特性 | 状态 |
|------|------|------|------|
| `message_extractor.py` | 通用消息提取器 | 点击消息判断类型 | ✅ 稳定 |
| `models.py` | 消息数据模型 | SSE JSONL 格式 | ✅ 稳定 |

**导入路径：**
```python
from core.extractor import UniversalMessageExtractor, MessageType, ExtractedMessage
```

### Detector 模块 (core/detector/)

视觉检测模块，支持图像变化检测和消息气泡检测。

| 模块 | 说明 | 用途 | 状态 |
|------|------|------|------|
| `change_detector.py` | 变化检测器 | 区分图片和视频 | ✅ 稳定 ⭐v2.1 |
| `detector.py` | 气泡检测器 | 检测消息气泡边界 | ✅ 稳定 ⭐v2.1 |
| `visual_monitor.py` | 视觉监控器 | 窗口截图和定位 | ✅ 稳定 ⭐v2.1 |
| `classifier.py` | 视觉分类器 | 分类消息类型 | ⚠️ 已废弃 |

**导入路径：**
```python
from core.detector.change_detector import ChangeDetector      # 图像变化检测
from core.detector.detector import BubbleDetector             # 气泡检测
from core.detector.detector import BoundaryDetector          # 边界扩展
from core.detector.visual_monitor import VisualMonitor        # 窗口监控
```

**注意**：v2.1 修复了类名冲突，`detector.py` 中的 `ChangeDetector` 已重命名为 `BubbleDetector`。

消息生产者模块，负责任务编排和队列管理。

| 模块 | 说明 | 方案 | 状态 |
|------|------|------|------|
| `hybrid_producer.py` | 混合生产者 | AT-SPI + 视觉 | ✅ 推荐 |
| `consumer.py` | 消息消费者 | Agent消费 | ✅ 稳定 |

**导入路径：**
```python
from core.producer.hybrid_producer import HybridProducer, ProductionMode
from core.producer.consumer import AgentConsumer
```

## 配置说明

### config/config.yaml

主要配置项：

```yaml
wechat:
  instance_id: default
  group_name: "测试群"

monitor:
  screenshot_interval: 1
  check_interval: 0.5

redis:
  host: localhost
  port: 6379
  db: 0

# 通用消息提取配置
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

### 3. 使用代码

**配置导入：**
```python
# 推荐方式
from config.config import config
# 或
from config import config
```

**使用 AT-SPI 观察者：**
```python
from core.atspi.observer import ATSPIObserver

observer = ATSPIObserver(
    enable_universal_extraction=True,
    save_dir="/host/data"
)

if observer.initialize():
    observer.start_monitoring(interval=0.5)
```

**使用混合生产者：**
```python
from core.producer.hybrid_producer import HybridProducer, ProductionMode
from config import config

producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.HYBRID
)

if producer.initialize():
    producer.start()
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| noVNC | http://localhost:6080 | Web 界面 |
| API 文档 | http://localhost:8000/docs | Swagger |
| SSE 流 | http://localhost:8000/api/stream/messages | 消息流 |
| 健康检查 | http://localhost:8000/health | 健康状态 |

## 消息类型说明

### 支持的消息类型（3种）

| 类型 | 说明 | SSE推送 | 保存位置 |
|------|------|---------|----------|
| **text** | 文本消息 | ✅ 是 | 不保存 |
| **photo** | 图片消息 | ✅ 是 | `/host/data/photos/` |
| **video** | 视频消息 | ✅ 是 | `/host/data/videos/` |

### 其他类型（不推送SSE）

| 类型 | 说明 | SSE推送 | 保存位置 |
|------|------|---------|----------|
| **file** | 文件 | ❌ 否 | `/host/data/others/file_*.json` |
| **link** | 链接 | ❌ 否 | `/host/data/others/link_*.json` |
| **其他** | 表情包等 | ❌ 否 | `/host/data/others/other_*.json` |

**详细说明**: [MESSAGE_TYPES.md](docs/MESSAGE_TYPES.md)

## 通用消息提取

### 工作流程

```
1. 检测新消息（AT-SPI观察者）
   ↓
2. 点击消息（所有消息）
   ↓
3. 检测是否唤起新窗口
   ├─ 否 → 文本消息 (text) → 推送SSE
   └─ 是 → 继续判断
           ↓
       获取窗口标题
           ↓
       ├─ "Photos and Videos" → 图片/视频 (photo/video) → 推送SSE
       ├─ "File Transfer" → 保存到物理机 → 不推送SSE
       ├─ "Browser" → 保存到物理机 → 不推送SSE
       └─ 其他 → 保存到物理机 → 不推送SSE
```

### 使用示例

```python
from core.extractor import UniversalMessageExtractor

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
    else:
        # 其他类型已保存到物理机
        print("其他类型已保存到物理机")
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
data: {"id":"msg_20250114_143022_001","type":"text","sender":"张三","content":{"text":"hello"},"group_name":"测试群聊"}

// 图片消息
data: {"id":"msg_20250114_143025_002","type":"photo","sender":"李四","content":{"high_res_media_path":"/host/data/photos/photo.png"},"group_name":"测试群聊"}

// 视频消息
data: {"id":"msg_20250114_143030_003","type":"video","sender":"王五","content":{"high_res_media_path":"/host/data/videos/video.mp4"},"group_name":"测试群聊"}
```

## API 接口

### SSE 消息流

```bash
curl -N http://localhost:8000/api/stream/messages
```

### 健康检查

```bash
curl http://localhost:8000/health
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
pytest services/wechat_sandbox/tests/test_producer_service.py -v

# 查看覆盖率
pytest --cov=services.wechat_sandbox services/wechat_sandbox/tests/
```

### 测试 AT-SPI

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 测试 AT-SPI 观察者
python3 -c "
import sys
sys.path.insert(0, '/app')
from core.atspi.observer import ATSPIObserver
observer = ATSPIObserver()
print(observer.initialize())
"
```

## 故障排查

### AT-SPI 相关问题

**问题: AT-SPI 找不到微信窗口**
```bash
# 检查环境变量
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"

# 检查 AT-SPI 进程
docker exec -it wechat_sandbox_test ps aux | grep at-spi
```

### 通用消息提取问题

**问题: 点击操作失败**
```bash
# 检查 xdotool
docker exec -it wechat_sandbox_test which xdotool

# 检查文件保存
docker exec -it wechat_sandbox_test ls -la /host/data
```

## 相关文档

### 核心文档
- [目录结构详细说明](DIRECTORY_STRUCTURE_V2.md) ⭐ 最新
- [消息类型说明](docs/MESSAGE_TYPES.md) ⭐ v2.0
- [AT-SPI使用指南](docs/AT_SPI_GUIDE.md) ⭐ 整合
- [架构设计文档](docs/ARCHITECTURE.md)
- [变更日志](CHANGELOG_v2.0.md) ⭐ v2.0

### 项目文档
- [快速开始](QUICKSTART.md)
- [Docker 主文档](../../docker/README.md)

## 版本历史

### 2025-01-14 (v2.1) ⭐ 最新
- ✅ **修复依赖问题**
  - 修复 `detector/` 模块的类名冲突（ChangeDetector → BubbleDetector）
  - 修复文档中的错误导入路径（`core.message` → `core.extractor`）
  - 标记废弃文件（`services/producer_service.py`, `core/extractor/extractor.py`）
- ✅ **扩展 detector/ 模块功能**
  - `change_detector.py` 新增 `detect_image_change()` 方法（区分图片/视频）
  - `visual_monitor.py` 新增 `capture_window_area()` 方法（窗口区域截图）
- ✅ **代码复用优化**
  - `message_extractor.py` 复用 `detector/` 模块，删除重复代码
  - 删除冗余的 `producer/visual_*.py` 文件

### 2025-01-14 (v2.0)
- ⭐ **目录结构重整**
  - 整合消息提取模块（message → extractor）
  - 创建独立配置目录（config/）
  - 整合文档到docs/
  - 删除旧实现和未使用模块
- ⭐ **简化消息类型**
  - 仅支持3种类型：text、photo、video
  - 其他类型直接保存到物理机
- ⭐ **更新导入路径**
  - `core.message` → `core.extractor`
  - `utils.config` → `config.config`

### 2025-01-12 (v1.x)
- 实现通用消息提取
- 实现点击消息判断类型的逻辑
- 支持根据窗口标题自动分类

### 早期版本
- 实现双生产者架构
- 实现 SSE 推送
- 添加 AT-SPI 混合方案支持

## 许可证

本项目遵循项目主许可证。
