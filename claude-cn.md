# Claude Code 上下文文档：基于 LangGraph 的微信群自动化系统

## 项目概述

这是一个基于 **LangGraph 构建的多模态 AI 智能体自动化系统**，用于监控微信群消息、理解图文混合内容、跟踪任务状态，并自动生成报告和更新电子表格。

**核心技术栈：**
- **LangGraph 0.0.50+**: 有状态智能体的编排框架
- **LangChain**: AI 工具集成
- **Ollama**: 本地 AI 模型服务（Qwen3-VL 视觉模型、Qwen3-Embedding 嵌入模型）
- **FastAPI**: REST API 编排层
- **ChromaDB**: 向量数据库（知识库）
- **Redis**: 状态存储和消息队列
- **Docker**: 容器化的微信沙盒环境（支持多实例部署）
- **VNC/noVNC**: 浏览器远程访问 Docker 化微信界面

## 架构模式

系统采用 **"中心化工作流 + 外围服务"** 的混合架构：

```
微信沙盒 (Docker 多实例) → 监控智能体 → 编排器 (FastAPI) → LangGraph 工作流
                                                      ↓
                                              [多模态分析 → 状态跟踪 → 文档生成]
                                                      ↓
                                              AI 服务 (Ollama + ChromaDB)
```

### 核心组件

1. **监控智能体 MonitorAgent** (`agents/monitor_agent.py`)
   - 管理微信 Docker 容器生命周期
   - 通过 Server-Sent Events (SSE) 消费消息流
   - 触发工作流执行
   - 支持多实例消息聚合

2. **编排器 Orchestrator** (`services/orchestrator/main.py`)
   - 运行在 8000 端口的 FastAPI 服务
   - 管理和执行 LangGraph 工作流
   - 处理状态和结果返回
   - 提供 RESTful API 端点

3. **LangGraph 工作流** (`core/workflows/`)
   - **监控节点 Monitor Node**: 消息验证和路由
   - **多模态节点 Multimodal Node**: 结合 RAG 的图文理解
   - **状态跟踪节点 StateTracker Node**: 任务状态管理
   - **文档节点 Document Node**: Excel/Word 文档生成

4. **微信沙盒服务** (`services/wechat_sandbox/`)
   - **生产者服务 Producer1Observer**: 监控微信群消息
   - **内容抓取 Producer2ContentFetcher**: 抓取消息内容
   - **消息队列 RedisQueueManager**: 消息持久化和分发
   - **屏幕检测 ChangeDetector**: 检测屏幕变化
   - **消息分类 MessageTypeClassifier**: 识别消息类型

5. **Web UI 界面** (`services/wechat_sandbox/static/`)
   - **VNC 集成**: 通过 noVNC 浏览器访问微信界面
   - **ROI 配置面板**: 可视化配置监控区域
   - **状态监控**: 实时显示服务状态
   - **消息流显示**: 实时展示捕获的消息

## 重要文件位置

### 配置文件
- `config/settings.yaml` - 主配置文件
- `.env` - 环境变量配置（不在 git 中）
- `docker-compose.yml` - 单实例服务编排配置
- `docker-compose.multi.yml` - 多实例服务编排配置（生产环境）

### 核心框架
- `core/schemas.py` - 数据模型定义（RawMessage、MessageType 等）
- `core/state.py` - LangGraph 状态定义（AgentState）
- `core/workflows/main_workflow.py` - 主工作流图
- `core/workflows/nodes/` - 各个节点的实现

### 工具层
- `tools/excel_tool.py` - Excel 更新操作
- `tools/word_tool.py` - Word 报告生成

### 微信沙盒服务
- `services/wechat_sandbox/producer_service/` - 生产者服务核心
  - `__init__.py` - 服务导出模块
  - `queue_manager.py` - Redis 队列管理器
  - `producer1_observer.py` - 消息观察者
  - `producer2_content_fetcher.py` - 内容抓取者
- `services/wechat_sandbox/utils/` - 工具模块
  - `classifier.py` - 消息类型分类器
  - `detector.py` - 屏幕变化检测器
