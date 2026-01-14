# Core 模块

微信沙盒的核心业务逻辑模块，负责消息采集、提取和生产协调。

## 📂 目录结构

```
core/
├── atspi/                # AT-SPI UI 控件监听（主方案）
├── extractor/            # 消息内容提取器
├── producer/             # 消息生产者（协调层）
├── detector/             # 视觉检测（兜底方案）
└── __init__.py           # 模块导出
```

---

## 🎯 模块概览

### 1. AT-SPI 模块 (`atspi/`)

**职责**：通过 AT-SPI 辅助功能框架监听微信 UI 控件树变化

**优势**：
- ✅ 快速、稳定、准确
- ✅ 资源占用少
- ✅ 不依赖界面布局

**文件说明**：
- `observer.py` - AT-SPI 观察者（核心监听逻辑）
- `chat_listener.py` - 聊天窗口事件监听
- `global_listener.py` - 全局聊天事件监听

**核心类**：
```python
from core.atspi.observer import ATSPIObserver, ATSPIMessage

# 初始化观察者
observer = ATSPIObserver(
    enable_universal_extraction=True,
    save_dir="/host/data"
)

# 初始化
if observer.initialize():
    # 添加消息回调
    def on_message(message: ATSPIMessage):
        print(f"[{message.sender}] {message.content}")

    observer.add_callback(on_message)

    # 启动监听
    observer.start_monitoring(interval=0.5)
```

---

### 2. 提取器模块 (`extractor/`)

**职责**：从 AT-SPI 控件或视觉截图中提取消息内容

**功能**：
- 支持所有消息类型（文本、图片、视频、文件等）
- 自动判断消息类型
- 点击消息并提取完整内容
- 自动保存媒体文件到物理机

**文件说明**：
- `message_extractor.py` - 通用消息提取器（主要实现）
- `models.py` - 消息数据模型（MessageType、ExtractedMessage）
- `text_extractor.py` - 文本内容提取器
- `extractor.py` - 提取器基类和工具函数

**核心类**：
```python
from core.extractor import UniversalMessageExtractor, MessageType

# 初始化提取器
extractor = UniversalMessageExtractor(save_dir="/host/data")

# 提取消息
message = extractor.extract_message(atspi_element)

# 消息类型
print(message.type)  # MessageType.TEXT
print(message.sender)
print(message.content)
```

**消息类型枚举**：
- `MessageType.TEXT` - 文本消息
- `MessageType.PHOTO` - 图片消息（高清）
- `MessageType.VIDEO` - 视频消息
- `MessageType.FILE` - 文件消息
- `MessageType.LINK` - 链接消息
- `MessageType.OTHER` - 其他类型

---

### 3. 生产者模块 (`producer/`)

**职责**：消息生产协调，整合 AT-SPI 和视觉方案

**架构**：
```
┌─────────────────────────────────────────────────────┐
│              HybridProducer                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐      ┌──────────────────┐        │
│  │ AT-SPI       │──OK──→│  精确消息队列    │        │
│  │ Observer     │      │  (高效)          │        │
│  └──────┬───────┘      └──────────────────┘        │
│         │Failed                                 │
│         ↓                                       │
│  ┌──────────────┐      ┌──────────────────┐        │
│  │ Visual       │──────→│  原始消息队列    │        │
│  │ Observer     │      │  (兜底)          │        │
│  └──────┬───────┘      └──────────────────┘        │
│         │                                           │
│         ↓                                           │
│  ┌──────────────┐                                  │
│  │ Visual       │──────→│  精确消息队列    │        │
│  │ Content      │      └──────────────────┘        │
│  │ Fetcher      │                                   │
│  └──────────────┘                                   │
└─────────────────────────────────────────────────────┘
```

**文件说明**：
- `hybrid_producer.py` - 混合生产者（主协调器）
- `consumer.py` - Agent 消费者（转发消息给 Orchestrator）
- `atspi_observer.py` - AT-SPI 观察者（已废弃，功能移至 atspi/）
- `chat_window_listener.py` - 聊天窗口监听（已废弃，功能移至 atspi/）
- `global_chat_listener.py` - 全局监听（已废弃，功能移至 atspi/）

**注意**：视觉兜底方案已重构为使用 `detector/` 模块，由 `extractor/` 直接调用

