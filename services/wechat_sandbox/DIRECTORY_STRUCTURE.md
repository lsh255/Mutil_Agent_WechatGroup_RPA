# wechat_sandbox 目录结构说明

## 新的目录结构

```
wechat_sandbox/
├── api/                        # FastAPI路由层
│   ├── __init__.py
│   ├── config.py              # 配置相关API
│   ├── health.py              # 健康检查
│   ├── instance.py            # 实例管理
│   └── stream.py              # SSE流接口
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   │
│   ├── atspi/                 # AT-SPI模块（新建）
│   │   ├── __init__.py
│   │   ├── observer.py        # AT-SPI观察者
│   │   ├── chat_listener.py   # 聊天窗口监听器
│   │   └── global_listener.py # 全局聊天监听器
│   │
│   ├── message/               # 消息处理模块（新建）
│   │   ├── __init__.py
│   │   ├── extractor.py       # 通用消息提取器
│   │   ├── classifier.py      # 消息分类器
│   │   └── models.py          # 消息数据模型
│   │
│   ├── window/                # 窗口管理模块（新建）
│   │   ├── __init__.py
│   │   ├── manager.py         # 窗口管理器
│   │   ├── detector.py        # 窗口检测器
│   │   └── interaction.py     # 窗口交互（点击等）
│   │
│   ├── producer/              # 生产者模块（重构）
│   │   ├── __init__.py
│   │   ├── hybrid.py          # 混合生产者
│   │   ├── consumer.py        # 消费者
│   │   ├── monitor.py         # 监控器
│   │   └── README.md          # 生产者文档
│   │
│   ├── detector/              # 视觉检测器
│   │   ├── __init__.py
│   │   ├── detector.py        # 气泡检测器
│   │   ├── visual_monitor.py  # 视觉监控
│   │   └── change_detector.py # 变化检测器
│   │
│   ├── extractor/             # 内容提取器（保留用于视觉方案）
│   │   ├── __init__.py
│   │   ├── extractor.py       # 基础提取器
│   │   └── text_extractor.py  # 文本提取器
│   │
│   ├── classifier/            # 分类器
│   │   └── classifier.py      # 消息分类器
│   │
│   ├── platform/              # 平台适配器
│   │   └── adapter.py
│   │
│   └── queue/                 # 队列管理
│       ├── __init__.py
│       └── manager.py         # 队列管理器
│
├── services/                   # 服务层
│   ├── __init__.py
│   └── producer_service.py    # 生产者服务
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── config.py              # 配置工具
│   ├── logger.py              # 日志工具
│   └── platform_adapter.py    # 平台适配工具
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api_server.py
│   ├── test_integration.py
│   ├── test_producer_service.py
│   └── test_queue_manager.py
│
├── models/                     # 数据模型（可选）
│   └── __init__.py
│
├── main.py                     # 主入口
├── run_tests.py               # 测试运行器
├── backup_start.py
└── README.md
```

## 模块职责说明

### core/atspi/ - AT-SPI模块
**职责**: 提供AT-SPI相关的所有功能
- `observer.py`: 主观察者，监听微信UI控件树变化
- `chat_listener.py`: 指定聊天窗口的监听器
- `global_listener.py`: 全局聊天监听器

**依赖**:
- `core.message.extractor`: 通用消息提取器
- `core.window.manager`: 窗口管理器

### core/message/ - 消息处理模块
**职责**: 消息的提取、分类和处理
- `extractor.py`: 通用消息提取器（点击消息判断类型）
- `classifier.py`: 消息类型分类器
- `models.py`: 消息数据模型定义

**依赖**:
- `core.window.manager`: 窗口检测和交互

### core/window/ - 窗口管理模块
**职责**: 窗口相关的所有操作
- `manager.py`: 窗口管理器（获取、关闭窗口等）
- `detector.py`: 窗口检测器（检测新窗口）
- `interaction.py`: 窗口交互（点击、截图等）

**依赖**:
- `pyatspi`: AT-SPI库
- `xdotool`: 点击工具

### core/producer/ - 生产者模块
**职责**: 消息生产和队列管理
- `hybrid.py`: 混合生产者（AT-SPI + 视觉方案）
- `consumer.py`: 消息消费者
- `monitor.py`: 生产者监控

**依赖**:
- `core.atspi.observer`: AT-SPI观察者
- `core.detector.*`: 视觉检测器
- `core.queue.manager`: 队列管理器

### core/detector/ - 视觉检测模块
**职责**: 基于视觉的消息检测
- 保留原有功能，作为AT-SPI的兜底方案

### core/extractor/ - 内容提取模块
**职责**: 基于视觉的内容提取
- 保留原有功能，用于视觉方案的内容提取

## 导入路径变更

### 旧的导入路径 → 新的导入路径

```python
# AT-SPI观察者
from core.producer.atspi_observer import ATSPIObserver
↓
from core.atspi.observer import ATSPIObserver

# 聊天窗口监听器
from core.producer.chat_window_listener import ChatWindowListener
↓
from core.atspi.chat_listener import ChatWindowListener

# 全局监听器
from core.producer.global_chat_listener import GlobalChatListener
↓
from core.atspi.global_listener import GlobalChatListener

# 消息提取器
from core.producer.photo_extractor import UniversalMessageExtractor
↓
from core.message.extractor import UniversalMessageExtractor

# 混合生产者
from core.producer.hybrid_producer import HybridProducer
↓
from core.producer.hybrid import HybridProducer
```

## 文件移动清单

### 从 core/producer/ 移动到 core/atspi/
- ✅ `atspi_observer.py` → `core/atspi/observer.py`
- ✅ `chat_window_listener.py` → `core/atspi/chat_listener.py`
- ✅ `global_chat_listener.py` → `core/atspi/global_listener.py`

### 从 core/producer/ 移动到 core/message/
- ✅ `photo_extractor.py` → `core/message/extractor.py`

### 保留在 core/producer/
- `hybrid_producer.py` → 重命名为 `hybrid.py`
- `agent_consumer.py` → 保留
- `monitor.py` → 保留
- `observer.py` → 保留（视觉方案观察者）
- `content_fetcher.py` → 保留或移动到 `core/extractor/`

## 待完成任务

1. ✅ 创建新目录结构
2. ⏳ 更新所有import语句
3. ⏳ 重命名hybrid_producer.py为hybrid.py
4. ⏳ 更新__init__.py文件
5. ⏳ 删除旧文件（或保留作为备份）
6. ⏳ 更新文档

## 迁移步骤

### 步骤1: 创建新目录结构
```bash
mkdir -p core/atspi
mkdir -p core/message
mkdir -p core/window
```

### 步骤2: 移动文件
```bash
# AT-SPI相关
cp core/producer/atspi_observer.py core/atspi/observer.py
cp core/producer/chat_window_listener.py core/atspi/chat_listener.py
cp core/producer/global_chat_listener.py core/atspi/global_listener.py

# 消息提取相关
cp core/producer/photo_extractor.py core/message/extractor.py

# 生产者重构
cp core/producer/hybrid_producer.py core/producer/hybrid.py
```

### 步骤3: 更新import语句
在所有新文件中更新import路径

### 步骤4: 更新__init__.py
确保所有新模块都有正确的__init__.py

### 步骤5: 测试
运行测试确保所有功能正常

### 步骤6: 清理
确认无问题后删除旧文件

---

**文档版本**: v1.0
**更新时间**: 2025-01-12
**维护者**: Claude Code
