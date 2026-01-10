# 技术栈文档 (LangGraph版)

## 1. 开发与运行时环境

**操作系统**：Windows

**Python**：3.12

**容器运行时**：Docker 24.0+, Docker Compose 2.20+

**版本控制**：Git

## 2. 技术栈详情

### 2.1 Agent框架与工作流编排

| 组件 | 具体技术/库 | 版本/说明 | 用途与影响 |
|------|------------|----------|----------|
| Agent编排框架 | LangGraph | 0.0.50+ | 核心组件。用于构建有状态、多参与者的Agent工作流。支持条件路由、状态持久化和检查点恢复。 |
| LangChain集成 | LangChain | 0.1.0+ | 提供与LangGraph无缝集成的工具调用、提示词管理、以及与Chroma等组件的连接器。 |
| 大模型调用 | LangChain-Community | 0.0.10+ | 通过其集成的ChatOllama等类，方便地调用本地Ollama模型。 |
| Web框架 | FastAPI | 0.104+ | 构建对外HTTP服务（Orchestrator管理API、健康检查、SSE消息流）。提供异步支持和自动API文档。 |
| 消息队列 | Redis | 7.2+ | 用于消息持久化、分发和跨工作流会话的状态管理。支持Redis Streams实现多消费者模式。 |
| 异步运行时 | asyncio | Python内置 | 处理高并发消息流和异步I/O操作。 |

### 2.2 AI与多模态核心

| 组件 | 具体技术/库 | 版本/说明 | 用途与影响 |
|------|------------|----------|----------|
| 大模型服务 | Ollama | 最新版 | 本地部署和运行 Qwen3-VL (视觉语言模型) 和 Qwen3-Embedding-4B (嵌入模型)。 |
| 意图识别模型 | Qwen3-72B / Qwen3-8B | via Ollama | 用于识别用户消息意图（任务配置、群聊监控指令、其他操作）。 |
| 视觉模型 | Qwen3-VL-8B | via Ollama | 用于理解微信截图中的图文混合内容，支持OCR、场景理解、任务识别、区域定位。 |
| 嵌入模型 | Qwen3-Embedding-4B | via Ollama | 将业务知识库文本转换为向量，存入Chroma用于RAG检索。 |
| 向量数据库 | ChromaDB | 0.4.18+ | 轻量级、嵌入式向量数据库，与LangChain生态集成度极高，支持持久化存储。 |
| 多模态处理 | PIL / OpenCV | 最新版 | 图像预处理，为Qwen3-VL模型准备截图数据。 |
| 屏幕检测 | OpenCV-Python | 4.8+ | 实现dHash算法和HSV颜色空间检测，用于识别屏幕变化和气泡。 |
| 消息分类 | numpy + PyTorch | 最新版 | 用于MessageTypeClassifier的图像特征提取和分类。 |
| RAG检索链 | LangChain Expression Language (LCEL) | - | 用于流畅地组合检索、上下文构建、提示、模型调用等步骤，构建高效的RAG流程。 |
| 意图识别 | LangChain Runnable | - | 构建用户消息意图识别链，解析任务配置和群聊监控指令。 |
| 视觉定位 | LangChain Runnable | - | 构建微信界面区域定位链，识别目标群聊、消息发送/接收区域。 |
| Agent决策 | LangGraph Agent Node | - | 核心决策节点，根据消息内容自主决定后续操作（写日报、更新台账、保存消息等）。 |

### 2.3 微信沙盒与自动化

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 基础镜像 | jlesage/baseimage-gui | debian-11 | 为Docker容器提供轻量级GUI和VNC/noVNC支持。 |
| 虚拟显示 | Xvfb | - | 在容器内提供虚拟显示服务器，支持headless模式。 |
| 桌面环境 | Fluxbox | - | 轻量级窗口管理器，为Linux微信提供桌面环境。 |
| 桌面自动化 | PyAutoGUI | 0.9+ | 在沙盒容器内部进行模拟操作（点击、滚动等）。 |
| 图像处理 | OpenCV-Python | 4.8+ | 图像匹配、模板匹配、ROI区域检测。 |
| 生产者服务 | FastAPI + SSE | - | 容器内服务，用于流式输出消息和提供API接口。 |
| VNC服务 | noVNC + x11vnc | 最新版 | noVNC 提供浏览器远程访问，x11vnc 提供 VNC 客户端访问。 |
| 屏幕变化检测 | 自定义ChangeDetector | - | 使用dHash算法和HSV颜色空间检测屏幕变化。 |
| 消息类型分类 | 自定义MessageTypeClassifier | - | 基于图像特征识别消息类型（文本、图片、链接等）。 |

