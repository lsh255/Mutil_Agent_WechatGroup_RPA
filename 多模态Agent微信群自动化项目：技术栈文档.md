技术栈文档 (LangGraph版)
1. 开发与运行时环境
操作系统：推荐 Linux (Ubuntu 22.04 LTS) 或 WSL2 (Windows)

Python：3.10+ (建议 3.11+ 以获得更好的异步支持)

容器运行时：Docker 24.0+, Docker Compose 2.20+

版本控制：Git

2. 技术栈详情
2.1 Agent框架与工作流编排
组件	具体技术/库	版本/说明	用途与影响
Agent编排框架	LangGraph	0.0.50+	核心变更。用于构建有状态、多参与者的Agent工作流。将替代部分自定义的消息路由逻辑，使StateManager Agent的功能内化为工作流的状态管理。
LangChain集成	LangChain	0.1.0+	提供与LangGraph无缝集成的工具调用、提示词管理、以及与Chroma等组件的连接器。
大模型调用	LangChain-Community	0.0.10+	通过其集成的ChatOllama等类，方便地调用本地Ollama模型。
Web框架	FastAPI	0.104+	构建对外HTTP服务（Orchestrator管理API、健康检查）。内部Agent协作将优先使用LangGraph流程。
消息总线	Redis	7.2+	用途调整：主要用于系统级事件通知（如“任务完成”）、缓存以及跨工作流会话的锁，而非细粒度Agent间消息传递。
2.2 AI与多模态核心
组件	具体技术/库	版本/说明	用途与影响
大模型服务	Ollama	最新版	本地部署和运行 Qwen2-VL (视觉语言模型) 和 Qwen3-Embedding-8B (嵌入模型)。
向量数据库	Chroma	0.4.18+	核心变更。轻量级、嵌入式向量数据库，与LangChain生态集成度极高，简化RAG实现。
嵌入模型	Qwen/Qwen3-Embedding-8B	via Ollama	核心变更。通过Ollama拉取并运行此嵌入模型，用于将业务知识库文本转换为向量，存入Chroma。
多模态处理	PIL / OpenCV	最新版	图像预处理，为Qwen2-VL模型准备截图数据。
RAG检索链	LangChain Expression Language (LCEL)	-	用于流畅地组合检索、上下文构建、提示、模型调用等步骤，构建高效的RAG流程。
2.3 微信沙盒与自动化
组件	具体技术/库	版本	用途说明
基础镜像	jlesage/baseimage-gui	debian-11	为Docker容器提供轻量级GUI和VNC/noVNC支持。
虚拟显示	Xvfb	-	在容器内提供虚拟显示服务器。
桌面自动化	PyAutoGUI	0.9+	在沙盒容器内部进行模拟操作。
图像处理	OpenCV-Python	4.8+	图像匹配。
生产者服务	FastAPI + SSE	-	容器内服务，用于流式输出消息。
2.4 数据、配置与存储
组件	具体技术/库	版本	用途说明
数据验证与配置	Pydantic	2.5+	用于定义严格的数据模型、配置管理和API请求/响应验证。
配置管理	pydantic-settings	2.1+	多源配置管理。
Excel操作	openpyxl	3.1+	读写和更新Excel台账。
Word操作	python-docx	1.1+	生成Word文档。
模板引擎	Jinja2	3.1+	报告模板渲染。
容器控制	Docker SDK for Python	7.0+	控制微信沙盒容器生命周期。
2.5 可观测性与运维
组件	具体技术/库	版本	用途说明
结构化日志	structlog	23.2+	生成结构化日志，便于追踪LangGraph工作流的执行路径。
指标导出	prometheus-client	0.19+	暴露性能指标。
进程管理	Supervisord	-	生产环境进程管理。
3. 项目目录结构参考 (调整后)
text
wechat-workflow-ai-agent/
├── README.md
├── pyproject.toml                      # 现代Python项目依赖管理（推荐）
├── docker-compose.yml                  # 编排Redis、Ollama等
├── config/
│   ├── settings.yaml                   # 主配置文件
│   └── __init__.py                     # Pydantic Settings类
├── core/                               # 核心框架与协议
│   ├── schemas.py                      # Pydantic消息/状态协议
│   ├── workflows/                      # **新增：LangGraph工作流定义**
│   │   ├── __init__.py
│   │   ├── main_workflow.py            # 主协调工作流
│   │   └── nodes/                      # 工作流节点（原Agent功能）
│   │       ├── monitor_node.py         # 原Monitor Agent功能
│   │       ├── multimodal_node.py      # 原Multimodal Agent功能
│   │       └── document_node.py        # 原Document Agent功能
│   └── state.py                        # 工作流状态（State）定义
├── services/
│   ├── orchestrator/                   # 协调中心FastAPI应用
│   │   ├── main.py
│   │   └── static/
│   └── wechat_sandbox/                 # 微信沙盒
│       ├── Dockerfile
│       └── producer_service/
├── agents/                             # **角色调整：对外服务或重型独立Agent**
│   ├── monitor_agent.py                # 管理沙盒，将数据触发至工作流
│   └── __init__.py
├── knowledge_base/                     # **新增：知识库管理**
│   ├── vector_store.py                 # Chroma向量库封装
│   ├── embeddings.py                   # Qwen3-Embedding封装
│   └── docs/                           # 存放知识库源文件
├── tools/                              # **新增：LangGraph工具定义**
│   ├── excel_tool.py                   # 更新Excel工具
│   ├── word_tool.py                    # 生成报告工具
│   └── __init__.py
├── scripts/                            # 部署、知识库初始化脚本
├── tests/
└── docs/
    ├── ARCHITECTURE.md
    └── TECHSTACK.md
