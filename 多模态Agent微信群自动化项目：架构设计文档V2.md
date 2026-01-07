多模态Agent自动化项目：架构设计文档 (LangGraph版)
1. 概述
1.1 项目愿景
构建一个端到端的自动化系统，通过有状态的智能体工作流，自动监控指定微信工作群的消息，理解图文混合内容，跟踪任务状态，并最终自动更新本地台账（Excel）和生成工作报告，解决人工整理效率低下、易出错的痛点。

1.2 核心设计原则与范式变更
从“多Agent消息总线”到“单一工作流”：系统核心驱动力由多个独立Agent通过消息总线异步协作，转变为一个由LangGraph管理的、有状态的工作流。工作流定义了固定的处理步骤（节点）和逻辑（边），状态在节点间线性传递，极大简化了协作复杂度和调试难度。

内聚的状态管理：原StateManager Agent的功能被内化为工作流State对象的一部分和条件边的逻辑，实现了状态与处理逻辑的统一管理。

工具化执行：原Document Agent等执行模块将被重构为工作流节点可调用的标准化工具（Tool），通过LangChain的Tool Calling机制集成。

维持解耦与可观测性：工作流之外的组件（如微信沙盒）仍保持服务化接口；系统关键节点继续暴露可观测性数据。

2. 架构总览
系统采用 “中心化工作流引擎 + 外围服务” 的混合架构。LangGraph工作流是处理核心，负责从消息理解到文档生成的全过程；微信沙盒、向量数据库等作为支撑服务。

text
┌─────────────────────────────────────────────────────────────────────────┐
│                        Orchestrator & API Gateway                        │
│                    (FastAPI, 提供管理界面与工作流触发接口)                 │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ (HTTP 触发)
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  LangGraph Workflow Engine (工作流引擎)                   │
│                                                                         │
│  ┌─────────┐     ┌────────────┐     ┌──────────────┐     ┌──────────┐  │
│  │ Monitor │────▶│ Multimodal │────▶│ StateTracker │────▶│ Document │  │
│  │  Node   │     │    Node    │◀───▶│    Node      │     │   Node   │  │
│  └─────────┘     └────────────┘     └──────────────┘     └──────────┘  │
│       │                  │                    │                │        │
│       └──────────────────┼────────────────────┼────────────────┘        │
│                          │                    │                         │
│                    ┌─────▼────┐         ┌─────▼────┐                    │
│                    │ Shared   │         │ Conditio-│                    │
│                    │  State   │         │ nal Edge │                    │
│                    └──────────┘         └──────────┘                    │
└─────────────────────────┬────────────────────────┬──────────────────────┘
                          │ (状态读取/更新)         │ (工具调用)
                          ▼                        ▼
┌─────────────────────────────────┐    ┌─────────────────────────────┐
│        支撑服务层                │    │        工具层               │
│                                 │    │                             │
│  ┌─────────────────┐  ┌──────┐ │    │  ┌──────┐  ┌────────────┐   │
│  │ WeChat Sandbox  │  │Chroma│ │    │  │ Excel│  │   Word     │   │
│  │  (微信沙盒容器)  │  │Vector│ │    │  │ Tool │  │ Report Tool│   │
│  │                 │  │ Store │ │    │  │      │  │            │   │
│  └─────────────────┘  └──────┘ │    │  └──────┘  └────────────┘   │
│           │               │     │    └─────────────────────────────┘
│           └───────────────┼─────┘
│                           │ (RAG检索)
│                    ┌──────▼──────┐
│                    │ Ollama      │
│                    │ (Qwen3-VL & │
│                    │  Embedding) │
│                    └─────────────┘
└─────────────────────────────────┘
3. 架构详述
3.1 协调与接口层
Orchestrator Service：

职责：系统的HTTP入口和运维面板。接收来自微信沙盒的触发请求，启动新的LangGraph工作流实例；提供管理界面。

关键设计：其核心是一个LangGraph工作流的包装器（Wrapper）和触发器。当收到新消息时，它初始化一个工作流State并调用workflow.invoke()。

3.2 核心处理层：LangGraph工作流
这是系统的大脑和中枢神经，取代了原先松散的Agent集群。

工作流状态（State）：

一个统一的、强类型的TypedDict（如AgentState），作为数据在整个工作流中流动的载体。

包含字段：raw_message（输入）, multimodal_analysis, current_task_status, document_instructions, messages（对话历史）等。

