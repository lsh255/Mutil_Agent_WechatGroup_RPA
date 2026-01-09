# 多模态Agent自动化项目：架构设计文档 (LangGraph版)

## 1. 概述

### 1.1 项目愿景

构建一个端到端的自动化系统，通过有状态的智能体工作流，自动监控指定微信工作群的消息，理解图文混合内容，跟踪任务状态，并最终自动更新本地台账（Excel）和生成工作报告，解决人工整理效率低下、易出错的痛点。

系统支持：
- **多实例部署**: 同时运行多个独立的微信实例，支持多用户/多群组场景
- **浏览器访问**: 通过 VNC/noVNC 在浏览器中远程访问微信界面
- **Web UI 管理**: 提供友好的 Web 界面进行 ROI 配置和状态监控
- **热键操作**: 支持通过热键快速配置监控区域

### 1.2 核心设计原则与范式变更

**从"多Agent消息总线"到"单一工作流"**：
- 系统核心驱动力由多个独立Agent通过消息总线异步协作，转变为一个由LangGraph管理的、有状态的工作流
- 工作流定义了固定的处理步骤（节点）和逻辑（边），状态在节点间线性传递，极大简化了协作复杂度和调试难度

**内聚的状态管理**：
- 原StateManager Agent的功能被内化为工作流State对象的一部分和条件边的逻辑
- 实现了状态与处理逻辑的统一管理

**工具化执行**：
- 原Document Agent等执行模块被重构为工作流节点可调用的标准化工具（Tool）
- 通过LangChain的Tool Calling机制集成

**维持解耦与可观测性**：
- 工作流之外的组件（如微信沙盒）仍保持服务化接口
- 系统关键节点继续暴露可观测性数据

## 2. 架构总览

系统采用 "中心化工作流引擎 + 外围服务" 的混合架构。LangGraph工作流是处理核心，负责从消息理解到文档生成的全过程；微信沙盒、向量数据库等作为支撑服务。

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层                                                     │
│                                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────────────┐  │
│  │   浏览器 noVNC       │  │   Web UI 界面        │  │   Orchestrator API          │  │
│  │   (远程微信界面)      │  │   (ROI配置/监控)     │  │   (工作流触发/管理)          │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              服务层                                                         │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                   LangGraph Workflow Engine (工作流引擎)                           │  │
│  │                                                                                  │  │
│  │  ┌─────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────┐            │  │
│  │  │ Monitor │────▶│ Multimodal │────▶│ StateTracker │────▶│ Document │            │  │
│  │  │  Node   │     │    Node    │◀───▶│    Node      │     │   Node   │            │  │
│  │  └─────────┘     └────────────┘     └──────────────┘     └──────────┘            │  │
│  │       │                  │                    │                │                  │  │
│  │       └──────────────────┼────────────────────┼────────────────┘                  │  │
│  │                          │                    │                                   │  │
│  │                    ┌─────▼────┐         ┌─────▼────┐                              │  │
│  │                    │ Shared   │         │ Conditio-│                              │  │
│  │                    │  State   │         │ nal Edge │                              │  │
│  │                    └──────────┘         └──────────┘                              │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                           │                              │                              │
│                           │ (状态读取/更新)                │ (工具调用)                  │
│                           ▼                              ▼                              │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────┐                │
│  │        支撑服务层                │    │        工具层               │                │
│  │                                 │    │                             │                │
│  │  ┌─────────────────┐  ┌──────┐ │    │  ┌──────┐  ┌────────────┐ │                │
│  │  │ WeChat Sandbox  │  │Chroma│ │    │  │ Excel│  │   Word     │ │                │
│  │  │  (Docker容器)    │  │Vector│ │    │  │ Tool │  │ Report Tool│ │                │
│  │  │                 │  │ Store │ │    │  │      │  │            │ │                │
│  │  │ ┌───────────┐  │  │      │ │    │  └──────┘  └────────────┘ │                │
│  │  │ │ FastAPI   │  │  │      │ │    └─────────────────────────────┘                │
│  │  │ │ + SSE     │  │  │      │ │                                             │        │
│  │  │ │ Producer  │  │  │      │ │                                             │        │
│  │  │ └───────────┘  │  └──────┘ │                                             │        │
│  │  └─────────────────┘           │                                             │        │
│  │           │               │     │                                             │        │
│  │           └───────────────┼─────┘                                             │        │
│  │                           │ (RAG检索)                                           │        │
│  │                    ┌──────▼──────┐                                             │        │
│  │                    │ Ollama      │                                             │        │
│  │                    │ (Qwen3-VL & │                                             │        │
│  │                    │  Embedding) │                                             │        │
│  │                    └─────────────┘                                             │        │
│  └─────────────────────────────────┘                                               │        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              数据层                                                         │
│                                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Redis Queue │  │ ChromaDB    │  │ Excel 台账  │  │ Word 报告   │  │ 微信用户数据 │  │
│  │ 消息队列    │  │ 向量数据库  │  │             │  │             │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 多实例部署架构

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              多实例部署架构                                               │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         Docker Host                                               │  │
│  │                                                                                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │ WeChat Instance │  │ WeChat Instance │  │ WeChat Instance │                  │  │
│  │  │       1         │  │       2         │  │       3         │                  │  │
│  │  │                 │  │                 │  │                 │                  │  │
│  │  │ API: 8001       │  │ API: 8002       │  │ API: 8003       │                  │  │
│  │  │ VNC: 5901       │  │ VNC: 5902       │  │ VNC: 5903       │                  │  │
│  │  │ noVNC: 6081     │  │ noVNC: 6082     │  │ noVNC: 6083     │                  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │  │
│  │           │                    │                    │                            │  │
│  │           └────────────────────┼────────────────────┘                            │  │
│  │                                │                                                 │  │
│  │  ┌─────────────────────────────▼───────────────────────────────────────────────┐  │  │
│  │  │                         Shared Redis (消息队列/状态存储)                      │  │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                         Orchestrator Service (工作流触发)                     │  │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                         Ollama Service (AI模型服务)                          │  │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                         ChromaDB Service (向量数据库)                         │  │  │
│  │  └────────────────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. 架构详述