### 2.4 数据、配置与存储

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 数据验证与配置 | Pydantic | 2.5+ | 用于定义严格的数据模型、配置管理和API请求/响应验证。 |
| 配置管理 | pydantic-settings | 2.1+ | 多源配置管理（YAML + 环境变量）。 |
| Excel操作 | openpyxl | 3.1+ | 读写和更新Excel台账。 |
| Word操作 | python-docx | 1.1+ | 生成Word文档。 |
| 模板引擎 | Jinja2 | 3.1+ | 报告模板渲染。 |
| 容器控制 | Docker SDK for Python | 7.0+ | 控制微信沙盒容器生命周期。 |
| Redis客户端 | redis-py | 5.0+ | 连接Redis进行消息队列操作。 |

### 2.5 Web UI 与用户交互

#### 2.5.1 对话式Web UI（面向用户）

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 前端框架 | React | 18.3+ | 构建对话式Web UI界面，提供简洁的用户交互体验。 |
| 构建工具 | Vite | 5.4+ | 快速开发和构建React应用。 |
| 语言 | TypeScript | 5.5+ | 类型安全的前端开发。 |
| 路由 | React Router | 6.26+ | 单页应用路由管理（对话页面、404页面）。 |
| 状态管理 | Zustand | 4.5+ | 轻量级状态管理，管理对话消息、任务状态。 |
| UI组件库 | shadcn/ui | latest | 基于Radix UI的高质量组件库，快速构建美观界面。 |
| 样式方案 | Tailwind CSS | 3.4+ | 实用优先的CSS框架，快速样式开发。 |
| 实时通信 | WebSocket | - | 与Orchestrator后端建立WebSocket连接，实现流式对话交互。 |
| HTTP客户端 | Axios / Fetch | - | 发送HTTP请求到Orchestrator和沙盒API。 |
| 消息渲染 | react-markdown | 9.0+ | 渲染AI返回的Markdown格式消息。 |
| 图标库 | lucide-react | latest | 美观的图标组件。 |

#### 2.5.2 系统管理界面（面向管理员）

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 仪表盘 | React + shadcn/ui | - | 显示系统概览、沙盒状态、Agent状态、工作流状态。 |
| 沙盒监控 | React + WebSocket | - | 实时监控微信沙盒运行状态、资源使用情况。 |
| Agent监控 | React + WebSocket | - | 实时监控AI Agent决策过程、工作流执行状态。 |
| 工作流监控 | React + Recharts | - | 可视化展示LangGraph工作流执行路径、节点状态。 |
| 实例列表 | React Table | - | 管理多实例沙盒，支持启动、停止、重启操作。 |
| 系统指标 | Recharts | 2.12+ | 图表展示CPU、内存、网络、磁盘使用情况。 |
| 日志查看 | React + VirtualList | - | 实时查看系统日志、工作流日志，支持过滤和搜索。 |
| VNC集成 | noVNC | 最新版 | 在管理界面中嵌入VNC客户端，远程访问微信沙盒。 |
| 实时更新 | WebSocket | - | 推送式实时更新，无需轮询。 |

#### 2.5.3 通信协议

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 意图反馈 | WebSocket | - | 接收AI对用户消息的意图识别结果，确认任务配置和群聊监控设置。 |
| 沙盒登录引导 | WebSocket | - | 当需要用户登录微信时，引导用户打开VNC界面进行扫码登录。 |
| 消息历史 | localStorage | - | 本地存储用户对话历史记录。 |
| 状态监控 | WebSocket | - | 实时推送服务状态、任务列表、监控群聊列表、Agent决策状态。 |
| 状态显示 | React State | - | 实时显示当前监控的群聊、任务列表、日报生成状态、Agent决策结果。 |

### 2.6 可观测性与运维

