# 项目记忆文档

## 项目基本信息
- 项目名称：多模态Agent微信群自动化项目（LangGraph版）
- 技术栈：LangGraph 0.0.50+、LangChain 0.1.0+、FastAPI 0.104+、Redis 7.2+、ChromaDB 0.4.18+、Ollama（Qwen3系列模型）
- 项目类型：单用户多群聊（MVP）→ 单用户多群聊映射 → 多用户场景
- 创建时间：2025年

## 目录结构
```
Mutil_Agent_WechatGroup_RPA/
├── agents/              # 智能体模块（IntentAgent、VisualAgent、DecisionAgent、MonitorAgent）
├── config/              # 配置管理（settings.py、settings.yaml）
├── core/                # 核心业务逻辑（LangGraph工作流、状态定义）
│   ├── workflows/       # LangGraph工作流定义
│   │   ├── nodes/      # 工作流节点
│   │   └── main_workflow.py
│   ├── schemas.py      # Pydantic数据模型
│   └── state.py        # LangGraph状态定义
├── docker/              # Docker配置（基础镜像、compose配置）
├── docs/                # 项目文档
├── frontend/            # React前端应用
├── knowledge_base/      # Chroma向量数据库管理
├── scripts/             # 部署、初始化脚本
├── services/            # 服务模块
│   ├── orchestrator/   # FastAPI协调中心
│   └── wechat_sandbox/  # 微信沙盒（双生产者架构）
└── pyproject.toml       # Python项目配置
```

## 开发规则（必须遵守）

### LangGraph框架约束
- 工作流使用StateGraph构建，状态定义必须继承TypedDict
- 状态传递使用Annotated[list, add_messages]模式实现消息追加
- 条件边使用add_conditional_edges实现工作流分支
- 工作流检查点使用Redis Checkpointer实现状态持久化

### 数据模型规范
- 所有数据模型使用Pydantic 2.5+定义
- 枚举类型使用Python enum.Enum
- 时间字段使用datetime类型，序列化为ISO格式字符串
- 图像路径使用相对路径（相对于data目录）

### 消息处理规范
- 原始消息结构：id、sender、content、type、timestamp、image_path
- 消息类型枚举：TEXT、IMAGE、VIDEO、FILE、MIXED
- 任务类型枚举：WORK_REPORT、TASK_ASSIGNMENT、STATUS_UPDATE、OTHER
- 任务阶段枚举：BEFORE、DURING、AFTER、UNKNOWN

### AI模型调用规范
- 意图识别使用Qwen3-72B（temperature: 0.1, max_tokens: 100）
- 视觉定位使用Qwen3-VL-8B（temperature: 0.1, max_tokens: 200）
- Agent决策使用Qwen3-72B（temperature: 0.3, max_tokens: 300）
- 嵌入使用Qwen3-Embedding-4B（用于ChromaDB RAG检索）

### Redis使用规范
- 消息队列使用Redis Streams，键名格式：wechat:messages:{raw|precise}
- 状态存储使用Redis Hash，键名格式：state:{user_id}:{workflow_id}
- 分布式锁使用Redis SET NX，键名格式：lock:{resource}:{user_id}
- 过期时间：消息队列24小时、状态存储7天、分布式锁10分钟

### 日志规范
- 使用structlog 23.2+生成结构化日志
- 日志级别：ERROR（功能异常）、WARN（潜在问题）、INFO（关键业务节点）、DEBUG（调试信息）
- 必须添加日志的位置：try-catch的catch块、外部调用前后、业务入口、状态变更、重要条件分支

## 架构约定

### Orchestrator-Worker架构模式
- Orchestrator：LangGraph工作流引擎负责任务编排和状态管理
- Worker：各功能节点（monitor、multimodal、state_tracker、document）专注特定领域处理
- 通过LangGraph Send API动态创建和分发Worker任务

### 状态流转设计
```
Entry → monitor → multimodal → state_tracker → document → END
                                          ↓
                                       (条件分支)
                                    任务完成？
                                    Yes → document
                                    No → END
```

### 微信沙盒双生产者架构
- Producer1（Observer）：检测气泡生成小截图，推送到原始队列
- Producer2（ContentFetcher）：从原始队列消费，精确定位并提取内容，推送到精确队列
- SSE流接口：/api/stream/messages流式推送精确消息

### 多模态分析流程
- MultimodalNode接收RawMessage，调用Qwen3-VL-8B分析图文内容
- 分析结果：task_type（任务类型）、task_phase（任务阶段）、user（用户）、summary（摘要）、location（地点）
- StateTrackerNode根据分析结果更新TaskStatus，判断任务是否完成

### 文档执行流程
- DocumentNode根据TaskStatus生成DocumentUpdate指令
- 支持操作类型：write_report（写日报）、update_ledger（更新台账）、save_message（保存消息）
- 日报按事项生成，台账按作业更新

### 前端交互规范
- 用户配置：今日工作安排（事项1、地点A、人员1、人员2）
- 群聊监控：用户指定监控群聊名称
- 登录引导：微信扫码登录阶段返回交互层，引导用户打开VNC界面
- WebSocket通信：意图反馈、沙盒登录引导、状态监控

## 历史决策记录

### MonitorAgent功能混杂问题（2025-01-11）
- 问题描述：MonitorAgent同时负责容器管理和消息消费，职责不清
- 决策：需要将MonitorAgent拆分为独立的容器管理服务和流消费服务
- 影响：涉及services/monitor_agent.py重构，新增services/sandbox_manager和services/stream_consumer

### LangGraph单Agent到多Agent演进（2025-01-11）
- 问题描述：当前单Agent架构无法支持前端用户交互、微信登录引导、多群聊监控等复杂场景
- 决策：参考UFO³ Galaxy架构，设计基于LangGraph的多Agent协作架构
- 需求：保留单Agent轻量性，引入多Agent扩展性，支持前端交互和用户协助

### 消息时间地点逻辑关系处理（2025-01-11）
- 业务逻辑：群成员A发消息"作业w1作业前"，群成员B发消息"作业w1作业中"，两者属于同一作业的不同阶段
- 技术方案：StateTrackerNode维护TaskStatus，根据sender、task_id、task_phase关联消息
- 实现方式：使用Redis存储任务状态，key格式：task:{user_id}:{task_id}:{work_id}

### 事项与作业的层级关系（2025-01-11）
- 事项：用户配置的工作安排（事项1、事项2、事项3）
- 作业：事项下的具体作业（w1、w2、w3）
- 日志生成：按事项生成日报（包含该事项下所有作业）
- 台账更新：按作业更新台账（作业前、作业中、作业后）

## 当前架构痛点

1. **MonitorAgent职责混杂**：容器管理 + 消息消费耦合，难以独立扩展
2. **单Agent限制**：无法支持前端用户交互、微信登录引导、多群聊监控
3. **微信界面变动适配**：双生产者架构依赖固定界面区域，界面变动会导致采集失败
4. **用户交互缺失**：微信登录需要用户扫码，但没有交互层支持
5. **前端监控缺失**：无法实时监控微信沙盒和工作流运行状态

## 演进目标

### 阶段一：单Agent架构（当前）
- 核心功能：多模态分析、任务状态跟踪、文档执行
- 限制：无前端交互、单群聊监控、固定界面区域

### 阶段二：多Agent协作（目标）
- 核心功能：用户交互Agent、容器管理Agent、消息消费Agent、任务编排Agent
- 扩展：支持多群聊监控、动态界面适配、前端实时监控

### 阶段三：多用户场景（远期）
- 核心功能：用户管理、数据隔离、多实例沙盒
- 扩展：支持多用户并发访问、独立任务配置