### 3.1 用户交互层

#### 3.1.1 VNC/noVNC 远程访问

**功能**: 在浏览器中远程访问 Docker 容器内的微信界面

**技术实现**:
- 使用 `jlesage/baseimage-gui` 镜像提供 VNC/noVNC 支持
- noVNC 服务默认运行在 6080 端口
- VNC 服务运行在 5900 端口
- 支持密码认证（通过环境变量配置）

**访问方式**:
- 单实例: `http://localhost:6080`
- 多实例: `http://localhost:6081/6082/6083`

**优势**:
- 无需安装 VNC 客户端
- 跨平台支持（Windows、Mac、Linux）
- 便于远程管理和调试

#### 3.1.2 Web UI 界面

**功能**: 提供友好的 Web 界面进行系统管理和配置

**主要模块**:
1. **ROI 配置面板**: 在预览图像上拖拽选择监控区域
2. **服务状态监控**: 显示 Producer Service、队列状态、检测状态
3. **消息流显示**: 实时显示捕获的微信消息
4. **热键说明**: 显示可用的热键操作

**技术实现**:
- 原生 JavaScript + Canvas API
- Fetch API 进行状态轮询
- Server-Sent Events (SSE) 接收实时消息

**API 端点**:
- `GET /health`: 健康检查
- `GET /status`: 获取服务状态
- `GET /roi`: 获取当前 ROI 配置
- `POST /roi`: 更新 ROI 配置
- `GET /screenshot`: 获取屏幕截图
- `GET /messages/stream`: SSE 消息流

#### 3.1.3 Orchestrator API

**功能**: 提供工作流管理和触发的 REST API