| 组件 | 具体技术/库 | 版本 | 用途说明 |
|------|------------|----------|----------|
| 结构化日志 | structlog | 23.2+ | 生成结构化日志，便于追踪LangGraph工作流的执行路径。 |
| 测试框架 | pytest | 8.0+ | 单元测试、集成测试和工作流测试。 |
| 测试报告 | pytest-html | 4.1+ | 生成HTML格式的测试报告。 |
| 数值计算 | numpy | 2.0+ | 用于视觉测试和图像数据处理。 |
| 异步测试 | pytest-asyncio | 0.23+ | 支持异步函数的测试。 |
| 进程管理 | Supervisord | - | 生产环境进程管理（可选）。 |

## 3. 项目目录结构参考

```
wechat-workflow-ai-agent/
├── README.md
├── pyproject.toml                      # Python项目依赖管理
├── requirements.txt                    # 依赖列表
├── docker-compose.yml                  # 单实例服务编排配置
├── docker-compose.multi.yml            # 多实例服务编排配置（生产环境）
├── config/
│   ├── settings.yaml                   # 主配置文件
│   └── __init__.py                     # Pydantic Settings类
├── core/                               # 核心框架与协议
│   ├── schemas.py                      # Pydantic消息/状态协议
│   ├── state.py                        # LangGraph工作流状态定义
│   ├── workflows/                      # LangGraph工作流定义
│   │   ├── __init__.py
│   │   ├── main_workflow.py            # 主协调工作流
│   │   └── nodes/                      # 工作流节点
│   │       ├── intent_recognition_node.py      # LLM意图识别节点
│   │       ├── sandbox_launcher_node.py        # 沙盒启动器节点
│   │       ├── visual_locator_node.py          # LLM视觉定位节点
│   │       ├── monitor_node.py                  # 监控节点
│   │       ├── multimodal_node.py               # 多模态分析节点
│   │       ├── agent_decision_node.py           # Agent核心决策节点
│   │       ├── document_executor_node.py        # 文档执行节点
│   │       └── exceptions.py                    # 自定义异常
│   └── exceptions.py                   # 自定义异常
├── services/
│   ├── orchestrator/                   # 协调中心FastAPI应用
│   │   ├── main.py
│   │   └── api/                        # API路由
│   └── wechat_sandbox/                 # 微信沙盒
│       ├── Dockerfile
│       ├── build/                      # 镜像构建依赖文件目录
│       │   ├── fonts-noto-cjk_20240730+repack1-1_all.deb  # Noto CJK 字体包
│       │   └── WeChatLinux_x86_64.deb  # Linux 微信客户端安装包
│       ├── api_server.py               # FastAPI API服务器
│       ├── producer_service/           # 生产者服务核心
│       │   ├── __init__.py
│       │   ├── queue_manager.py        # Redis队列管理器
│       │   ├── producer1_observer.py   # 消息观察者
│       │   └── producer2_content_fetcher.py  # 内容抓取者
│       ├── utils/                      # 工具模块
│       │   ├── classifier.py           # 消息类型分类器
│       │   └── detector.py             # 屏幕变化检测器
│       └── tests/                     # 测试文件
│           ├── test_queue_manager.py
│           └── test_producer_service.py
├── frontend/                           # React前端应用
│   ├── package.json                    # 依赖管理
│   ├── tsconfig.json                   # TypeScript配置
│   ├── vite.config.ts                  # Vite构建配置
│   ├── index.html                      # HTML入口
│   ├── src/
│   │   ├── main.tsx                    # 应用入口
│   │   ├── App.tsx                     # 根组件
│   │   ├── assets/                     # 静态资源
│   │   │   ├── styles/
│   │   │   └── images/
│   │   ├── router/                     # 路由配置
│   │   ├── layouts/                    # 布局组件
│   │   │   ├── MainLayout.tsx
│   │   │   └── AdminLayout.tsx
│   │   ├── pages/                      # 页面组件
│   │   │   ├── chat/                   # 对话式Web UI（面向用户）
│   │   │   │   ├── ChatPage.tsx
│   │   │   │   ├── components/
│   │   │   │   │   ├── ChatContainer.tsx
│   │   │   │   │   ├── MessageList.tsx
│   │   │   │   │   ├── MessageInput.tsx
│   │   │   │   │   ├── TaskStatusCard.tsx
│   │   │   │   │   └── AgentDecisionDisplay.tsx
│   │   │   │   └── hooks/
│   │   │   │       ├── useWebSocket.ts
│   │   │   │       └── useChatMessages.ts
│   │   │   ├── admin/                  # 系统管理界面（面向管理员）
│   │   │   │   ├── AdminPage.tsx
│   │   │   │   ├── components/
│   │   │   │   │   ├── Dashboard.tsx
│   │   │   │   │   ├── SandboxMonitor.tsx
│   │   │   │   │   ├── AgentMonitor.tsx
│   │   │   │   │   ├── WorkflowMonitor.tsx
│   │   │   │   │   ├── InstanceList.tsx
│   │   │   │   │   ├── SystemMetrics.tsx
│   │   │   │   │   └── LogViewer.tsx
│   │   │   │   └── hooks/
│   │   │   │       ├── useSandboxStatus.ts
│   │   │   │       ├── useAgentStatus.ts
│   │   │   │       └── useSystemMetrics.ts
│   │   │   └── NotFound.tsx
│   │   ├── components/                 # 共享组件
│   │   │   ├── common/
│   │   │   └── charts/
│   │   ├── services/                   # API服务
│   │   │   ├── api.ts
│   │   │   ├── orchestrator.ts
│   │   │   ├── sandbox.ts
│   │   │   └── workflow.ts
│   │   ├── types/                      # TypeScript类型定义
│   │   ├── store/                      # 状态管理
│   │   ├── utils/                      # 工具函数
│   │   └── constants/                  # 常量
│   ├── public/                        # 公共静态文件
│   ├── Dockerfile                      # 前端Docker镜像
│   └── nginx.conf                      # Nginx配置（生产环境）
├── agents/                             # 对外服务或重型独立Agent
│   ├── monitor_agent.py                # 管理沙盒，将数据触发至工作流
│   └── __init__.py
├── knowledge_base/                     # 知识库管理
│   ├── vector_store.py                 # Chroma向量库封装
│   ├── embeddings.py                   # Qwen3-Embedding封装
│   └── docs/                           # 存放知识库源文件
├── intent_recognition/                 # LLM意图识别模块
│   ├── chains.py                       # 意图识别链
│   └── prompts.py                      # 意图识别提示词
├── visual_locator/                     # LLM视觉定位模块
│   ├── chains.py                       # 视觉定位链
│   └── prompts.py                      # 视觉定位提示词
├── agent_decision/                     # Agent决策模块
│   ├── chains.py                       # Agent决策链
│   └── prompts.py                      # Agent决策提示词
├── tools/                              # LangGraph工具定义
│   ├── excel_tool.py                   # 更新Excel工具
│   ├── word_tool.py                    # 生成报告工具
│   └── __init__.py
├── scripts/                            # 部署、知识库初始化脚本
├── tests/                              # 全局测试
│   ├── unit/                           # 单元测试
│   ├── integration/                    # 集成测试
│   └── workflows/                      # 工作流测试
├── data/                               # 数据目录
│   ├── chroma_db/                      # Chroma向量数据库
│   ├── wechat_profile/                 # 微信用户数据
│   └── output/                         # 输出文件
└── docs/
    ├── ARCHITECTURE.md
    └── TECHSTACK.md
```