**核心类**：
```python
from core.producer import HybridProducer, ProductionMode
import redis

# 初始化 Redis 客户端
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 初始化混合生产者
producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.ATSPI,  # 或 HYBRID、VISUAL
    precise_queue="wechat:messages:precise",
    save_dir="/host/data"
)

# 启动生产者
producer.start()

# 获取统计信息
stats = producer.get_stats()
print(stats)
```

**生产模式**：
- `ProductionMode.ATSPI` - 纯 AT-SPI 模式（推荐）
- `ProductionMode.VISUAL` - 纯视觉模式
- `ProductionMode.HYBRID` - 混合模式（AT-SPI 失败时自动降级到视觉）

---

### 4. 检测器模块 (`detector/`)

**职责**：视觉检测技术，作为 AT-SPI 的兜底方案

**功能**：
- 屏幕截图和 ROI 管理
- 变化检测（识别新消息气泡）
- 边界检测（扩展消息区域）
- 视觉分类（判断消息类型）

**文件说明**：
- `visual_monitor.py` - 视觉监控器（截图和窗口定位）
- `change_detector.py` - 变化检测器（检测画面差异，区分图片/视频）
- `detector.py` - 气泡检测器（检测消息气泡和边界推断）
- `classifier.py` - 视觉分类器（已废弃）

**核心类**：
```python
from core.detector.visual_monitor import VisualMonitor
from core.detector.change_detector import ChangeDetector
from core.detector.detector import BubbleDetector, BoundaryDetector

# 初始化监控器
monitor = VisualMonitor()
if monitor.locate_wechat():
    screenshot = monitor.capture()

# 图像变化检测（区分图片/视频）
change_detector = ChangeDetector()
if change_detector.detect_image_change(img1, img2):
    # 画面变化，是视频
    pass
else:
    # 画面不变，是图片
    pass

# 气泡检测（旧方案，用于消息气泡定位）
bubble_detector = BubbleDetector()
if bubble_detector.detect_changes(current_frame, prev_frame):
    # 检测到变化
    bubbles = bubble_detector.detect_bubbles(current_frame)

# 边界扩展
boundary_detector = BoundaryDetector()
expanded = boundary_detector.expand_boundary(bubble_rect, image_shape)
```

**类职责说明**：
- `ChangeDetector` (change_detector.py) - 通用图像变化检测，用于区分图片和视频
- `BubbleDetector` (detector.py) - 消息气泡检测，用于检测消息气泡边界
- `BoundaryDetector` (detector.py) - 边界扩展，用于扩展气泡区域以包含头像、昵称等
- `VisualMonitor` (visual_monitor.py) - 窗口监控，用于截图和定位窗口

---

## 🚀 快速开始

### 基础用法

```python
# 方式1：使用混合生产者（推荐）
from core.producer import HybridProducer, ProductionMode
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.ATSPI
)
producer.start()

# 方式2：直接使用 AT-SPI 观察者
from core.atspi import ATSPIObserver

observer = ATSPIObserver()
if observer.initialize():
    def on_message(msg):
        print(f"[{msg.sender}] {msg.content}")

    observer.add_callback(on_message)
    observer.start_monitoring(interval=0.5)

# 方式3：使用模块导出
from core import HybridProducer, ATSPIObserver
```

### 完整示例

```python
import redis
from core.producer import HybridProducer, ProductionMode

# 1. 初始化 Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# 2. 初始化混合生产者（AT-SPI 模式）
producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.ATSPI,
    precise_queue="wechat:messages:precise",
    save_dir="/host/data"
)

# 3. 启动生产者
try:
    producer.start()
    print("✅ 混合生产者已启动")

    # 4. 运行一段时间
    import time
    time.sleep(60)

    # 5. 查看统计信息
    stats = producer.get_stats()
    print(f"📊 统计信息: {stats}")

finally:
    # 6. 停止生产者
    producer.stop()
    print("⏹️  混合生产者已停止")
```

---

## 📊 数据流

### AT-SPI 模式（推荐）

```
微信 UI 控件树
    ↓
ATSPIObserver (监听)
    ↓
ATSPIMessage (提取)
    ↓
UniversalMessageExtractor (内容提取)
    ↓
Redis Stream (精确队列)
    ↓
SSE 流 (推送给前端)
```