**主要端点**:
- `POST /workflow/trigger`: 触发新的工作流实例
- `GET /workflow/{workflow_id}/state`: 获取工作流状态
- `GET /workflow/{workflow_id}/status`: 获取工作流执行状态
- `POST /workflow/{workflow_id}/cancel`: 取消工作流

### 3.2 协调与接口层

#### 3.2.1 Orchestrator Service

**职责**: 系统的HTTP入口和运维面板

**关键功能**:
- 接收来自微信沙盒的触发请求
- 启动新的LangGraph工作流实例
- 提供管理界面（工作流状态、日志、配置）
- 工作流生命周期管理

**关键设计**:
- 核心是一个LangGraph工作流的包装器（Wrapper）和触发器
- 当收到新消息时，初始化一个工作流State并调用 `workflow.invoke()`
- 支持工作流检查点（Checkpoint）和状态持久化

#### 3.2.2 API 服务器生命周期管理

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

### 3.3 核心处理层：LangGraph工作流

这是系统的大脑和中枢神经，取代了原先松散的Agent集群。

#### 3.3.1 工作流状态（State）

一个统一的、强类型的TypedDict（如AgentState），作为数据在整个工作流中流动的载体。

**包含字段**:
- `raw_message`: 来自微信的原始消息（输入）
- `multimodal_analysis`: 多模态分析结果
- `task_status`: 任务状态（如 "waiting_mid"）
- `document_updates`: 需要执行的文档更新指令（输出）
- `messages`: 用于串联对话的消息记录

**设计意义**:
- 状态对象取代了跨Agent的消息协议
- 使数据流和当前上下文一目了然

#### 3.3.2 工作流节点（Nodes）

节点是工作流中的处理单元，对应原Agent的核心功能，但彼此直接共享内存状态，而非通过网络通信。

**Monitor Node**:
- 适配器节点
- 作为工作流入口，接收来自外部Monitor Agent服务的标准化消息输入
- 将消息载入工作流State的 `raw_message` 字段

**Multimodal Node**:
- 从State中读取 `raw_message`（含截图和文本）
- 调用Ollama中的Qwen3-VL模型进行理解和分类
- 调用Tool：通过Qwen3-Embedding-4B与Chroma进行RAG检索，增强业务上下文
- 将结构化结果写回State的 `multimodal_analysis` 字段

**StateTracker Node**:
- 核心逻辑节点
- 读取 `multimodal_analysis`
- 基于业务规则（如匹配"作业前、中、后"），更新State中的 `task_status`
- 包含条件判断逻辑，决定工作流下一步走向

**Document Node**:
- 工具调用节点
- 当任务状态满足完成条件时，此节点被激活
- 根据State中的数据，调用相应的Excel Tool或Word Report Tool执行更新
- 将执行结果写回State

#### 3.3.3 工作流边（Edges）与条件路由

**边定义节点的执行顺序**（A -> B -> C）

**条件边**: 由StateTracker Node的返回值决定
- 若任务未完成，则工作流结束（等待下次触发）
- 若完成，则流向Document Node

**条件路由示例**:

```python
def should_generate_document(state: AgentState) -> str:
    """判断是否应该生成文档"""
    analysis = state.get("multimodal_analysis", {})
    if any(signal in analysis.get("text", "") for signal in ["complete", "end", "report"]):
        return "yes"
    return "no"

# 在工作流中添加条件边
workflow.add_conditional_edges(
    "state_tracker",
    should_generate_document,
    {
        "yes": "document",
        "no": END
    }
)
```

### 3.4 工具层

**定义**: 将被复用的、对外的操作（如读写文件、调用API）封装为LangChain Tool

**示例**:
- `UpdateExcelTool`: 更新Excel台账
- `GenerateReportTool`: 生成Word报告
- `RAGRetrievalTool`: 检索相关业务知识

**特点**:
- 在工作流节点中被声明和调用
- 实现了执行能力的模块化和标准化
- 支持工具的参数验证和错误处理

### 3.5 支撑服务层

#### 3.5.1 微信沙盒容器

**架构**: 独立的Docker化服务