## 4. 关键配置示例 (config/settings.yaml)

```yaml
project:
  name: "wechat-workflow-agent"
  env: "development"

langgraph:
  # LangGraph工作流状态存储后端（示例用Redis）
  state_store: "redis://localhost:6379/0"
  # 工作流检查点配置
  checkpoint_enabled: true

# AI模型服务配置
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"        # 多模态模型（视觉理解、区域定位）
    embedding_model: "qwen3-embedding-4b"    # 嵌入模型
    intent_model: "qwen3-72b:latest"          # 意图识别模型
    decision_model: "qwen3-72b:latest"        # Agent决策模型
  chat_model: "qwen3-72b:latest"              # 对话模型（用于用户交互）

# LLM意图识别配置
intent_recognition:
  enabled: true
  temperature: 0.1                            # 低温度保证意图识别准确性
  max_tokens: 100                            # 限制输出长度
  confidence_threshold: 0.8                  # 置信度阈值

# LLM视觉定位配置
visual_locator:
  enabled: true
  temperature: 0.1                            # 低温度保证定位准确性
  max_tokens: 200                            # 限制输出长度
  confidence_threshold: 0.7                  # 置信度阈值

# Agent决策配置
agent_decision:
  enabled: true
  temperature: 0.3                            # 适中温度平衡创造性和准确性
  max_tokens: 300                            # 限制输出长度
  action_types:                               # 支持的操作类型
    - "write_report"                          # 写日报
    - "update_ledger"                         # 更新台账
    - "save_message"                          # 保存消息
    - "continue"                              # 继续监控

# 向量数据库与知识库配置
vector_store:
  type: "chroma"
  persist_directory: "./data/chroma_db"      # Chroma持久化路径
  collection_name: "work_knowledge_base"

# 用户管理配置（阶段三启用）
user_management:
  enabled: false
  secret_key: "${JWT_SECRET_KEY}"             # JWT密钥
  token_expire_hours: 24                      # Token过期时间

# 任务配置
tasks:
  storage_backend: "redis"                    # 任务存储后端：redis/memory
  redis_key_prefix: "tasks:"                  # 任务Redis键前缀

# 监控群聊配置
monitored_groups:
  storage_backend: "redis"                    # 监控群聊存储后端
  redis_key_prefix: "monitored_groups:"      # 监控群聊Redis键前缀
  default_groups: []                           # 默认监控的群聊列表

# 微信沙盒配置
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  producer_service_url: "http://localhost:8000"
  data_volume: "./data/wechat_profile"
  vnc_password: "vnc123"                      # VNC密码

# 多实例配置（生产环境）
multi_instance:
  enabled: false
  instances:
    - id: 1
      api_port: 8001
      novnc_port: 6081
      vnc_port: 5901
      user_id: null                           # 阶段三：绑定用户ID
    - id: 2
      api_port: 8002
      novnc_port: 6082
      vnc_port: 5902
      user_id: null
    - id: 3
      api_port: 8003
      novnc_port: 6083
      vnc_port: 5903
      user_id: null

# 文档与工具配置
tools:
  excel_template_path: "./templates/task_log.xlsx"
  report_template_path: "./templates/daily_report.j2"
  output_dir: "./output"

# 基础设施
redis:
  host: "localhost"
  port: 6379
  db: 0
  # 可选：用于跨工作流锁的专用DB
  lock_db: 1

# 屏幕检测配置
screen_detection:
  change_threshold: 0.05                      # dHash变化阈值
  bubble_detection: true                      # 是否启用气泡检测
  hsv_color_space: true                       # 是否使用HSV颜色空间

# 消息分类配置
message_classification:
  model_type: "simple"                        # 分类模型类型
  confidence_threshold: 0.8                  # 置信度阈值

# 对话式Web UI配置
chat_ui:
  max_history_messages: 50                     # 最大历史消息数
  stream_response: true                       # 是否启用流式响应
  typing_simulation: true                      # 是否模拟打字效果
```

