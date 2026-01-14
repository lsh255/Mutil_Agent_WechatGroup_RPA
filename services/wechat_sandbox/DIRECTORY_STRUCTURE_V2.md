# Wechat Sandbox 目录结构说明

## 📂 完整目录树

```
services/wechat_sandbox/
├── api/                        # FastAPI接口层
│   ├── __init__.py
│   ├── config.py              # API配置
│   ├── health.py              # 健康检查接口
│   ├── instance.py            # 实例管理接口
│   └── stream.py              # SSE流接口
│
├── config/                     # 沙盒配置管理（独立）
│   ├── __init__.py
│   ├── config.py              # 配置类
│   ├── config.yaml            # 开发环境配置
│   └── config.production.yaml # 生产环境配置
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   │
│   ├── atspi/                # AT-SPI消息监听（主方案）
│   │   ├── __init__.py
│   │   ├── observer.py        # AT-SPI观察者（主要逻辑）
│   │   ├── chat_listener.py   # 聊天窗口监听
│   │   └── global_listener.py # 全局聊天监听
│   │
│   ├── extractor/            # 消息内容提取器
│   │   ├── __init__.py
│   │   ├── message_extractor.py  # 通用消息提取器（视觉方案）
│   │   └── models.py          # 消息数据模型
│   │
│   ├── producer/             # 消息生产者（协调层）
│   │   ├── __init__.py
│   │   ├── hybrid_producer.py # 混合生产者
│   │   ├── consumer.py        # 消息消费者
│   │   ├── atspi_observer.py  # AT-SPI观察者（Producer版本）
│   │   ├── chat_window_listener.py  # 聊天窗口监听（Producer版本）
│   │   └── global_chat_listener.py  # 全局监听（Producer版本）
│   │
│   └── detector/             # 视觉检测（兜底方案）
│       ├── __init__.py
│       ├── change_detector.py # 变化检测
│       ├── classifier.py      # 视觉分类器
│       ├── detector.py        # 检测器
│       └── visual_monitor.py  # 视觉监控
│
├── services/                   # 服务层
│   ├── __init__.py
│   └── producer_service.py   # 生产者服务
│
├── utils/                      # 工具类（沙盒专用）
│   ├── __init__.py
│   ├── logger.py             # 日志工具
│   └── platform_adapter.py   # 平台适配器
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api_server.py
│   ├── test_integration.py
│   ├── test_producer_service.py
│   └── test_queue_manager.py
│
├── docs/                       # 沙盒文档（独立）
│   ├── ARCHITECTURE.md        # 架构设计文档
│   ├── DIRECTORY_STRUCTURE.md # 旧版目录结构说明
│   ├── MESSAGE_TYPES.md       # 消息类型说明（v2.0）
│   └── AT_SPI_GUIDE.md        # AT-SPI使用指南
│
├── data/                       # 数据目录（运行时）
│   └── media/                 # 媒体文件
│
├── static/                     # 静态文件
├── logs/                       # 日志目录
├── archive/                    # 归档文件
│   ├── docker-compose.wechat.yml
│   └── README.md
│
├── main.py                     # 入口文件
├── README.md                   # 项目说明
├── QUICKSTART.md              # 快速开始指南
├── RESTRUCTURE_PLAN_V2.md     # 重整计划v2.0
├── RESTRUCTURE_PLAN.md        # 原重整计划
├── BUSINESS_LOGIC_TEST.md     # 业务逻辑测试文档
└── run_tests.py               # 测试运行脚本
```

## 🎯 核心模块说明

### 1. AT-SPI模块 (`core/atspi/`)
**职责**：AT-SPI UI控件监听
- `observer.py`：AT-SPI观察者，监听UI控件树变化
- `chat_listener.py`：聊天窗口事件监听
- `global_listener.py`：全局聊天事件监听

**特点**：
- ✅ 快速、稳定、准确
- ✅ 资源占用少
- ✅ 不依赖界面布局

### 2. 提取器模块 (`core/extractor/`)
**职责**：消息内容提取
- `message_extractor.py`：通用消息提取器（视觉方案）
- `models.py`：消息数据模型（MessageType、ExtractedMessage）

**特点**：
- ✅ 支持所有消息类型
- ✅ 自动判断类型
- ⚠️ 需要点击和窗口检测

### 3. 生产者模块 (`core/producer/`)
**职责**：消息生产协调
- `hybrid_producer.py`：混合生产者（AT-SPI + 视觉兜底）
- `consumer.py`：消息消费者

**特点**：
- ✅ 自动选择最佳方案
- ✅ 故障自动切换
- ✅ 健康检查

### 4. 检测器模块 (`core/detector/`)
**职责**：视觉检测（兜底方案）
- 变化检测、视觉分类、视觉监控

**特点**：
- ⚠️ 仅在AT-SPI不可用时使用
- ⚠️ 依赖视觉技术

## 📦 配置管理

### 配置文件
```
config/
├── config.py              # 配置类
├── config.yaml            # 开发环境
└── config.production.yaml # 生产环境
```

### 使用方式
```python
# 推荐方式（相对导入）
from config.config import config

# 或
from config import config
```

## 📚 文档结构

### 核心文档
- `ARCHITECTURE.md`：架构设计文档
- `MESSAGE_TYPES.md`：消息类型说明（v2.0）
- `AT_SPI_GUIDE.md`：AT-SPI使用指南
- `DIRECTORY_STRUCTURE.md`：旧版目录结构（参考）

### 快速开始
- `README.md`：项目说明
- `QUICKSTART.md`：快速开始指南

### 其他文档
- `BUSINESS_LOGIC_TEST.md`：业务逻辑测试
- `RESTRUCTURE_PLAN_V2.md`：重整计划v2.0

## 🚀 快速导航

### 我要...

**了解架构**
→ 阅读 `docs/ARCHITECTURE.md`

**开始使用**
→ 阅读 `QUICKSTART.md`

**了解消息类型**
→ 阅读 `docs/MESSAGE_TYPES.md`

**使用AT-SPI**
→ 阅读 `docs/AT_SPI_GUIDE.md`

**调用API**
→ 查看 `api/` 目录

**扩展功能**
→ 查看 `core/` 对应模块

## 🔄 与项目其他部分的交互

### 独立性
- ✅ 沙盒拥有独立的配置管理
- ✅ 沙盒拥有独立的文档
- ✅ 沙盒可作为独立服务运行

### 接口
- 📡 **API接口**：通过 `api/` 提供REST API
- 📡 **SSE流**：通过 `/api/stream/messages` 推送消息
- 📡 **Redis**：通过Redis Stream与项目通信

### 依赖
- Python环境
- Redis服务（用于消息队列）
- Docker环境（用于容器化部署）

## 📝 重整历史

### v2.0 (2025-01-14)
- ✅ 整合提取器模块（message → extractor）
- ✅ 创建独立的config目录
- ✅ 整合文档到docs目录
- ✅ 删除旧实现和未使用模块
- ✅ 简化producer目录

### 删除的模块
- `core/classifier/`：未使用
- `core/extractor/`（旧）：与message重复
- `core/platform/`：功能简单，移到utils/
- `core/queue/`：未使用
- `core/window/`：空目录

### 删除的文件
- `core/producer/observer.py`：旧实现
- `core/producer/monitor.py`：旧实现
- `core/producer/content_fetcher.py`：旧实现
- `core/producer/photo_extractor.py`：已合并到message_extractor
- `core/producer/*.md`：旧文档，已整合到docs/

---

**版本**：v2.0
**最后更新**：2025-01-14
**维护者**：Claude Code