- `services/wechat_sandbox/api_server.py` - FastAPI API 服务器
- `services/wechat_sandbox/static/index.html` - Web UI 界面

### 知识库
- `knowledge_base/vector_store.py` - ChromaDB 封装
- `knowledge_base/embeddings.py` - Ollama 嵌入模型集成

## 开发指南

### 使用 LangGraph 工作流

**添加新节点：**

1. 在 `core/workflows/nodes/new_node.py` 中创建节点：
```python
from typing import TypedDict
from ..state import AgentState

def process(state: AgentState) -> AgentState:
    """节点处理逻辑"""
    state["context"]["result"] = "已处理"
    return state
```

2. 在 `core/workflows/main_workflow.py` 中注册：
```python
from .nodes.new_node import process

workflow.add_node("new_node", process)
workflow.add_edge("multimodal", "new_node")
```

### 状态管理

`AgentState` 是一个流经所有节点的 `TypedDict`：
```python
class AgentState(TypedDict):
    raw_message: RawMessage          # 输入消息
    multimodal_analysis: Optional[dict]  # 分析结果
    task_status: Optional[str]       # 任务状态
    document_updates: list            # 更新历史
    messages: list                    # 消息日志
    context: dict                     # 附加上下文
```

**重要提示：** 节点必须返回更新后的状态，即使状态未改变。

### 配置访问

使用 Pydantic Settings 模式：
```python
from config.settings import settings

# 访问嵌套配置
ollama_url = settings.ai.ollama.base_url
vision_model = settings.ai.ollama.vision_model
```

环境变量会覆盖 YAML 配置：
- 使用双下划线表示嵌套：`AI__OLLAMA__BASE_URL`

### 使用 Ollama 模型

**视觉模型（Qwen3-VL）：**
```python
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

vision_model = ChatOllama(
    base_url=settings.ai.ollama.base_url,
    model="qwen3-vl-8b:latest"
)

# 处理图片
message = HumanMessage(content=[
    {"type": "text", "text": "描述这张图片"},
    {"type": "image_url", "url": "file://path/to/image.jpg"}
])
response = vision_model.invoke([message])
```

**嵌入模型：**
```python
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    base_url=settings.ai.ollama.base_url,
    model="qwen3-embedding-4b"
)
vector = embeddings.embed_query("要嵌入的文本")
```

### 文档生成

**Excel 更新：**
```python
from tools.excel_tool import ExcelTool

tool = ExcelTool(config=settings.ai.excel)
tool.update_row(
    sheet_name="Sheet1",
    row_index=5,
    data={"status": "完成", "date": "2026-01-09"}
)
```

**Word 报告：**
```python
from tools.word_tool import WordTool

tool = WordTool(config=settings.ai.word)
tool.generate_from_template(
    template_path="templates/daily_report.j2",
    output_path="output/report.docx",
    context={"title": "日报", "items": [...]}
)
```

### API 服务器生命周期管理

`api_server.py` 使用 FastAPI 的 `lifespan` 机制管理服务启动和关闭：

```python
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
```

### LangGraph 条件路由

使用条件边实现动态路由：

```python
def should_generate_document(state: AgentState) -> str:
    """判断是否应该生成文档"""
    analysis = state.get("multimodal_analysis", {})
    if any(signal in analysis.get("text", "") for signal in ["complete", "end", "report"]):
        return "yes"
    return "no"

# 在工作流中添加条件边
workflow.add_conditional_edges(
    "multimodal",
    should_generate_document,
    {
        "yes": "document_node",
        "no": END
    }
)
```

## 常见开发任务

### 添加新的消息类型

1. 在 `core/schemas.py` 中更新枚举：
```python
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"  # 新类型
```

2. 在 `multimodal_node.py` 中添加处理逻辑

3. 在 `monitor_node.py` 中更新验证逻辑

### 测试工作流执行

```bash
# 启动服务
docker-compose up -d redis ollama

# 拉取模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 启动编排器
uvicorn services.orchestrator.main:app --reload

# 触发工作流
curl -X POST http://localhost:8000/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "张三",
    "content": "请生成本周工作周报",
    "message_type": "text",
    "group_id": "group_123"
  }'
```