## 5. 核心组件初始化代码示例

### 5.1 初始化Chroma向量库与嵌入模型

```python
# knowledge_base/vector_store.py
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from config.settings import settings

def get_vector_store():
    """获取或创建Chroma向量存储实例"""
    embeddings = OllamaEmbeddings(
        model=settings.ai.ollama.embedding_model,
        base_url=settings.ai.ollama.base_url
    )
    
    vector_store = Chroma(
        persist_directory=settings.vector_store.persist_directory,
        embedding_function=embeddings,
        collection_name=settings.vector_store.collection_name
    )
    return vector_store
```

### 5.2 定义LangGraph工作流状态

```python
# core/state.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    """LangGraph工作流的状态定义，贯穿整个处理流程。"""
    # 输入
    user_message: Optional[str]               # 用户输入消息
    raw_message: Optional[dict]                # 来自微信的原始消息
    # 处理中间状态
    intent: Optional[Literal["task_config", "monitor_group", "other"]]  # 用户意图
    task_config: Optional[dict]                # 任务配置解析结果
    group_name: Optional[str]                  # 目标群聊名称
    visual_regions: Optional[dict]             # 视觉定位结果（目标群聊、消息发送/接收区域）
    multimodal_analysis: Optional[dict]        # 多模态分析结果
    action_type: Optional[Literal["write_report", "update_ledger", "save_message", "continue"]]  # Agent决策的操作类型
    task_status: Optional[str]                 # 任务状态
    # 输出
    document_updates: List[dict]              # 需要执行的文档更新指令
    # 用于串联对话的消息记录
    messages: Annotated[list, add_messages]
```

