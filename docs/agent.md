# Agent 系统架构文档

## 概述

本项目是一个基于 LangGraph 的多模态 Agent 自动化系统，用于监控微信群消息并进行智能分析和文档生成。系统采用微服务架构，包含监控 Agent、工作流协调中心、多模态分析、状态跟踪和文档生成等核心组件。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     微信沙盒容器 (Docker)                      │
│  - WeChat 实例                                               │
│  - 生产者服务 (http://localhost:6789)                        │
│  - noVNC 界面 (http://localhost:5800)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ 消息流
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  MonitorAgent (监控Agent)                      │
│  - 容器生命周期管理                                           │
│  - 消息流消费                                                 │
│  - 工作流触发                                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /workflow/trigger
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator (工作流协调中心)                     │
│  - FastAPI 服务 (http://localhost:8000)                      │
│  - LangGraph 工作流引擎                                       │
│  - 状态管理                                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph 工作流                            │
│  ┌─────────┐    ┌──────────────┐    ┌─────────────┐         │
│  │ Monitor │ →  │  Multimodal  │ →  │ StateTracker │         │
│  │  Node   │    │     Node     │    │    Node     │         │
│  └─────────┘    └──────────────┘    └──────┬──────┘         │
│                                            │                 │
│                                  ┌─────────┴─────────┐       │
│                                  │                   │       │
│                          任务完成?  否              │ 是     │
│                                  ↓                   ↓       │
│                                END              ┌─────────┐  │
│                                                  │Document │  │
│                                                  │  Node   │  │
│                                                  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   外部服务与工具                              │
│  - Redis (缓存与分布式锁)                                     │
│  - Ollama (AI 模型服务)                                      │
│  - ChromaDB (向量数据库)                                      │
│  - Word/Excel 工具 (文档生成)                                 │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. MonitorAgent (监控Agent)

**文件位置**: [`agents/monitor_agent.py`](../agents/monitor_agent.py)

**功能职责**:
- 管理微信沙盒 Docker 容器的生命周期（启动、停止）
- 消费微信消息流（Server-Sent Events）
- 解析消息并触发工作流执行
- 提供消息回调机制

**主要方法**:

| 方法名 | 功能说明 |
|--------|----------|
| `start_container()` | 启动微信沙盒容器，端口映射：5800(noVNC), 5900(VNC), 6789(生产者服务) |
| `stop_container()` | 停止微信沙盒容器 |
| `start()` | 启动监控 Agent，开始消费消息流 |
| `stop()` | 停止监控 Agent 和容器 |
| `set_message_callback()` | 设置消息处理回调函数 |

**使用示例**:

```python
from agents.monitor_agent import MonitorAgent

# 创建监控Agent实例
agent = MonitorAgent(orchestrator_url="http://localhost:8000")

# 启动监控Agent
await agent.start()

# 停止监控Agent
agent.stop()
```

**配置依赖**:

```yaml
# config/settings.yaml
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  data_volume: "wechat-data"
  producer_service_url: "http://localhost:6789"
```

### 2. Orchestrator (工作流协调中心)

**文件位置**: [`services/orchestrator/main.py`](../services/orchestrator/main.py)

**功能职责**:
- 提供 FastAPI REST API 接口
- 管理和执行 LangGraph 工作流
- 处理工作流状态和结果返回
- 健康检查和异常处理

**API 端点**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径，返回服务信息 |
| `/health` | GET | 健康检查 |
| `/workflow/trigger` | POST | 触发工作流执行 |
| `/workflow/status` | GET | 获取工作流状态 |

**触发工作流请求示例**:

```python
import httpx

async def trigger_workflow():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/workflow/trigger",
            json={
                "sender": "张三",
                "content": "请生成本周工作周报",
                "message_type": "text",
                "group_id": "group_123",
                "metadata": {"priority": "high"}
            },
            timeout=30.0
        )
        return response.json()
```

### 3. LangGraph 工作流

**文件位置**: [`core/workflows/main_workflow.py`](../core/workflows/main_workflow.py)

**工作流结构**:

```
monitor → multimodal → state_tracker → [条件判断] → document → END
                                        ↓
                                     END
```

#### 3.1 Monitor Node (监控节点)

**文件位置**: [`core/workflows/nodes/monitor_node.py`](../core/workflows/nodes/monitor_node.py)

**功能**:
- 接收原始消息
- 消息类型验证和预处理
- 消息路由到下一个节点

#### 3.2 Multimodal Node (多模态分析节点)

**文件位置**: [`core/workflows/nodes/multimodal_node.py`](../core/workflows/nodes/multimodal_node.py)

**功能**:
- 文本消息：使用 LLM 进行意图识别和任务提取
- 图片消息：使用视觉模型（Qwen3-VL）进行图像理解
- 混合消息：融合文本和图像信息进行综合分析
- 生成结构化分析结果

**AI 模型配置**:

```yaml
# config/settings.yaml
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
    embedding_model: "qwen3-embedding-4b"
    chat_model: "qwen3-72b:latest"
```

#### 3.3 State Tracker Node (状态跟踪节点)

**文件位置**: [`core/workflows/nodes/state_tracker_node.py`](../core/workflows/nodes/state_tracker_node.py)

**功能**:
- 维护任务状态（待处理、进行中、已完成）
- 记录上下文信息
- 判断是否需要生成文档
- 更新 Redis 缓存状态

**条件判断逻辑**:

```python
def should_generate_document(state: AgentState) -> Literal["yes", "no"]:
    """判断是否生成文档
    
    Returns:
        "yes": 任务完成，生成文档
        "no": 任务未完成，继续等待
    """
```

#### 3.4 Document Node (文档生成节点)

**文件位置**: [`core/workflows/nodes/document_node.py`](../core/workflows/nodes/document_node.py)

**功能**:
- 根据任务类型选择文档模板
- 生成 Word/Excel 文档
- 保存文档到指定路径
- 记录文档更新历史

**工具集成**:

| 工具类 | 文件位置 | 功能 |
|--------|----------|------|
| `WordTool` | [`tools/word_tool.py`](../tools/word_tool.py) | Word 文档生成 |
| `ExcelTool` | [`tools/excel_tool.py`](../tools/excel_tool.py) | Excel 文档生成 |

## 数据流

### 1. 消息流

```
微信沙盒 → 生产者服务 (/stream) → MonitorAgent → Orchestrator → LangGraph
```

### 2. 状态流

```
AgentState (状态对象) → 各节点处理 → 更新状态 → 传递给下一节点
```

**状态结构**:

```python
from typing import TypedDict, Optional
from ..schemas import RawMessage

class AgentState(TypedDict):
    raw_message: RawMessage          # 原始消息
    multimodal_analysis: Optional[dict]  # 多模态分析结果
    task_status: Optional[str]       # 任务状态
    document_updates: list            # 文档更新历史
    messages: list                    # 消息记录
    context: dict                     # 上下文信息
```

### 3. 文档流

```
任务完成 → 文档节点 → 选择模板 → 生成文档 → 保存文件 → 记录更新
```

## 配置管理

### 环境变量优先级

```
系统环境变量 > .env 文件 > settings.yaml > 代码默认值
```

### 关键配置项

```yaml
# AI 模型服务
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
    embedding_model: "qwen3-embedding-4b"

# Redis 缓存
redis:
  host: "localhost"
  port: 6379
  lock_db: 1

# 微信沙盒
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  data_volume: "wechat-data"
  producer_service_url: "http://localhost:6789"

# 向量数据库
chroma:
  persist_directory: "data/chroma_db"
  collection_name: "wechat_messages"
```

## 部署指南

### 1. 启动依赖服务

```bash
# 启动 Redis 和 Ollama
docker-compose up -d redis ollama

# 拉取 Ollama 模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
docker exec -it ollama ollama pull qwen3-72b
```

### 2. 启动 Orchestrator 服务

```bash
# 激活 Conda 环境
conda activate wechat-workflow-agent

# 启动协调中心
python -m services.orchestrator.main
```

### 3. 启动 MonitorAgent

```bash
# 方法 1: 使用脚本
python scripts/run_monitor_agent.py

# 方法 2: 直接运行
python -c "
import asyncio
from agents.monitor_agent import MonitorAgent

async def main():
    agent = MonitorAgent()
    await agent.start()

asyncio.run(main())
"
```

### 4. 访问服务

- **Orchestrator API**: http://localhost:8000
- **微信沙盒 noVNC**: http://localhost:5800
- **Ollama API**: http://localhost:11434
- **Redis**: localhost:6379

## 扩展开发

### 添加新的工作流节点

1. 创建节点文件: [`core/workflows/nodes/new_node.py`](../core/workflows/nodes/new_node.py)

```python
from typing import TypedDict
from ..state import AgentState

def process(state: AgentState) -> AgentState:
    """处理新节点逻辑"""
    # 实现节点逻辑
    state["context"]["new_node_result"] = "处理结果"
    return state
```

2. 注册节点到工作流:

```python
# core/workflows/main_workflow.py
from .nodes.new_node import new_node

def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("new_node", new_node.process)
    # 添加边
    workflow.add_edge("multimodal", "new_node")
    return workflow.compile()
```

### 添加新的工具

1. 创建工具文件: [`tools/new_tool.py`](../tools/new_tool.py)

```python
class NewTool:
    """新工具类"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def execute(self, data: dict) -> dict:
        """执行工具操作"""
        # 实现工具逻辑
        return {"result": "操作成功"}
```

2. 注册工具:

```python
# tools/__init__.py
from .new_tool import NewTool

__all__ = ["WordTool", "ExcelTool", "NewTool"]
```

### 扩展消息类型

1. 更新消息枚举:

```python
# core/schemas.py
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"      # 新增语音类型
    VIDEO = "video"      # 新增视频类型
    FILE = "file"        # 新增文件类型
```

2. 实现对应的消息处理逻辑。

## 监控与日志

### 结构化日志

系统使用 `structlog` 进行结构化日志记录：

```python
import structlog

logger = structlog.get_logger()
logger.info("处理消息", sender="张三", content="请生成周报")
```

### 日志级别

- `INFO`: 正常操作流程
- `WARNING`: 可忽略的异常情况
- `ERROR`: 需要注意的错误
- `DEBUG`: 调试信息（开发环境）

### 健康检查

```bash
# 检查 Orchestrator 服务
curl http://localhost:8000/health

# 检查工作流状态
curl http://localhost:8000/workflow/status
```

## 故障排查

### 常见问题

1. **容器启动失败**
   - 检查 Docker 是否运行: `docker ps`
   - 检查端口是否被占用: `netstat -ano | findstr "5800"`
   - 查看容器日志: `docker logs wechat-sandbox`

2. **工作流执行失败**
   - 检查 Ollama 服务是否可用: `curl http://localhost:11434/api/tags`
   - 检查 Redis 连接: `redis-cli ping`
   - 查看 Orchestrator 日志

3. **消息流断开**
   - 检查生产者服务: `curl http://localhost:6789/stream`
   - 重启 MonitorAgent

### 性能优化

1. **使用连接池**: 复用 HTTP 客户端连接
2. **异步处理**: 使用 `asyncio` 提高并发性能
3. **缓存策略**: 使用 Redis 缓存常用数据
4. **批量处理**: 合并多个消息进行批量分析

## 安全建议

1. **环境变量**: 使用 `.env` 文件管理敏感配置，不要提交到 Git
2. **API 认证**: 为 Orchestrator 添加认证机制（JWT、API Key）
3. **容器隔离**: 使用 Docker 网络隔离容器
4. **日志脱敏**: 避免在日志中记录敏感信息
5. **访问控制**: 限制 noVNC 和 VNC 的访问权限

## 参考资源

- [LangGraph 官方文档](https://python.langchain.com/docs/langgraph)
- [Ollama 官方文档](https://ollama.ai/docs)
- [FastAPI 官方文档](https://fastapi.tiangolo.com)
- [Docker 官方文档](https://docs.docker.com)
- [Redis 官方文档](https://redis.io/docs)

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-01-09 | 初始版本，包含核心功能 |

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目！

## 许可证

请查看项目根目录的 LICENSE 文件。