### 调试 LangGraph 工作流

**启用工作流可视化：**
```python
from core.workflows.main_workflow import create_workflow

workflow = create_workflow()
# 打印图结构
print(workflow.get_graph().print_ascii())
```

**在每个节点检查状态：**
```python
def debug_node(state: AgentState) -> AgentState:
    print(f"当前状态: {state}")
    # 节点逻辑
    return state
```

### 使用 RAG（知识库）

```python
from knowledge_base.vector_store import VectorStoreManager

vector_store = VectorStoreManager(config=settings.vector_store)

# 添加文档
vector_store.add_documents([
    {"text": "知识内容", "metadata": {"source": "doc1"}}
])

# 搜索
results = vector_store.similarity_search(
    query="用户的问题",
    k=3
)
```

### 配置 ROI 监控区域

通过 Web UI 界面配置 ROI 区域：

1. 访问 `http://localhost:6080`（noVNC）或 `http://localhost:8000/static/index.html`（Web UI）
2. 点击"配置 ROI"按钮
3. 在预览图像上拖拽选择监控区域
4. 保存配置，配置会应用到 Producer1Observer 的监控逻辑

### 通过热键操作 ROI

在 Docker 微信环境中使用热键快速配置 ROI：

- `Ctrl+Shift+R`: 进入 ROI 配置模式
- `Ctrl+Shift+S`: 保存当前 ROI 配置
- `Ctrl+Shift+C`: 取消 ROI 配置

## 代码风格规范

1. **类型提示**: 所有函数必须有类型提示
2. **文档字符串**: 使用 Google 风格的 docstrings
3. **日志记录**: 使用 `structlog` 进行结构化日志
4. **错误处理**: 使用 `core/exceptions.py` 中的自定义异常
5. **异步编程**: I/O 操作使用 `async/await`

```python
import structlog

logger = structlog.get_logger()

async def process_message(message: RawMessage) -> dict:
    """处理微信消息。

    Args:
        message: 来自微信的原始消息

    Returns:
        处理结果字典

    Raises:
        MessageValidationError: 消息格式无效时
    """
    logger.info("处理消息", sender=message.sender)
    # 实现代码
    return {"status": "success"}
```

## 测试策略

- **单元测试**: `tests/unit/` - 测试单个组件
- **集成测试**: `tests/integration/` - 测试服务交互
- **工作流测试**: `tests/workflows/` - 测试 LangGraph 工作流

```bash
# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=core --cov-report=html

# 生成 HTML 测试报告（使用 pytest-html）
pytest --html=report.html --self-contained-html
```

### 测试框架说明

- **pytest**: 主要测试框架
- **pytest-html**: 生成 HTML 测试报告
- **numpy**: 用于视觉测试（创建测试图像）
- **pytest-asyncio**: 异步测试支持

### 测试修复记录

**test_producer_service.py 修复：**
1. 修复了 ChangeDetector 测试方法中错误的阈值检查（50 → 0.05）
2. 修复了 detect_changes 返回值检查（从 len() 改为直接检查布尔值）
3. 修复了 MessageTypeClassifier 测试方法中错误的输入类型（字符串 → numpy 图像）
4. 修复了 MessageTypeClassifier 返回值断言（从字典 → 字符串）
5. 添加了 pytest-html 依赖支持

## Docker 服务

### 微信沙盒（单实例）
- **端口**: 6080 (noVNC), 5900 (VNC), 8000 (生产者服务)
- **使用**: 通过浏览器访问 http://localhost:6080 操作微信
- **管理**: `docker start/stop wechat-sandbox`

### 微信沙盒（多实例）
- **端口映射**:
  - 实例 1: 8001 (API), 6081 (noVNC), 5901 (VNC)
  - 实例 2: 8002 (API), 6082 (noVNC), 5902 (VNC)
  - 实例 3: 8003 (API), 6083 (noVNC), 5903 (VNC)
- **使用**: 通过不同的 noVNC 端口访问不同的微信实例
- **管理**: 使用 `docker-compose.multi.yml` 配置文件