### 5.3 构建主工作流示例

```python
# core/workflows/main_workflow.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    intent_recognition_node,
    sandbox_launcher_node,
    visual_locator_node,
    monitor_node,
    multimodal_node,
    agent_decision_node,
    document_executor_node
)

def create_workflow():
    """创建并编译主处理工作流"""
    workflow = StateGraph(AgentState)
    
    # 添加节点（对应AI Agent核心功能）
    workflow.add_node("intent_recognition", intent_recognition_node.process)
    workflow.add_node("sandbox_launcher", sandbox_launcher_node.launch)
    workflow.add_node("visual_locator", visual_locator_node.locate)
    workflow.add_node("monitor", monitor_node.process)
    workflow.add_node("multimodal", multimodal_node.analyze)
    workflow.add_node("agent_decision", agent_decision_node.decide)
    workflow.add_node("document_executor", document_executor_node.execute)
    
    # 设置边（定义流程逻辑）
    workflow.set_entry_point("intent_recognition")
    
    # 意图识别后的条件路由
    workflow.add_conditional_edges(
        "intent_recognition",
        lambda state: "task_config" if state.get("intent") == "task_config" else "monitor_group",
        {
            "task_config": END,
            "monitor_group": "sandbox_launcher"
        }
    )
    
    workflow.add_edge("sandbox_launcher", "visual_locator")
    workflow.add_edge("visual_locator", "monitor")
    workflow.add_edge("monitor", "multimodal")
    workflow.add_edge("multimodal", "agent_decision")
    
    # Agent决策后的条件路由
    workflow.add_conditional_edges(
        "agent_decision",
        lambda state: state.get("action_type", "continue"),
        {
            "write_report": "document_executor",
            "update_ledger": "document_executor",
            "save_message": END,
            "continue": END
        }
    )
    
    workflow.add_edge("document_executor", END)
    
    return workflow.compile(checkpointer=RedisCheckpointSaver(redis_conn))
```

### 5.4 LLM意图识别初始化

```python
# intent_recognition/chains.py
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from config.settings import settings

def create_intent_recognition_chain():
    """创建LLM意图识别链"""
    llm = ChatOllama(
        model=settings.ai.ollama.intent_model,
        base_url=settings.ai.ollama.base_url,
        temperature=settings.intent_recognition.temperature,
        num_predict=settings.intent_recognition.max_tokens
    )
    
    prompt = ChatPromptTemplate.from_template("""
你是一个意图识别助手，负责识别用户消息的意图。

用户消息：{user_message}

请判断用户意图并返回以下三种之一：
- task_config：用户发送任务配置消息（如：工作1（地点A）人员1，人员2）
- monitor_group：用户发送群聊监控指令（如：监控微信群聊SSS）
- other：其他意图

仅返回意图类型，不要其他内容。
""")
    
    chain = prompt | llm
    return chain
```

### 5.5 LLM视觉定位初始化

```python
# visual_locator/chains.py
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from config.settings import settings

def create_visual_locator_chain():
    """创建LLM视觉定位链"""
    llm = ChatOllama(
        model=settings.ai.ollama.vision_model,
        base_url=settings.ai.ollama.base_url,
        temperature=settings.visual_locator.temperature,
        num_predict=settings.visual_locator.max_tokens
    )
    
    prompt = ChatPromptTemplate.from_template("""
你是一个视觉定位助手，负责在微信界面中定位特定区域。

目标群聊名称：{group_name}

请识别并返回以下区域坐标（像素坐标，格式为[x1, y1, x2, y2]）：
1. target_group：目标群聊区域
2. message_send_area：消息发送区域
3. message_receive_area：消息接收区域

请返回JSON格式的坐标信息。
""")
    
    chain = prompt | llm
    return chain
```

### 5.6 Agent决策初始化

```python
# agent_decision/chains.py
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from config.settings import settings

def create_agent_decision_chain():
    """创建Agent决策链"""
    llm = ChatOllama(
        model=settings.ai.ollama.decision_model,
        base_url=settings.ai.ollama.base_url,
        temperature=settings.agent_decision.temperature,
        num_predict=settings.agent_decision.max_tokens
    )
    
    prompt = ChatPromptTemplate.from_template("""
你是一个AI Agent，负责根据群聊消息内容自主决策后续操作。

群聊消息：{message_content}
上下文：{context}

请根据消息内容决定执行以下哪种操作：
- write_report：生成日报
- update_ledger：更新Excel台账
- save_message：保存消息到数据库
- continue：继续监控，不执行操作

返回格式：{"action_type": "操作类型", "reason": "决策原因"}
""")
    
    chain = prompt | llm
    return chain
```

