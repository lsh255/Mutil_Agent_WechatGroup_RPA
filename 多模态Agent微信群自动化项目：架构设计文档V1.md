1. 概述
1.1 项目愿景
构建一个端到端的自动化系统，通过智能体（Agent）协作，自动监控指定微信工作群的消息，理解图文混合内容，跟踪任务状态，并最终自动更新本地台账（Excel）和生成工作报告，解决人工整理效率低下、易出错的痛点。

1.2 核心设计原则
解耦与模块化：系统功能由独立的、单一职责的Agent实现，通过标准协议通信。

可观测性：每个组件均暴露健康状态与性能指标，支持日志聚合。

演进式架构：通过抽象层（如IMessageSource）设计，确保从个人微信沙盒向企业微信API的迁移路径清晰、成本最低。

沙盒化与稳定性：将高度依赖图形界面和外部环境的组件（微信客户端）容器化，形成隔离、可控的“消息源”。

2. 架构总览
系统采用 “协调者-工作者” (Orchestrator-Worker) 模式的分层多Agent架构。所有Agent通过中央消息总线进行异步、松耦合通信，数据格式遵循统一消息协议。
┌─────────────────────────────────────────────────────────────────────┐
│                        Orchestrator (协调中心)                       │
│                      (FastAPI + 简易管理界面)                        │
├─────────────────────────────────────────────────────────────────────┤
│                  Message Bus / Event Stream (消息总线)                │
│                     (Redis Streams / PubSub)                         │
├──────────────┬──────────────┬────────────────┬──────────────┐
│              │              │                │              │
│  Monitor     │ Multimodal   │  StateManager  │  Document    │
│   Agent      │   Agent      │     Agent      │    Agent     │
│ (消息采集)   │ (多模态理解)  │  (状态管理)    │ (文档执行)   │
└──────────────┴──────────────┴────────────────┴──────────────┘
         │                                                      │
         ▼                                                      ▼
┌─────────────────┐                                    ┌─────────────────┐
│ WeChat Sandbox  │                                    │ Local File      │
│  (微信沙盒容器)  │                                    │ System & Excel  │
└─────────────────┘                                    └─────────────────┘
3. 架构详述
3.1 协调层：Orchestrator
职责：系统的启动入口与管家。负责加载配置、初始化并启动所有Agent、提供管理界面、监控全局状态。

关键设计：

提供RESTful API和Web管理界面。

管理界面直接集成微信沙盒的noVNC登录入口。

通过调用各Agent的健康检查接口进行心跳监控。

扩展点：未来可拆分出独立的 SchedulerAgent 负责复杂定时与工作流编排。

3.2 通信层：消息总线与协议
消息总线：

选型：Redis（Streams用于持久化消息流，PubSub用于轻量级事件广播）。

作用：作为Agent间的“神经网络”，实现完全解耦的异步通信。

统一消息协议：

格式：采用Pydantic BaseModel定义的JSON Schema，确保类型安全。

核心字段：

class AgentMessage(BaseModel):
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    source: str  # 发出此消息的Agent名称
    type: str    # 消息类型，如 `raw_message`, `classified_task`, `state_updated`
    payload: dict  # 消息主体，内容因`type`而异
    context: dict  # 上下文，如 user_id, group_id, session_id, trace_id
    # 预留扩展字段，用于未来承载路由、优先级等信息
    extensions: dict = Field(default_factory=dict)
3.3 核心工作层：功能Agent
所有Agent均继承自一个抽象的 BaseAgent 类，实现 start(), stop(), health_check() 等标准方法。

Monitor Agent

职责：管理“消息源”，将原始数据转换为标准协议消息。

核心抽象 IMessageSource：
class IMessageSource(ABC):
    @abstractmethod
    async def start(self): ...
    @abstractmethod
    async def stop(self): ...
    @abstractmethod
    async def subscribe(self, callback: Callable[[dict], None]): ...
当前实现 WeChatContainerSource：管理微信沙盒Docker容器，调用其内部服务的SSE流，实现数据流式获取。

未来扩展：实现 EnterpriseWeChatAPISource，通过企业微信官方API获取消息，即可无缝切换。

Multimodal Agent

职责：订阅原始消息，调用多模态大模型进行消息分类、内容理解、结构化信息提取。

工作流：

接收 type=raw_message 的消息。

调用本地部署的 Qwen-VL 模型进行图文理解。

结合 RAG 系统，从业务知识库（LanceDB）检索增强上下文。

发布 type=classified_task 的消息，其 payload 中包含结构化数据（如 task_type, user, content_summary, step 等）。

StateManager Agent

职责：维护有状态的任务上下文，跟踪如“作业前-中-后”等序列的完整性。

核心：一个基于规则引擎或轻量级状态机（如transitions库）的处理器。为每个 (user, task) 维护状态，并在状态转换完成时发布 type=state_completed 的事件消息。

Document Agent

职责：订阅状态完成事件，执行文件系统操作。

功能：

使用 openpyxl 更新Excel台账。

使用 python-docx 和 Jinja2 模板引擎生成Word日报。

设计：文件操作封装在 FileRepository 仓储类中，接口与实现分离，便于未来迁移至云存储。
3.4 基础设施层
微信沙盒容器：

技术：Docker + noVNC + FastAPI。

镜像：基于 jlesage/baseimage-gui，集成微信客户端、Python及生产者服务。

数据流：容器内生产者服务通过SSE暴露消息流；宿主机通过映射端口访问noVNC Web界面进行扫码登录。

AI模型服务：

部署：Ollama 本地部署微调后的 Qwen3-VL 模型。

向量数据库：LanceDB，存储业务知识库的嵌入向量。

存储：

配置：YAML 文件 + pydantic-settings 管理，支持环境变量覆盖。

状态与缓存：Redis。

持久化：本地文件系统（结构化日志、生成的文档）。
4. 关键数据流
用户登录：管理员在 Orchestrator 界面点击“登录微信”，跳转至沙盒noVNC页面完成扫码。登录状态持久化至宿主机卷。

消息处理：
微信消息 -> 沙盒容器捕获 -> Monitor Agent (转换) -> [Bus: raw_message]
-> Multimodal Agent (理解) -> [Bus: classified_task]
-> StateManager Agent (跟踪) -> [Bus: state_updated]
-> Document Agent (执行) -> 更新Excel/生成Word
系统监控：各Agent暴露/metrics端点（Prometheus格式），Orchestrator聚合展示。
5. 扩展性设计
水平扩展：无状态的Agent（如Multimodal）可启动多个实例，通过消息总线的消费者组实现负载均衡。

垂直扩展：

更换消息源：实现新的 IMessageSource，系统即可支持新的平台（如钉钉、飞书）。

增强AI能力：替换 Multimodal Agent 中调用的模型服务地址即可升级模型。

接入外部工具：通过开发新的、具有特定能力的Agent（如 EmailAgent）并订阅相关事件，轻松扩展系统功能边界。