**多实例部署命令：**
```bash
# 启动多实例
docker-compose -f docker-compose.multi.yml up -d

# 访问不同实例
# 实例 1: http://localhost:6081
# 实例 2: http://localhost:6082
# 实例 3: http://localhost:6083
```

### Ollama
- **端口**: 11434
- **API**: http://localhost:11434/api/tags
- **模型**: qwen3-vl-8b, qwen3-embedding-4b, qwen3-72b

### Redis
- **端口**: 6379
- **用途**: 消息队列和状态缓存

## Web UI 界面

### 访问方式

1. **noVNC 浏览器访问**: http://localhost:6080（单实例）或 http://localhost:6081-6083（多实例）
2. **Web UI 界面**: http://localhost:8000/static/index.html

### 功能模块

1. **VNC 集成**
   - 通过 noVNC 在浏览器中远程访问 Docker 中的微信界面
   - 支持完整的微信操作（扫码登录、发送消息等）
   - 实时屏幕同步

2. **ROI 配置面板**
   - 可视化配置监控区域
   - 拖拽选择 ROI 区域
   - 保存和管理多个 ROI 配置

3. **状态监控**
   - 实时显示生产者服务状态
   - 消息队列长度监控
   - 屏幕检测状态

4. **消息流显示**
   - 实时展示捕获的消息
   - 消息类型和内容预览
   - 消息时间戳和发送者信息

### API 端点

- `GET /health`: 健康检查
- `GET /status`: 服务状态
- `GET /messages`: 消息流（SSE）
- `POST /roi`: 更新 ROI 配置
- `POST /start`: 启动生产者服务
- `POST /stop`: 停止生产者服务

## 性能优化建议

1. **连接池复用**: 为 Ollama 和 API 调用复用 HTTP 客户端
2. **异步操作**: 使用 `asyncio` 提高并发消息处理能力
3. **Redis 缓存**: 缓存常用查询（嵌入向量、RAG 结果）
4. **批量处理**: 将多个消息分组进行批量分析
5. **多实例部署**: 使用多实例 Docker 部署支持多用户/多群组场景

## 安全注意事项

1. **切勿提交** `.env` 文件（已在 `.gitignore` 中）
2. **API 密钥**: 所有密钥使用环境变量
3. **输入验证**: 在所有节点中验证用户输入
4. **Docker 隔离**: 使用 Docker 网络隔离服务
5. **VNC 密码**: 生产环境必须设置强密码

## 故障排查

**容器无法启动：**
```bash
docker ps -a                    # 检查容器状态
docker logs wechat-sandbox       # 查看日志
docker inspect wechat-sandbox   # 检查配置
```

**工作流执行失败：**
```bash
# 检查 Ollama
curl http://localhost:11434/api/tags

# 检查 Redis
redis-cli ping

# 检查编排器日志
# (查看运行 uvicorn 的终端输出)
```

**模型加载错误：**
```bash
# 验证模型已拉取
docker exec -it ollama ollama list

# 重新拉取
docker exec -it ollama ollama pull qwen3-vl-8b
```

**VNC 连接失败：**
```bash
# 检查 VNC 服务状态
docker exec -it wechat-sandbox ps aux | grep vnc

# 重启 VNC 服务
docker restart wechat-sandbox
```

**Redis 连接失败：**
```bash
# 检查 Redis 容器状态
docker ps | grep redis

# 检查 Redis 日志
docker logs redis

# 测试连接
redis-cli -h localhost ping
```

## 主要依赖包

- `langgraph>=0.0.50` - 工作流编排
- `langchain>=0.1.0` - AI 框架
- `fastapi>=0.104` - API 框架
- `pydantic>=2.0` - 数据验证
- `pydantic-settings` - 配置管理
- `structlog` - 结构化日志
- `docker` - 容器管理
- `redis` - 消息队列
- `chromadb` - 向量数据库
- `openpyxl` - Excel 操作
- `python-docx` - Word 操作
- `pytest` - 测试框架
- `pytest-html` - HTML 测试报告
- `numpy` - 数值计算（用于视觉测试）