### 混合模式（兜底）

```
AT-SPI 失败
    ↓
VisualObserver (视觉检测)
    ↓
VisualContentFetcher (内容提取)
    ↓
Redis Stream (原始/精确队列)
    ↓
SSE 流 (推送给前端)
```

---

## 🔧 配置说明

### 环境变量

```bash
# AT-SPI 相关
export QT_ACCESSIBILITY=1
export GNOME_ACCESSIBILITY=1
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export DBUS_SESSION_BUS_ADDRESS=unix:path=/root/.cache/at-spi/bus_99

# Redis 配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# 文件保存
export SAVE_DIR=/host/data
```

### 消息队列

```python
# 原始消息队列（视觉方案使用）
RAW_QUEUE = "wechat:messages:raw"

# 精确消息队列（AT-SPI 和最终输出使用）
PRECISE_QUEUE = "wechat:messages:precise"
```

---

## 📖 相关文档

- [架构设计文档](../docs/ARCHITECTURE.md)
- [消息类型说明](../docs/MESSAGE_TYPES.md)
- [AT-SPI 使用指南](../docs/AT_SPI_GUIDE.md)
- [目录结构说明](../DIRECTORY_STRUCTURE_V2.md)

---

## ⚠️ 注意事项

### AT-SPI 模式

1. **环境变量必须设置**
   - `QT_ACCESSIBILITY=1` - 启用 Qt 辅助功能
   - `GNOME_ACCESSIBILITY=1` - 启用 GNOME 辅助功能
   - `DBUS_SESSION_BUS_ADDRESS` - D-Bus 会话地址

2. **微信必须支持 AT-SPI**
   - Linux 版微信 4.1.13+ 支持
   - 其他版本可能不支持

3. **首次使用需要验证**
   - 使用 Accerciser 查看控件树
   - 运行测试脚本验证功能

### 视觉模式

1. **依赖 ROI 配置**
   - 需要正确配置监控区域
   - 界面变化需要重新校准

2. **资源占用较高**
   - 需要持续截图
   - 图像处理消耗 CPU

### 通用建议

1. **优先使用 AT-SPI 模式**
   - 更稳定、更快速
   - 资源占用更少

2. **视觉模式仅作兜底**
   - 在 AT-SPI 不可用时使用
   - 或用于开发调试

3. **监控生产者状态**
   - 定期检查统计信息
   - 及时发现和处理异常

---

## 🧪 测试

### 单元测试

```bash
# 测试 AT-SPI 观察者
python3 -m pytest tests/test_atspi_observer.py

# 测试混合生产者
python3 -m pytest tests/test_hybrid_producer.py

# 测试消息提取器
python3 -m pytest tests/test_message_extractor.py
```

### 集成测试

```bash
# 运行 AT-SPI 测试脚本
bash docker/scripts/atspi/test_atspi_solution.sh

# 测试混合生产者
python3 -c "
from core.producer import HybridProducer, ProductionMode
import redis

producer = HybridProducer(
    redis.Redis(host='localhost', port=6379, db=0),
    mode=ProductionMode.ATSPI
)
producer.initialize()
print(producer.get_stats())
"
```

---

## 📝 版本历史

### v2.1 (2025-01-14)
- ✅ 修复 detector/ 模块的类名冲突（ChangeDetector → BubbleDetector）
- ✅ 重构 detector/__init__.py 明确各类职责
- ✅ 更新测试文件的导入路径
- ✅ 扩展 change_detector.py 添加图像变化检测
- ✅ 扩展 visual_monitor.py 添加窗口区域截图
- ✅ 消息提取器复用 detector/ 模块
- ✅ 删除冗余的 producer/visual_*.py 文件

### v2.0 (2025-01-14)
- ✅ 重构目录结构
- ✅ 整合提取器模块
- ✅ 恢复视觉兜底方案
- ✅ 更新导入路径
- ✅ 添加模块导出

### v1.0 (2025-01-10)
- ✅ 初始版本
- ✅ AT-SPI 混合方案
- ✅ 通用消息提取

---

**维护者**: Claude Code
**最后更新**: 2025-01-14
**版本**: 2.1