**核心组件**:
1. **Linux微信**: 运行在容器内的Deepin Wine微信
2. **虚拟显示**: Xvfb 提供虚拟显示服务器（1920x1080 分辨率）
3. **桌面环境**: Fluxbox 轻量级窗口管理器
4. **生产者服务**: FastAPI服务，负责消息捕获和分发
5. **屏幕检测**: ChangeDetector 检测屏幕变化
6. **消息分类**: MessageTypeClassifier 识别消息类型
7. **VNC服务**: noVNC + x11vnc 提供远程访问能力

**Monitor Agent服务**:
- 管理沙盒生命周期（启动、停止、重启）
- 从SSE流中读取数据
- 向Orchestrator发起HTTP请求，触发工作流

**远程访问**:
- **noVNC Web界面**: 通过浏览器访问（端口 6080），密码默认为 wechat123
- **VNC客户端**: 支持 RealVNC、TightVNC 等客户端（端口 5900），密码默认为 wechat123

**数据流**:
```
微信消息 → 屏幕截图 → ChangeDetector检测 → 消息捕获 → Redis队列 → Monitor Agent → Orchestrator → LangGraph工作流
```

#### 3.5.2 AI与知识库服务

**Ollama**:
- 提供Qwen3-VL和Qwen3-Embedding-4B模型服务
- 本地部署，保护数据隐私
- 支持批量推理和流式输出

**Chroma向量数据库**:
- 存储业务知识嵌入
- 与LangChain生态集成
- 在Multimodal Node中被调用以完成RAG检索

**状态持久化（可选）**:
- LangGraph支持将工作流State检查点（Checkpoint）保存至数据库（如Redis）
- 实现长周期、可中断重启的复杂会话

## 4. 关键数据流（LangGraph范式）

### 4.1 消息捕获与工作流触发

```
微信消息 
  → 沙盒容器捕获 
  → ChangeDetector检测变化 
  → MessageTypeClassifier分类 
  → Producer Service写入Redis队列 
  → Monitor Agent从Redis读取 
  → (HTTP Post) Orchestrator 
  → 创建并invoke新的工作流实例
```

### 4.2 工作流内部执行

```
工作流开始 (State初始化)
    ↓
Monitor Node: 将原始消息载入State.raw_message
    ↓
Multimodal Node: 分析 & RAG → 结果写入State.multimodal_analysis
    ↓
StateTracker Node: 更新状态，并决定下一步
    ├── 若任务未完成 → 工作流结束（等待下次触发）
    └── 若任务完成 → 执行 Document Node
            ↓
        Document Node: 调用工具，更新文档 → 结果写入State
            ↓
        工作流结束
```

### 4.3 状态持久化

每个工作流实例的State可被自动保存为检查点。当同一任务的下一条消息触发新工作流时，可从检查点恢复状态，实现跨消息的连续对话和跟踪。

**状态存储示例**:
```python
# 使用Redis作为状态存储后端
workflow = create_workflow()
app = workflow.compile(checkpointer=RedisCheckpointSaver(redis_conn))
```

## 5. 扩展性设计

### 5.1 工作流本身的扩展

增加新节点或修改边逻辑即可添加新功能：
- 新增Notification Node用于发送通知
- 新增Validation Node用于数据验证
- 新增Retry Node用于失败重试

### 5.2 替换消息源

Monitor Node是输入适配器。未来迁移企业微信：
- 只需改造外部的Monitor Agent服务
- 使其从企业微信API拉取消息并触发工作流
- 工作流内部无需任何修改

### 5.3 多群组与并行化

每个群聊或任务由独立的工作流实例处理，其State相互隔离。
- LangGraph运行时支持高并发执行多个工作流实例
- 支持多实例Docker部署（默认3个实例）

### 5.4 工具生态集成

可轻松集成更多的LangChain Tool：
- 搜索工具（Google Search、Bing Search）
- 计算工具（Calculator、Python REPL）
- 文件操作工具（File I/O、Cloud Storage）
- 通知工具（Email、Slack、DingTalk）

### 5.5 水平扩展