## 参考资源

- **LangGraph 文档**: https://python.langchain.com/docs/langgraph
- **Ollama 文档**: https://ollama.ai/docs
- **FastAPI 文档**: https://fastapi.tiangolo.com
- **项目 README**: 参见 README.md 了解安装说明
- **智能体架构**: 参见 agent.md 了解详细架构

## 快速参考

### 启动所有服务（单实例）：
```bash
docker-compose up -d
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

### 启动所有服务（多实例）：
```bash
docker-compose -f docker-compose.multi.yml up -d
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

### MonitorAgent 控制：
```python
from agents.monitor_agent import MonitorAgent

agent = MonitorAgent()
await agent.start()  # 开始监控
agent.stop()         # 停止监控
```

### 手动触发工作流：
```bash
curl -X POST http://localhost:8000/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"sender": "测试", "content": "测试消息", "message_type": "text"}'
```

### 检查工作流状态：
```bash
curl http://localhost:8000/workflow/status
```

### 访问微信界面：
```bash
# 单实例
http://localhost:6080

# 多实例实例 1
http://localhost:6081
# 多实例实例 2
http://localhost:6082
# 多实例实例 3
http://localhost:6083
```

## 给 Claude 的提示

在使用此代码库时：

1. **修改前先阅读现有代码** - 这是一个复杂的系统，组件间相互依赖
2. **理解数据流** - 消息在节点间流动，每步更新状态
3. **测试工作流更改** - 提交前使用 API 端点测试
4. **检查配置** - 许多行为在 `settings.yaml` 或 `.env` 中配置
5. **监控日志** - 使用 structlog 输出调试问题
6. **遵循异步模式** - 大多数 I/O 操作都是异步的
7. **注意多实例配置** - 生产环境需要使用 `docker-compose.multi.yml`
8. **理解 ROI 配置** - 监控区域配置影响消息捕获的准确性

项目在某些文件中**使用中文注释**，并支持中文文本处理（微信消息）。使用的 AI 模型（Qwen3）是针对中文优化的模型。

### 项目特点

1. **多模态处理**: 同时处理文本和图片消息
2. **有状态工作流**: 使用 LangGraph 维护对话和任务状态
3. **本地 AI**: 使用 Ollama 本地部署，无需外部 API 调用
4. **容器化隔离**: 微信运行在独立的 Docker 容器中
5. **多实例部署**: 支持生产级别的多用户/多群组场景
6. **浏览器访问**: 通过 noVNC 在浏览器中远程操作微信
7. **RAG 增强**: 结合向量数据库提供上下文感知
8. **中文优化**: 针对中文场景的模型和配置
9. **Web UI 界面**: 提供可视化的配置和监控界面

### 典型工作流程

1. 微信沙盒容器（单实例或多实例）捕获群消息
2. 生产者服务通过 SSE 推送消息到 API 服务器
3. MonitorAgent 接收消息并触发工作流
4. LangGraph 工作流依次执行各节点：
   - 多模态节点分析消息内容（文本+图片）
   - 状态跟踪节点判断任务进度
   - 如果任务完成，文档节点生成报告
5. 更新 Excel 台账和生成 Word 报告

### 关键设计模式

- **状态机模式**: LangGraph 管理工作流状态转换
- **生产者-消费者模式**: Redis 消息队列解耦组件
- **策略模式**: 不同消息类型使用不同的处理策略
- **模板方法模式**: 文档生成使用 Jinja2 模板
- **单例模式**: 配置和连接池使用单例
- **观察者模式**: Producer1Observer 监控屏幕变化
- **工厂模式**: 根据消息类型创建不同的处理器

### 性能指标

- 消息处理延迟: < 3秒（不含文档生成）
- 并发处理能力: 支持多个工作流并行执行
- 多实例支持: 默认支持 3 个独立微信实例
- 内存占用: Ollama 模型加载约需 8-16GB RAM
- 存储需求: ChromaDB 向量存储约 100-500MB（取决于知识库大小）
- 屏幕检测延迟: < 500ms（ChangeDetector）

### 扩展方向

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