### 5.7 API服务器生命周期管理

```python
# services/wechat_sandbox/api_server.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue_manager, producer1, producer2
    try:
        logger.info("Starting Producer Service...")
        queue_manager = RedisQueueManager()
        producer1 = Producer1Observer(queue_manager)
        producer2 = Producer2ContentFetcher(queue_manager)
        producer1.start()
        producer2.start()
        logger.info("Producer Service started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start Producer Service: {e}")
        raise
    finally:
        logger.info("Shutting down Producer Service...")
        if producer1:
            producer1.stop()
        if producer2:
            producer2.stop()
        logger.info("Producer Service stopped")

app = FastAPI(lifespan=lifespan)
```

## 6. 部署与运行说明

### 6.1 开发环境启动

#### 启动基础设施

```bash
# 单实例部署
docker-compose up -d redis ollama

# 多实例部署（生产环境）
docker-compose -f docker-compose.multi.yml up -d
```

#### 拉取模型

```bash
# 拉取视觉模型
docker exec -it ollama ollama pull qwen3-vl-8b:latest

# 拉取嵌入模型
docker exec -it ollama ollama pull qwen3-embedding-4b

# 拉取意图识别和Agent决策模型
docker exec -it ollama ollama pull qwen3-72b:latest
```

#### 初始化知识库

运行 `scripts/init_knowledge_base.py`，将业务文档灌入Chroma。

#### 构建并启动微信沙盒

```bash
# 单实例
docker-compose up -d wechat-sandbox

# 多实例
docker-compose -f docker-compose.multi.yml up -d
```

#### 启动Orchestrator服务

```bash
uvicorn services.orchestrator.main:app --reload
```

#### 触发工作流

Monitor Agent 接收到新消息后，将调用 `workflow.invoke()` 启动LangGraph处理流程。

### 6.2 生产部署建议

#### 容器化

将 Orchestrator、Monitor Agent、知识库服务等分别容器化。

#### Ollama管理

确保Ollama服务常驻，并监控GPU/内存使用。

#### Chroma持久化

确保 `persist_directory` 使用卷挂载，数据持久化。

#### 状态存储

为LangGraph配置高可用的Redis实例作为状态存储后端。

#### 多实例部署

使用 `docker-compose.multi.yml` 启动多个微信实例，支持多用户/多群组场景。

#### 监控与日志

- 使用 structlog 生成结构化日志
- 配置日志轮转和远程日志收集
- 监控容器状态、服务健康度和队列长度

#### 安全配置

- 设置强密码（VNC、Redis等）
- 使用环境变量管理敏感信息
- 配置防火墙和网络隔离
- 启用HTTPS（生产环境）

### 6.3 镜像构建与推送

#### 镜像构建说明

微信沙盒提供两个 Dockerfile：
- `Dockerfile`：生产环境基础镜像（分层设计）
- `Dockerfile.test`：测试环境镜像（继承自生产镜像，添加 FastAPI 支持）

构建依赖文件存放在 `build/` 目录中：

```
wechat_sandbox/
├── Dockerfile
├── Dockerfile.test
├── build/
│   ├── fonts-noto-cjk_20240730+repack1-1_all.deb  # Noto CJK 字体包
│   └── WeChatLinux_x86_64.deb  # Linux 微信客户端安装包
```

#### 构建生产环境基础镜像

```bash
cd services/wechat_sandbox
docker build -f Dockerfile -t wechat-sandbox:latest .
```

#### 构建测试环境镜像

```bash
cd services/wechat_sandbox
docker build -f Dockerfile.test -t wechat-sandbox-test:latest .
```

**说明**：Dockerfile.test 继承自 wechat-sandbox:latest，添加 FastAPI 支持，用于测试环境部署。

#### 推送到 GitHub Container Registry (ghcr.io)

**步骤 1：创建 GitHub Personal Access Token**

1. 访问 GitHub 设置页面：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 选择权限：`write:packages`, `read:packages`, `delete:packages`
4. 生成并复制 token（仅显示一次）