**Redis集群**: 支持大规模消息队列
**Ollama分布式**: 支持多个Ollama实例负载均衡
**ChromaDB集群**: 支持向量数据库的水平扩展
**容器编排**: 支持Kubernetes部署

## 6. 与技术栈的对应关系

本架构是所选技术栈的具象化体现：

- **LangGraph**: 实现了本架构的核心工作流引擎
- **Chroma + Qwen3-Embedding-4B**: 作为Multimodal Node中的检索增强组件
- **LangChain & Tools**: 提供了节点与模型、工具、向量数据库交互的标准方式
- **FastAPI & Docker**: 构成了外围的服务化与容器化基础设施
- **Redis**: 实现消息队列和状态持久化
- **noVNC/VNC**: 实现浏览器远程访问
- **OpenCV**: 实现屏幕变化检测和图像处理

## 7. 安全与权限

### 7.1 访问控制

- VNC密码认证
- API接口Token认证
- Web UI用户登录认证（可选）

### 7.2 数据隔离

- 多实例部署时，每个实例的数据完全隔离
- Redis队列使用不同的key前缀
- ChromaDB使用不同的collection

### 7.3 敏感信息保护

- 所有敏感配置使用环境变量
- 禁止在代码中硬编码密码和密钥
- 日志输出脱敏处理

## 8. 监控与运维

### 8.1 日志管理

- 使用 structlog 生成结构化日志
- 日志级别：DEBUG、INFO、WARNING、ERROR
- 支持日志轮转和远程日志收集

### 8.2 健康检查

- API服务健康检查端点：`GET /health`
- 容器健康检查（Docker healthcheck）
- Redis连接检查

### 8.3 指标监控

- 消息处理延迟
- 队列长度
- 工作流执行次数
- 错误率
- 资源使用率（CPU、内存、磁盘）

### 8.4 告警机制

- 服务异常告警
- 队列积压告警
- 工作流失败告警
- 资源使用超限告警

## 9. 性能优化

### 9.1 消息处理优化

- 异步I/O处理
- 批量消息处理
- 并行工作流执行

### 9.2 AI推理优化

- 模型量化（Qwen3-VL支持INT8量化）
- 批量推理
- 缓存常用结果

### 9.3 数据库优化

- Redis连接池
- ChromaDB索引优化
- 向量检索优化（使用HNSW索引）

## 10. 部署策略

### 10.1 开发环境

- 单实例Docker部署
- 本地Ollama服务
- 本地ChromaDB
- 本地Redis

### 10.2 生产环境

- 多实例Docker部署（3个实例）
- 独立Ollama服务容器
- 独立ChromaDB容器
- 独立Redis容器（支持集群）
- 容器编排（Docker Compose或Kubernetes）

### 10.3 高可用部署

- Redis Sentinel或Redis Cluster
- Ollama多实例负载均衡
- ChromaDB集群
- 工作流检查点持久化
- 自动故障转移

## 11. 镜像构建与远程部署

### 11.1 镜像构建架构

微信沙盒采用分层 Docker 构建策略，构建依赖文件独立存储：

```
wechat_sandbox/
├── Dockerfile
├── build/
│   ├── fonts-noto-cjk_20240730+repack1-1_all.deb  # Noto CJK 字体包
│   └── WeChatLinux_x86_64.deb  # Linux 微信客户端安装包
├── api_server.py
├── producer_service/
│   ├── queue_manager.py
│   ├── producer1_observer.py
│   └── producer2_content_fetcher.py
└── static/
    └── index.html
```

**构建分层策略**:
1. 基础层: `jlesage/baseimage-gui:debian-11`
2. 依赖层: 安装字体包和系统依赖
3. 应用层: 安装微信客户端和 Python 环境
4. 代码层: 复制应用代码和服务脚本

### 11.2 GitHub Container Registry (ghcr.io) 部署

