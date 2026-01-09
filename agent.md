# AI 智能体系统架构文档

> 本文档为 AI 模型提供项目上下文信息，用于理解系统架构、组件职责和开发规范。

## 📋 项目简介

**项目名称**：多模态微信群自动化智能体系统

**项目定位**：基于 LangGraph 的有状态多模态 AI 智能体系统，用于监控微信工作群消息、理解图文混合内容、跟踪任务状态、自动更新台账和生成工作报告。

**核心价值**：
- 自动化处理微信群消息，减少人工干预
- 多模态理解（文本+图像）能力
- 智能任务状态跟踪和管理
- 自动化文档生成（Excel、Word）

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     微信沙盒容器 (Docker)                      │
│  ├── WeChat 客户端实例                                         │
│  ├── 生产者服务 (http://localhost:6789)                       │
│  └── noVNC 远程桌面 (http://localhost:5800)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ SSE 消息流
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  MonitorAgent (监控智能体)                     │
│  ├── Docker 容器生命周期管理                                    │
│  ├── Server-Sent Events 消息消费                              │
│  ├── 消息解析和预处理                                          │
│  └── 工作流触发                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /workflow/trigger
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator (工作流编排中心)                     │
│  ├── FastAPI Web 服务 (http://localhost:8000)                │
│  ├── LangGraph 工作流引擎                                      │
│  ├── API 请求处理和响应                                        │
│  └── 健康检查和监控                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph 工作流引擎                         │
│  ┌─────────┐    ┌──────────────┐    ┌─────────────┐         │
│  │ Monitor │ →  │  Multimodal  │ →  │ StateTracker │         │
│  │  Node   │    │     Node     │    │    Node     │         │
│  └─────────┘    └──────────────┘    └──────┬──────┘         │
│                                             │                 │
│                                   ┌─────────┴─────────┐       │
│                                   │                   │       │
│                           任务完成?  否              │ 是     │
│                                   ↓                   ↓       │
│                                 END              ┌─────────┐  │
│                                                  │Document │  │
│                                                  │  Node   │  │
│                                                  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   外部服务与基础设施                           │
│  ├── Redis (状态缓存、分布式锁)                                │
│  ├── Ollama (AI 模型服务)                                     │
│  │   ├── Qwen3-VL (视觉理解)                                  │
│  │   ├── Qwen3-Embedding (文本嵌入)                           │
│  │   └── Qwen3-Chat (对话生成)                                │
│  ├── ChromaDB (向量数据库)                                    │
│  └── 文档工具 (Word/Excel 生成)                               │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈说明

| 技术/框架 | 版本要求 | 用途 |
|----------|---------|------|
| Python | 3.12+ | 主要开发语言 |
| LangGraph | 0.0.50+ | 工作流编排框架 |
| LangChain | 0.1.0+ | AI 工具集成框架 |
| FastAPI | 0.104+ | Web API 框架 |
| Ollama | latest | 本地 AI 模型服务 |
| ChromaDB | latest | 向量数据库 |
| Redis | 7.0+ | 缓存和状态存储 |
| Docker | 20.0+ | 容器化部署 |

### AI 模型配置

```yaml
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"       # 图像理解
    embedding_model: "qwen3-embedding-4b"    # 文本嵌入
    chat_model: "qwen3-72b:latest"           # 对话生成
```

## 🔧 核心组件详解

### 1. MonitorAgent（监控智能体）

**文件路径**：`agents/monitor_agent.py`

**核心职责**：
- 管理微信沙盒 Docker 容器的启动和停止
- 订阅微信消息流（Server-Sent Events）
- 解析和验证消息格式
- 触发工作流执行

**关键方法**：
```python
class MonitorAgent:
    async def start_container()    # 启动微信沙盒容器
    async def stop_container()     # 停止容器
    async def start()              # 开始监控消息
    def stop()                     # 停止监控
    def set_message_callback()     # 设置消息回调函数
```

**端口映射**：
- `5800` → noVNC Web 界面
- `5900` → VNC 协议
- `6789` → 生产者服务 API

**使用示例**：
```python
from agents.monitor_agent import MonitorAgent

agent = MonitorAgent(orchestrator_url="http://localhost:8000")
await agent.start()
# ... 运行 ...
agent.stop()
```

### 2. Orchestrator（工作流编排中心）

**文件路径**：`services/orchestrator/main.py`

**核心职责**：
- 提供 RESTful API 接口
- 管理工作流实例和执行
- 处理并发请求和状态管理
- 返回执行结果和错误处理

**API 端点**：

| 端点 | 方法 | 功能 | 请求示例 |
|------|------|------|----------|
| `/` | GET | 服务信息 | - |
| `/health` | GET | 健康检查 | - |
| `/workflow/trigger` | POST | 触发工作流 | 见下方 |
| `/workflow/status` | GET | 查询状态 | - |

**触发工作流请求格式**：
```json
POST /workflow/trigger
{
  "sender": "张三",
  "content": "请生成本周工作周报",
  "message_type": "text",
  "group_id": "group_123",
  "timestamp": "2026-01-09T10:30:00",
  "metadata": {
    "priority": "high",
    "mentions": ["@all"]
  }
}
```

**响应格式**：
```json
{
  "success": true,
  "workflow_id": "wf_20260109_103000_abc123",
  "status": "completed",
  "result": {
    "task_status": "completed",
    "document_path": "/output/report_20260109.docx"
  }
}
```

### 3. LangGraph 工作流节点

**文件路径**：`core/workflows/`

#### 3.1 监控节点 (Monitor Node)

**文件**：`nodes/monitor_node.py`

**功能**：
- 接收原始消息
- 验证消息格式和类型
- 消息预处理（清理、标准化）
- 路由到下一个节点

**输入**：`raw_message: RawMessage`
**输出**：更新后的 `AgentState`

#### 3.2 多模态分析节点 (Multimodal Node)

**文件**：`nodes/multimodal_node.py`

**功能**：
- **文本消息**：使用 LLM 进行意图识别和任务提取
- **图片消息**：使用视觉模型（Qwen3-VL）进行图像内容理解
- **混合消息**：融合文本和图像信息进行综合分析
- **RAG 增强**：从向量数据库检索相关上下文

**处理流程**：
```
消息输入 → 判断类型 → 选择模型 → 生成分析结果 → RAG检索 → 融合结果 → 输出
```

**AI 能力**：
- 文本意图识别（任务类型、紧急程度、执行者）
- 图像内容识别（截图、文档、照片、二维码）
- 实体提取（人名、时间、地点、任务内容）
- 上下文理解（结合历史对话和知识库）

#### 3.3 状态跟踪节点 (StateTracker Node)

**文件**：`nodes/state_tracker_node.py`

**功能**：
- 维护任务状态机（待处理 → 进行中 → 已完成）
- 记录任务上下文和历史
- 判断任务是否完成
- 更新 Redis 缓存

**状态转换**：
```
┌──────────┐    任务开始    ┌──────────┐
│  待处理   │ ───────────→ │  进行中   │
└──────────┘               └──────────┘
     ↑                         │
     │                    任务完成
     │                         ↓
└──────────┘               ┌──────────┐
│  已完成   │ ←─────────── │  已完成   │
└──────────┘               └──────────┘
```

**判断逻辑**：
```python
def should_generate_document(state: AgentState) -> str:
    """判断是否生成文档"""
    analysis = state.get("multimodal_analysis", {})

    # 判断条件：
    # 1. 明确的完成信号（"完成了"、"做完了"）
    # 2. 任务状态标记为完成
    # 3. 包含生成报告的指令

    if any(signal in analysis.get("text", "") for signal in ["完成", "结束", "报告"]):
        return "yes"
    return "no"
```

#### 3.4 文档生成节点 (Document Node)

**文件**：`nodes/document_node.py`

**功能**：
- 根据任务类型选择文档模板
- 生成 Word 报告文档
- 更新 Excel 台账
- 保存文档到指定路径
- 记录文档更新历史

**模板系统**：
```
templates/
├── daily_report.j2         # 日报模板
├── weekly_report.j2        # 周报模板
├── monthly_report.j2       # 月报模板
├── task_summary.j2         # 任务汇总模板
└── meeting_minutes.j2      # 会议纪要模板
```

**输出路径**：
```
output/
├── reports/                # 报告文档
│   ├── daily_20260109.docx
│   └── weekly_20260109.docx
└── ledgers/                # 台账文件
    └── task_tracker.xlsx
```

## 📦 数据模型

### 核心数据结构

**原始消息 (RawMessage)**：
```python
class RawMessage(BaseModel):
    sender: str              # 发送者
    content: str             # 消息内容
    message_type: MessageType # 消息类型
    group_id: str            # 群组 ID
    timestamp: datetime      # 时间戳
    metadata: dict = {}      # 元数据
    image_url: Optional[str] = None  # 图片 URL（如果有）
```

**消息类型 (MessageType)**：
```python
class MessageType(str, Enum):
    TEXT = "text"            # 纯文本
    IMAGE = "image"          # 纯图片
    TEXT_IMAGE = "text_image" # 图文混合
    VOICE = "voice"          # 语音（未来支持）
    VIDEO = "video"          # 视频（未来支持）
    FILE = "file"            # 文件（未来支持）
```

**智能体状态 (AgentState)**：
```python
class AgentState(TypedDict):
    # 输入
    raw_message: RawMessage                  # 原始消息

    # 处理结果
    multimodal_analysis: Optional[dict]      # 多模态分析结果
    task_status: Optional[str]               # 任务状态
    document_updates: List[dict]             # 文档更新历史

    # 上下文
    messages: List[BaseMessage]              # 消息记录
    context: dict                            # 附加上下文
    next_action: Optional[str]               # 下一步动作
```

**多模态分析结果 (MultimodalAnalysis)**：
```python
class MultimodalAnalysis(BaseModel):
    text_summary: str                        # 文本摘要
    image_description: Optional[str]         # 图片描述
    intent: str                              # 意图识别
    entities: Dict[str, Any]                 # 提取的实体
    task_type: Optional[str]                 # 任务类型
    confidence: float                        # 置信度
    rag_context: Optional[List[str]]         # RAG 检索上下文
```

## 🔀 数据流转

### 消息处理流程

```
1. 微信消息
   ↓
2. 微信沙盒容器捕获
   ↓
3. 生产者服务推送 (SSE)
   ↓
4. MonitorAgent 接收
   ↓
5. HTTP POST 到 Orchestrator
   ↓
6. LangGraph 工作流执行
   │
   ├─→ Monitor Node: 消息验证
   ├─→ Multimodal Node: AI 分析
   │   ├─ 文本理解 (LLM)
   │   ├─ 图像理解 (Vision Model)
   │   └─ RAG 检索 (Vector DB)
   ├─→ StateTracker Node: 状态更新
   │   ├─ 判断任务状态
   │   ├─ 更新 Redis
   │   └─ 决策下一步
   └─→ Document Node: 文档生成
       ├─ 选择模板
       ├─ 填充数据
       ├─ 生成 Word/Excel
       └─ 保存文件
   ↓
7. 返回结果
```

### 状态流转

```
初始状态
  ↓
raw_message (接收消息)
  ↓
multimodal_analysis (AI 分析)
  ↓
task_status (状态更新)
  ↓
判断: 任务完成?
  ├─ 否 → END (等待下一条消息)
  └─ 是 → document_updates (生成文档)
          ↓
        END
```

## 🗂️ 项目目录结构

```
Mutil_Agent_WechatGroup_RPA/
├── agents/                              # 智能体模块
│   └── monitor_agent.py                 # 监控智能体
│
├── config/                              # 配置管理
│   ├── settings.yaml                    # 主配置文件
│   └── settings.py                      # Pydantic 配置类
│
├── core/                                # 核心框架
│   ├── schemas.py                       # 数据模型定义
│   ├── state.py                         # LangGraph 状态定义
│   ├── workflows/                       # 工作流定义
│   │   ├── main_workflow.py             # 主工作流
│   │   └── nodes/                       # 工作流节点
│   │       ├── monitor_node.py          # 监控节点
│   │       ├── multimodal_node.py       # 多模态分析节点
│   │       ├── state_tracker_node.py    # 状态跟踪节点
│   │       └── document_node.py         # 文档生成节点
│   └── exceptions.py                    # 自定义异常
│
├── tools/                               # 工具层
│   ├── excel_tool.py                    # Excel 更新工具
│   ├── word_tool.py                     # Word 报告生成工具
│   └── __init__.py
│
├── knowledge_base/                      # 知识库管理
│   ├── vector_store.py                  # 向量存储管理
│   └── embeddings.py                    # 嵌入模型管理
│
├── services/                            # 服务层
│   ├── orchestrator/                    # 编排中心
│   │   └── main.py                      # FastAPI 应用
│   └── wechat_sandbox/                  # 微信沙盒
│       ├── Dockerfile
│       ├── start.sh
│       └── producer_service/            # 消息生产者服务
│
├── scripts/                             # 工具脚本
│   ├── init_knowledge_base.py           # 初始化知识库
│   ├── start_all.py                     # 启动所有服务
│   └── run_monitor_agent.py             # 运行监控智能体
│
├── templates/                           # Jinja2 模板
│   ├── daily_report.j2                  # 日报模板
│   ├── weekly_report.j2                 # 周报模板
│   └── task_summary.j2                  # 任务汇总模板
│
├── data/                                # 数据目录
│   ├── chroma_db/                       # 向量数据库
│   └── wechat_profile/                  # 微信用户数据
│
├── output/                              # 输出目录
│   ├── reports/                         # 生成的报告
│   └── ledgers/                         # 台账文件
│
├── logs/                                # 日志目录
│
├── tests/                               # 测试目录
│   ├── unit/                            # 单元测试
│   ├── integration/                     # 集成测试
│   └── workflows/                       # 工作流测试
│
├── docs/                                # 文档目录
│   ├── ENVIRONMENT_SETUP.md             # 环境配置说明
│   └── ENVIRONMENT_INIT.md              # 环境初始化指南
│
├── docker-compose.yml                   # Docker 编排配置
├── requirements.txt                     # Python 依赖
├── environment.yml                      # Conda 环境配置
├── .env.example                         # 环境变量示例
├── .gitignore                           # Git 忽略文件
├── README.md                            # 项目说明
├── claude.md                            # Claude Code 上下文（英文）
├── claude-cn.md                         # Claude Code 上下文（中文）
└── agent.md                             # 本文档：AI 智能体上下文
```

## ⚙️ 配置管理

### 配置文件优先级

```
系统环境变量 > .env 文件 > settings.yaml > 代码默认值
```

### 环境变量命名规范

使用双下划线表示嵌套配置：

```bash
# settings.yaml 中：
# ai:
#   ollama:
#     base_url: "http://localhost:11434"

# 对应的环境变量：
export AI__OLLAMA__BASE_URL="http://localhost:11434"
```

### 主要配置项

```yaml
# 项目配置
project:
  name: "wechat-workflow-agent"
  env: "development"  # development | production

# AI 模型服务
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
    embedding_model: "qwen3-embedding-4b"
    chat_model: "qwen3-72b:latest"

# Redis 配置
redis:
  host: "localhost"
  port: 6379
  lock_db: 1          # 分布式锁数据库
  cache_db: 0         # 缓存数据库

# 向量数据库
chroma:
  persist_directory: "data/chroma_db"
  collection_name: "wechat_messages"

# 微信沙盒
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  data_volume: "wechat-data"
  producer_service_url: "http://localhost:6789"

# 文档工具
ai:
  excel:
    template_path: "templates/excel_template.xlsx"
    output_path: "output/ledgers"
  word:
    template_dir: "templates"
    output_path: "output/reports"

# 日志配置
logging:
  level: "INFO"        # DEBUG | INFO | WARNING | ERROR
  format: "json"       # json | text
  file: "logs/app.log"
```

## 🚀 快速开始

### 方式一：使用 Conda 虚拟环境（推荐）

**Windows 用户**：
```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd D:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建必要的目录
mkdir data\chroma_db data\wechat_profile output\reports output\ledgers templates logs

# 6. 复制环境变量配置
copy .env.example .env

# 7. 启动基础设施服务
docker-compose up -d redis ollama

# 8. 拉取 AI 模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
docker exec -it ollama ollama pull qwen3-72b

# 9. 初始化知识库
python scripts/init_knowledge_base.py

# 10. 启动编排器
uvicorn services.orchestrator.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/Mac 用户**：
```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建必要的目录
mkdir -p data/chroma_db data/wechat_profile output/{reports,ledgers} templates logs

# 6. 复制环境变量配置
cp .env.example .env

# 7. 启动基础设施服务
docker-compose up -d redis ollama

# 8. 拉取 AI 模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
docker exec -it ollama ollama pull qwen3-72b

# 9. 初始化知识库
python scripts/init_knowledge_base.py

# 10. 启动编排器
uvicorn services.orchestrator.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式二：直接安装依赖

```bash
# 1. 安装项目依赖
pip install -e .

# 2-10. 同方式一的步骤 2-10
```

## 🔧 开发指南

### 添加新的工作流节点

**步骤 1**：创建节点文件
```python
# core/workflows/nodes/new_node.py
from typing import TypedDict
from ..state import AgentState
import structlog

logger = structlog.get_logger()

def process(state: AgentState) -> AgentState:
    """节点处理逻辑

    Args:
        state: 当前智能体状态

    Returns:
        更新后的状态
    """
    logger.info("执行新节点", state=state)

    # 实现节点逻辑
    result = "处理结果"

    # 更新状态
    state["context"]["new_node_result"] = result

    return state
```

**步骤 2**：注册到工作流
```python
# core/workflows/main_workflow.py
from .nodes.new_node import process as new_node_process

def create_workflow():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("new_node", new_node_process)

    # 添加边（定义节点间的连接）
    workflow.add_edge("multimodal", "new_node")
    workflow.add_edge("new_node", "state_tracker")

    return workflow.compile()
```

### 添加新的工具

**步骤 1**：创建工具类
```python
# tools/new_tool.py
from typing import Dict, Any
from config.settings import settings
import structlog

logger = structlog.get_logger()

class NewTool:
    """新工具类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("初始化工具", config=config)

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具操作

        Args:
            data: 输入数据

        Returns:
            执行结果
        """
        logger.info("执行工具", data=data)

        # 实现工具逻辑
        result = {"status": "success", "data": data}

        return result
```

**步骤 2**：注册工具
```python
# tools/__init__.py
from .new_tool import NewTool

__all__ = ["WordTool", "ExcelTool", "NewTool"]
```

**步骤 3**：在工作流节点中使用
```python
from tools import NewTool

def process(state: AgentState) -> AgentState:
    tool = NewTool(config=settings.ai.new_tool)
    result = tool.execute({"key": "value"})
    state["context"]["tool_result"] = result
    return state
```

### 扩展消息类型

**步骤 1**：更新枚举
```python
# core/schemas.py
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TEXT_IMAGE = "text_image"
    VOICE = "voice"      # 新增语音类型
    VIDEO = "video"      # 新增视频类型
    FILE = "file"        # 新增文件类型
```

**步骤 2**：在多模态节点中添加处理逻辑
```python
# core/workflows/nodes/multimodal_node.py

async def handle_voice_message(message: RawMessage) -> dict:
    """处理语音消息"""
    # 1. 下载语音文件
    # 2. 使用 Whisper 转文字
    # 3. 返回文本内容
    pass

async def handle_video_message(message: RawMessage) -> dict:
    """处理视频消息"""
    # 1. 下载视频文件
    # 2. 提取关键帧
    # 3. 使用视觉模型分析
    pass
```

### 自定义文档模板

**步骤 1**：创建 Jinja2 模板
```jinja2
{# templates/custom_report.j2 #}
---
title: {{ title }}
date: {{ date|strftime('%Y-%m-%d') %}
author: {{ author }}
---

# {{ title }}

**生成时间**: {{ date }}
**作者**: {{ author }}

## 任务列表

{% for task in tasks %}
### {{ task.name }}
- 状态: {{ task.status }}
- 负责人: {{ task.assignee }}
- 截止日期: {{ task.deadline }}
- 描述: {{ task.description }}
{% endfor %}

## 统计信息

- 总任务数: {{ tasks|length }}
- 已完成: {{ tasks|selectattr('status', 'equalto', 'completed')|list|length }}
- 进行中: {{ tasks|selectattr('status', 'equalto', 'in_progress')|list|length }}
```

**步骤 2**：使用模板生成文档
```python
from tools.word_tool import WordTool

tool = WordTool(config=settings.ai.word)
tool.generate_from_template(
    template_path="templates/custom_report.j2",
    output_path="output/reports/custom.docx",
    context={
        "title": "自定义报告",
        "date": datetime.now(),
        "author": "AI 智能体",
        "tasks": [...]
    }
)
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_workflow.py

# 运行特定测试函数
pytest tests/test_workflow.py::test_multimodal_node

# 生成覆盖率报告
pytest --cov=core --cov=services --cov=agents --cov-report=html

# 显示详细输出
pytest -v

# 只运行失败的测试
pytest --lf
```

### 编写测试

```python
# tests/workflows/test_multimodal_node.py
import pytest
from core.workflows.nodes.multimodal_node import process
from core.state import AgentState
from core.schemas import RawMessage, MessageType

@pytest.mark.asyncio
async def test_text_message_processing():
    """测试文本消息处理"""
    # 准备测试数据
    state: AgentState = {
        "raw_message": RawMessage(
            sender="张三",
            content="请生成本周工作周报",
            message_type=MessageType.TEXT,
            group_id="test_group",
            timestamp=datetime.now()
        ),
        "multimodal_analysis": None,
        "task_status": None,
        "document_updates": [],
        "messages": [],
        "context": {},
        "next_action": None
    }

    # 执行节点
    result = await process(state)

    # 验证结果
    assert result["multimodal_analysis"] is not None
    assert result["multimodal_analysis"]["intent"] == "generate_report"
```

## 🐛 故障排查

### 常见问题及解决方案

#### 1. 容器启动失败

**症状**：`docker-compose up` 报错

**排查步骤**：
```bash
# 检查 Docker 是否运行
docker ps

# 检查端口占用
# Windows:
netstat -ano | findstr "5800"
netstat -ano | findstr "6379"
netstat -ano | findstr "11434"

# Linux/Mac:
lsof -i :5800
lsof -i :6379
lsof -i :11434

# 查看容器日志
docker-compose logs wechat-sandbox
docker-compose logs redis
docker-compose logs ollama
```

**解决方案**：
- 停止占用端口的服务
- 删除旧容器：`docker-compose down -v`
- 重新启动：`docker-compose up -d`

#### 2. 工作流执行失败

**症状**：API 返回 500 错误

**排查步骤**：
```bash
# 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 检查 Redis 连接
redis-cli ping

# 查看编排器日志
# (查看运行 uvicorn 的终端输出)

# 检查模型是否加载
docker exec -it ollama ollama list
```

**解决方案**：
- 确保 Ollama 服务正常运行
- 重新拉取模型：`docker exec -it ollama ollama pull qwen3-vl-8b`
- 重启 Redis：`docker-compose restart redis`

#### 3. 消息流断开

**症状**：MonitorAgent 无法接收消息

**排查步骤**：
```bash
# 检查生产者服务
curl http://localhost:6789/stream

# 检查容器状态
docker ps | grep wechat-sandbox

# 查看容器日志
docker logs wechat-sandbox --tail 100
```

**解决方案**：
- 重启微信沙盒容器
- 检查 noVNC 界面是否正常显示
- 重新启动 MonitorAgent

#### 4. 模型调用超时

**症状**：Ollama 请求超时

**排查步骤**：
```bash
# 检查模型是否正确加载
docker exec -it ollama ollama list

# 测试模型推理
docker exec -it ollama ollama run qwen3-vl-8b "测试"

# 查看 Ollama 日志
docker logs ollama --tail 50
```

**解决方案**：
- 增加 Ollama 超时时间配置
- 使用更小的模型（如 qwen3-vl-3b）
- 增加 Docker 内存限制

### 调试技巧

#### 启用详细日志

```python
# .env 文件
LOGGING__LEVEL=DEBUG
LOGGING__FORMAT=json
```

#### 打印工作流状态

```python
# 在节点中添加调试输出
def debug_node(state: AgentState) -> AgentState:
    print(f"当前状态:\n{json.dumps(state, indent=2, ensure_ascii=False)}")
    return state
```

#### 可视化工作流图

```python
from core.workflows.main_workflow import create_workflow

workflow = create_workflow()
print(workflow.get_graph().print_ascii())
```

## 🔒 安全注意事项

1. **敏感信息保护**
   - 不要在代码中硬编码密钥
   - 使用环境变量管理敏感配置
   - `.env` 文件已加入 `.gitignore`

2. **输入验证**
   - 验证所有用户输入
   - 防止注入攻击
   - 限制文件上传大小和类型

3. **容器隔离**
   - 使用 Docker 网络隔离服务
   - 限制容器资源使用
   - 定期更新基础镜像

4. **API 安全**
   - 实现身份认证（JWT、API Key）
   - 使用 HTTPS（生产环境）
   - 添加速率限制

5. **日志脱敏**
   - 避免记录敏感信息
   - 对日志进行访问控制
   - 定期清理旧日志

## 📚 扩展资源

### 官方文档
- [LangGraph 文档](https://python.langchain.com/docs/langgraph)
- [LangChain 文档](https://python.langchain.com/docs)
- [Ollama 文档](https://ollama.ai/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [ChromaDB 文档](https://docs.trychroma.com)

### 项目文档
- `README.md` - 项目概述和快速开始
- `claude.md` - Claude Code 上下文（英文）
- `claude-cn.md` - Claude Code 上下文（中文）
- `docs/ENVIRONMENT_SETUP.md` - 环境配置说明
- `docs/ENVIRONMENT_INIT.md` - 环境初始化指南

### 相关技术
- Python 异步编程：`asyncio`
- 结构化日志：`structlog`
- 配置管理：`pydantic-settings`
- 容器化：`Docker`, `docker-compose`
- 测试框架：`pytest`

## 📝 开发规范

### 代码风格

- **类型提示**：所有函数必须添加类型提示
- **文档字符串**：使用 Google 风格的 docstrings
- **命名规范**：
  - 类名：大驼峰（`MonitorAgent`）
  - 函数/变量：小写下划线（`process_message`）
  - 常量：大写下划线（`MAX_RETRIES`）
- **导入顺序**：标准库 → 第三方库 → 本地模块

### 异步编程规范

```python
# ✅ 正确：使用 async/await
async def process_message(message: RawMessage) -> dict:
    result = await ai_model.analyze(message)
    return result

# ❌ 错误：阻塞调用
async def process_message(message: RawMessage) -> dict:
    result = ai_model.analyze(message)  # 缺少 await
    return result
```

### 错误处理规范

```python
# ✅ 正确：捕获特定异常
from core.exceptions import MessageValidationError

try:
    validated = validate_message(message)
except MessageValidationError as e:
    logger.error("消息验证失败", error=str(e))
    raise

# ❌ 错误：捕获所有异常
try:
    validated = validate_message(message)
except Exception:  # 过于宽泛
    pass
```

### 日志记录规范

```python
import structlog

logger = structlog.get_logger()

# ✅ 正确：使用结构化日志
logger.info("处理消息",
            sender=message.sender,
            message_type=message.message_type,
            message_id=message.id)

# ❌ 错误：字符串拼接
logger.info(f"处理来自 {message.sender} 的消息")
```

## 🎯 项目路线图

### 已完成 ✅
- [x] 基础架构搭建
- [x] LangGraph 工作流实现
- [x] 多模态消息处理（文本+图像）
- [x] 基础文档生成（Word、Excel）
- [x] Redis 状态管理
- [x] ChromaDB 知识库

### 进行中 🚧
- [ ] 语音消息支持（Whisper）
- [ ] Web 管理界面
- [ ] 性能优化和缓存策略

### 计划中 📋
- [ ] 视频消息支持
- [ ] 文件处理能力
- [ ] 企业微信 API 集成
- [ ] 数据分析和可视化
- [ ] 多租户支持
- [ ] 云端部署方案

## 📞 支持与反馈

### 问题报告
如遇到问题，请提供以下信息：
1. 系统环境（操作系统、Python 版本）
2. 错误信息和堆栈跟踪
3. 相关配置和日志
4. 复现步骤

### 贡献指南
欢迎提交 Pull Request！请确保：
1. 代码符合项目规范
2. 添加必要的测试
3. 更新相关文档
4. 通过所有测试

---

**文档版本**: v1.0.0
**最后更新**: 2026-01-09
**维护者**: 项目团队