**步骤 2：登录 ghcr.io**

```bash
docker login ghcr.io
# 输入用户名：GitHub 用户名（如：lsh255）
# 输入密码：GitHub 个人访问令牌（不是 GitHub 密码）
```

**步骤 3：标记镜像**

```bash
docker tag wechat-sandbox:latest ghcr.io/lsh255/wechat-sandbox:latest
```

**步骤 4：推送镜像**

```bash
docker push ghcr.io/lsh255/wechat-sandbox:latest
```

**步骤 5：验证镜像**

```bash
# 查看本地镜像
docker images | grep wechat-sandbox

# 查看 ghcr.io 上的镜像（需登录）
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user/packages
```

#### 使用远程镜像部署

**测试环境、生产单服务、生产多服务部署**

在 docker-compose.yml 中使用 ghcr.io 上的远程镜像：

```yaml
services:
  wechat-sandbox:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox-test
    # ... 其他配置
```

多实例部署 (docker-compose.multi.yml)：

```yaml
services:
  wechat-sandbox-1:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox-instance-1
    # ... 端口映射配置
```

**优点：**
- 所有环境使用相同的镜像，确保一致性
- 无需在每台机器上重新构建
- 便于版本管理和回滚
- 减少构建时间

### 6.4 Web UI 访问

#### 测试环境

| 端口 | 服务 |
|------|------|
| 8000 | FastAPI |
| 6080 | noVNC Web 界面 |
| 5900 | VNC 客户端 |
| 6379 | Redis |

**访问地址**：
- noVNC Web 界面：http://localhost:6080/vnc.html（密码：wechat123）
- VNC 客户端：localhost:5900（密码：wechat123）
- FastAPI 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

#### 生产单实例

| 端口 | 服务 |
|------|------|
| 8000 | FastAPI |
| 6080 | noVNC |
| 5900 | VNC |
| 6379 | Redis |

**访问地址**：
- noVNC：http://localhost:6080
- VNC：localhost:5900（密码：vnc123）
- Web UI：http://localhost:8000/static/index.html

#### 生产多实例

| 端口范围 | 服务 |
|----------|------|
| 8001-8003 | FastAPI |
| 6081-6083 | noVNC |
| 5901-5903 | VNC |
| 6379 | Redis |

**访问地址**：

| 实例 | noVNC | VNC | FastAPI |
|------|-------|-----|---------|
| 1 | http://localhost:6081 | localhost:5901 | http://localhost:8001 |
| 2 | http://localhost:6082 | localhost:5902 | http://localhost:8002 |
| 3 | http://localhost:6083 | localhost:5903 | http://localhost:8003 |

VNC 密码：vnc123

## 7. 测试说明

### 7.1 测试框架

- **pytest**: 主要测试框架
- **pytest-html**: 生成HTML测试报告
- **numpy**: 用于视觉测试（创建测试图像）
- **pytest-asyncio**: 异步测试支持

### 7.2 运行测试

```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=core --cov-report=html

# 生成HTML测试报告
pytest --html=report.html --self-contained-html

# 运行特定测试文件
pytest services/wechat_sandbox/tests/test_producer_service.py
```

### 7.3 测试覆盖范围

- **单元测试**: RedisQueueManager、ChangeDetector、MessageTypeClassifier
- **集成测试**: Producer1Observer、Producer2ContentFetcher、API服务器
- **工作流测试**: LangGraph工作流节点和边逻辑

## 8. 性能指标

- 消息处理延迟: < 3秒（不含文档生成）
- 并发处理能力: 支持多个工作流并行执行
- 多实例支持: 默认支持 3 个独立微信实例
- 内存占用: Ollama 模型加载约需 8-16GB RAM
- 存储需求: ChromaDB 向量存储约 100-500MB（取决于知识库大小）
- 屏幕检测延迟: < 500ms（ChangeDetector）

## 9. 扩展方向

可以考虑添加的功能：
- 支持语音消息转文字（Whisper）
- 支持视频帧提取和分析
- 增强多群组管理（支持更多实例）
- 完善 Web UI 管理界面（用户认证、权限管理）
- 支持定时任务和提醒
- 集成企业微信 API
- 添加数据分析和可视化
- 支持 OCR 文字识别
- 增强消息搜索和过滤功能