#### 11.2.1 推送流程

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         镜像推送流程                                                     │
│                                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │ 本地构建      │───▶│ 标记镜像      │───▶│ 登录 ghcr.io │───▶│ 推送镜像      │        │
│  │              │    │              │    │              │    │              │        │
│  │ wechat-      │    │ ghcr.io/     │    │ GitHub Token │    │ ghcr.io/     │        │
│  │ sandbox:     │    │ lsh255/      │    │ 认证         │    │ lsh255/      │        │
│  │ latest       │    │ wechat-      │    │              │    │ wechat-      │        │
│  │              │    │ sandbox:     │    │              │    │ sandbox:     │        │
│  │              │    │ latest       │    │              │    │ latest       │        │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 11.2.2 推送步骤

**步骤 1: 创建 GitHub Personal Access Token**

1. 访问: https://github.com/settings/tokens
2. 生成新 token (classic)
3. 选择权限: `write:packages`, `read:packages`, `delete:packages`
4. 复制 token（仅显示一次）

**步骤 2: 登录 ghcr.io**

```bash
docker login ghcr.io
# 用户名: GitHub 用户名
# 密码: GitHub Personal Access Token
```

**步骤 3: 标记并推送**

```bash
docker tag wechat-sandbox:latest ghcr.io/lsh255/wechat-sandbox:latest
docker push ghcr.io/lsh255/wechat-sandbox:latest
```

### 11.3 远程镜像部署架构

#### 11.3.1 部署场景

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         远程镜像部署场景                                                 │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         ghcr.io (远程镜像仓库)                                      │  │
│  │                                                                                  │  │
│  │  ghcr.io/lsh255/wechat-sandbox:latest                                            │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                                  │
│                                      │ 拉取镜像                                           │
│                                      ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                         部署环境                                                   │  │
│  │                                                                                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │  │
│  │  │  测试环境       │  │ 生产单服务      │  │ 生产多服务      │                  │  │
│  │  │                 │  │                 │  │                 │                  │  │
│  │  │ docker-compose  │  │ docker-compose  │  │ docker-compose  │                  │  │
│  │  │ .yml            │  │ .yml            │  │ .multi.yml      │                  │  │
│  │  │                 │  │                 │  │                 │                  │  │
│  │  │ image: ghcr.io/ │  │ image: ghcr.io/ │  │ image: ghcr.io/ │                  │  │
│  │  │       lsh255/   │  │       lsh255/   │  │       lsh255/   │                  │  │
│  │  │       wechat-   │  │       wechat-   │  │       wechat-   │                  │  │
│  │  │       sandbox:  │  │       sandbox:  │  │       sandbox:  │                  │  │
│  │  │       latest    │  │       latest    │  │       latest    │                  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### 11.3.2 配置示例

**docker-compose.yml (测试/生产单服务)**:

```yaml
services:
  wechat-sandbox:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox
    ports:
      - "8000:8000"
      - "5900:5900"
      - "6080:6080"
    volumes:
      - ./data/wechat_profile:/wechat/data
    environment:
      - VNC_PASSWORD=vnc123
```

**docker-compose.multi.yml (生产多服务)**:

```yaml
services:
  wechat-sandbox-1:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox-instance-1
    ports:
      - "8001:8000"
      - "5901:5900"
      - "6081:6080"

  wechat-sandbox-2:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox-instance-2
    ports:
      - "8002:8000"
      - "5902:5900"
      - "6082:6080"

  wechat-sandbox-3:
    image: ghcr.io/lsh255/wechat-sandbox:latest
    container_name: wechat-sandbox-instance-3
    ports:
      - "8003:8000"
      - "5903:5900"
      - "6083:6080"
```

### 11.4 部署优势

**一致性保证**:
- 所有环境使用完全相同的镜像
- 避免因本地构建差异导致的问题

**效率提升**:
- 无需在每台机器上重新构建
- 减少构建时间和资源消耗

**版本管理**:
- 支持多版本并存 (latest, v1.0, v2.0)
- 便于版本回滚和 A/B 测试

**运维简化**:
- 集中式镜像管理
- 便于权限控制和访问审计