设计意义：状态对象取代了跨Agent的消息协议，使数据流和当前上下文一目了然。

工作流节点（Nodes）：
节点是工作流中的处理单元，对应原Agent的核心功能，但彼此直接共享内存状态，而非通过网络通信。

Monitor Node：适配器节点。作为工作流入口，它不直接管理沙盒，而是接收来自外部Monitor Agent服务（管理沙盒）的标准化消息输入，并将其载入工作流State。

Multimodal Node：

从State中读取raw_message（含截图和文本）。

调用Ollama中的Qwen3-VL模型进行理解和分类。

调用Tool：通过Qwen3-Embedding-4B与Chroma进行RAG检索，增强业务上下文。

将结构化结果写回State的multimodal_analysis字段。

StateTracker Node：

核心逻辑节点。读取multimodal_analysis。

基于业务规则（如匹配“作业前、中、后”），更新State中的current_task_status。

此节点包含条件判断逻辑，决定工作流下一步走向。

Document Node：

工具调用节点。当任务状态满足完成条件时，此节点被激活。

根据State中的数据，调用相应的Excel Tool或Word Report Tool执行更新。

将执行结果写回State。

工作流边（Edges）与条件路由：

边定义了节点的执行顺序（A -> B -> C）。

条件边：由StateTracker Node的返回值决定。例如，若任务未完成，则工作流结束；若完成，则流向Document Node。这是实现“等待后续消息”等状态逻辑的关键。

3.3 工具层
定义：将被复用的、对外的操作（如读写文件、调用API）封装为LangChain Tool。

示例：UpdateExcelTool、GenerateReportTool。这些工具在工作流节点中被声明和调用，实现了执行能力的模块化和标准化。

3.4 支撑服务层
微信沙盒容器：与之前设计一致，是一个独立的Docker化服务。由一个轻量的 Monitor Agent服务管理，该服务负责沙盒生命周期、从SSE流中读取数据，并向Orchestrator发起HTTP请求，触发工作流。

AI与知识库服务：

Ollama：提供Qwen3-VL和Qwen3-Embedding-4B模型服务。

Chroma向量数据库：存储业务知识嵌入，通过LangChain集成，在Multimodal Node中被调用以完成RAG检索。

状态持久化（可选）：LangGraph支持将工作流State检查点（Checkpoint）保存至数据库（如Redis），从而实现长周期、可中断重启的复杂会话。

4. 关键数据流（LangGraph范式）
消息捕获与工作流触发：
微信消息 -> 沙盒容器捕获 -> Monitor Agent服务 -> (HTTP Post) -> Orchestrator -> 创建并invoke新的工作流实例

工作流内部执行：

text
工作流开始 (State初始化)
    ↓
Monitor Node: 将原始消息载入State.raw_message
    ↓
Multimodal Node: 分析 & RAG -> 结果写入State.multimodal_analysis
    ↓
StateTracker Node: 更新状态，并决定下一步
    ├── 若任务未完成 -> 工作流结束（等待下次触发）
    └── 若任务完成 -> 执行 Document Node
            ↓
        Document Node: 调用工具，更新文档 -> 结果写入State
            ↓
        工作流结束
状态持久化：每个工作流实例的State可被自动保存为检查点。当同一任务的下一条消息触发新工作流时，可从检查点恢复状态，实现跨消息的连续对话和跟踪。

5. 扩展性设计
工作流本身的扩展：增加新节点或修改边逻辑即可添加新功能（如新增一个Notification Node用于发送通知）。

替换消息源：Monitor Node是输入适配器。未来迁移企业微信，只需改造外部的Monitor Agent服务，使其从企业微信API拉取消息并触发工作流，工作流内部无需任何修改。

多群组与并行化：每个群聊或任务由独立的工作流实例处理，其State相互隔离。LangGraph运行时支持高并发执行多个工作流实例。

工具生态集成：可轻松集成更多的LangChain Tool（如搜索、计算），丰富工作流能力。

6. 与技术栈的对应关系
本架构是所选技术栈的具象化体现：

LangGraph：实现了本架构的核心工作流引擎。

Chroma + Qwen3-Embedding-4B：作为Multimodal Node中的检索增强组件。

LangChain & Tools：提供了节点与模型、工具、向量数据库交互的标准方式。

FastAPI & Docker：构成了外围的服务化与容器化基础设施。