4. 关键配置示例 (config/settings.yaml)
yaml
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
    vision_model: "qwen2-vl:latest"        # 多模态模型
    embedding_model: "qwen3-embedding-8b"  # **变更：嵌入模型**

# 向量数据库与知识库配置
vector_store:
  type: "chroma"                           # **核心变更**
  persist_directory: "./data/chroma_db"    # Chroma持久化路径
  collection_name: "work_knowledge_base"

# 微信沙盒配置
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  producer_service_url: "http://localhost:6789"
  data_volume: "./data/wechat_profile"

# 文档与工具配置
tools:
  excel_template_path: "./templates/task_log.xlsx"
  report_template_path: "./templates/daily_report.j2"
  output_dir: "./output"

# 基础设施
redis:
  host: "localhost"
  port: 6379
  # 可选：用于跨工作流锁的专用DB
  lock_db: 1
5. 核心组件初始化代码示例
5.1 初始化Chroma向量库与嵌入模型
python
# knowledge_base/vector_store.py
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from .config import settings

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
5.2 定义LangGraph工作流状态
python
# core/state.py
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
import operator

class AgentState(TypedDict):
    """LangGraph工作流的状态定义，贯穿整个处理流程。"""
    # 输入
    raw_message: Optional[dict]  # 来自微信的原始消息
    # 处理中间状态
    multimodal_analysis: Optional[dict]  # 多模态分析结果
    task_status: Optional[str]           # 任务状态（如 “waiting_mid”)
    # 输出
    document_updates: List[dict]         # 需要执行的文档更新指令
    # 用于串联对话的消息记录
    messages: Annotated[list, add_messages]
5.3 构建主工作流示例
python
# core/workflows/main_workflow.py
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import monitor_node, multimodal_node, state_node, document_node
from ..config import settings

def create_workflow():
    """创建并编译主处理工作流"""
    workflow = StateGraph(AgentState)
    
    # 添加节点（对应原Agent的核心功能）
    workflow.add_node(“monitor”, monitor_node.process)
    workflow.add_node(“multimodal”, multimodal_node.analyze)
    workflow.add_node(“state_tracker”, state_node.update)
    workflow.add_node(“document”, document_node.execute)
    
    # 设置边（定义流程逻辑）
    workflow.set_entry_point(“monitor”)
    workflow.add_edge(“monitor”, “multimodal”)
    workflow.add_edge(“multimodal”, “state_tracker”)
    # 状态节点决定下一步：若任务完成则生成文档，否则等待
    workflow.add_conditional_edges(
        “state_tracker”,
        state_node.should_generate_document,
        {“yes”: “document”, “no”: END}
    )
    workflow.add_edge(“document”, END)
    
    return workflow.compile()
6. 部署与运行说明
6.1 开发环境启动
启动基础设施：docker-compose up -d redis ollama (需在compose中配置Ollama)

拉取模型：

bash
ollama pull qwen2-vl:latest
ollama pull qwen3-embedding-8b
初始化知识库：运行 scripts/init_knowledge_base.py，将业务文档灌入Chroma。

构建并启动微信沙盒。

启动Orchestrator服务：uvicorn services.orchestrator.main:app --reload

触发工作流：Monitor Agent 接收到新消息后，将调用 workflow.invoke() 启动LangGraph处理流程。

6.2 生产部署建议
容器化：将 Orchestrator、Monitor Agent、知识库服务 等分别容器化。

Ollama管理：确保Ollama服务常驻，并监控GPU/内存使用。

Chroma持久化：确保 persist_directory 使用卷挂载，数据持久化。

状态存储：为LangGraph配置高可用的Redis实例作为状态存储后端。