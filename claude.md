# 项目记忆文档

## 项目基本信息
- 项目名称：多模态Agent微信群自动化项目（LangGraph版）
- 技术栈：LangGraph 0.0.50+、LangChain 0.1.0+、FastAPI 0.104+、Redis 7.2+、ChromaDB 0.4.18+、Ollama（Qwen3系列模型）
- 项目类型：单用户多群聊（MVP）→ 单用户多群聊映射 → 多用户场景
- 创建时间：2025年

## 目录结构
```
Mutil_Agent_WechatGroup_RPA/
├── agents/              # 智能体模块（IntentAgent、VisualAgent、DecisionAgent、SandboxManagerAgent、SSEProcessorAgent）
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
│   └── wechat_sandbox/  # 微信沙盒（AT-SPI混合方案 + 通用消息提取）⭐
└── pyproject.toml       # Python项目配置
```

### 微信沙盒目录结构（2025-01-14更新）
```
services/wechat_sandbox/
├── core/                            # 核心业务逻辑
│   ├── atspi/                       # AT-SPI模块 ⭐
│   │   ├── observer.py              # AT-SPI观察者
│   │   ├── chat_listener.py         # 聊天窗口监听器
│   │   └── global_listener.py       # 全局聊天监听器
│   ├── extractor/                   # 消息提取模块 ⭐ 整合
│   │   ├── message_extractor.py     # 通用消息提取器
│   │   └── models.py                # 消息数据模型
│   ├── producer/                    # 生产者模块（简化）
│   │   ├── hybrid_producer.py       # 混合生产者（AT-SPI + 视觉）
│   │   └── consumer.py              # 消费者
│   └── detector/                    # 视觉检测模块
├── config/                          # 配置管理 ⭐ 独立
│   ├── config.py                    # 配置类
│   ├── config.yaml                  # 配置文件
│   └── config.production.yaml       # 生产配置
├── docs/                            # 文档 ⭐ 整合
│   ├── ARCHITECTURE.md              # 架构文档
│   ├── MESSAGE_TYPES.md             # 消息类型说明
│   ├── AT_SPI_GUIDE.md              # AT-SPI指南
│   └── DIRECTORY_STRUCTURE.md       # 目录结构
├── api/                             # FastAPI接口
└── utils/                           # 工具类
```

详细说明见：`services/wechat_sandbox/DIRECTORY_STRUCTURE_V2.md`

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

### 消息处理规范（2025-01-12更新）
- 原始消息结构：id、sender、content、type、timestamp、image_path、high_res_image_path
- 消息类型枚举：TEXT、IMAGE、VIDEO、FILE、MIXED、**PHOTO** ⭐ 新增
- 任务类型枚举：WORK_REPORT、TASK_ASSIGNMENT、STATUS_UPDATE、OTHER
- 任务阶段枚举：BEFORE、DURING、AFTER、UNKNOWN

### 通用消息提取规范（2025-01-12新增）
- **点击所有消息判断类型**：不预判类型，统一点击处理
- **窗口检测机制**：根据是否唤起新窗口判断消息类型
- **窗口标题映射**：
  - 无窗口 → text
  - "Photos and Videos" → photo/video
  - "File Transfer" → file
  - "Browser" → link
  - 其他 → other
- **文件保存**：自动保存到物理机挂载目录 `/host/data/`
- **SSE推送格式**：使用JSONL格式，每行一个完整JSON对象

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

### 导入路径规范（2025-01-14更新）
```python
# AT-SPI相关
from core.atspi.observer import ATSPIObserver
from core.atspi.chat_listener import ChatWindowListener
from core.atspi.global_listener import GlobalChatListener

# 消息提取（统一）
from core.extractor import UniversalMessageExtractor, MessageType, ExtractedMessage

# 生产者
from core.producer.hybrid_producer import HybridProducer, ProductionMode
from core.producer.consumer import AgentConsumer

# 配置（独立）
from config.config import config
# 或
from config import config
```

## 架构约定

### 微信沙盒架构演进（2025-01-12更新）

#### 阶段一：双生产者架构（早期）
- Producer1（Observer）：检测气泡生成小截图，推送到原始队列
- Producer2（ContentFetcher）：从原始队列消费，精确定位并提取内容，推送到精确队列
- 限制：依赖固定界面区域，界面变动导致采集失败

#### 阶段二：AT-SPI混合方案（推荐）
- 主要方案：AT-SPI UI控件监听
- 兜底方案：视觉技术（自动降级）
- 优势：速度快、资源占用少、准确率高
- SSE流接口：/api/stream/messages流式推送精确消息

#### 阶段三：通用消息提取（当前）⭐
- 点击所有消息判断类型（不预判）
- 根据窗口标题自动分类
- 文件自动保存到物理机
- **仅支持3种消息类型**：text、photo、video
- 其他类型（file、link、表情包等）直接保存到物理机，不推送SSE

### 通用消息提取工作流程（2025-01-14更新）
```
1. 检测新消息（AT-SPI观察者）
   ↓
2. 点击消息（所有消息）
   ↓
3. 检测是否唤起新窗口
   ├─ 否 → 文本消息 (text) → 推送SSE
   └─ 是 → 继续判断
           ↓
       获取窗口标题
           ↓
       ├─ "Photos and Videos" → 图片/视频 (photo/video) → 推送SSE
       ├─ "File Transfer" → 保存到物理机 → 不推送SSE
       ├─ "Browser" → 保存到物理机 → 不推送SSE
       └─ 其他 → 保存到物理机 → 不推送SSE
```

### SSE消息格式（2025-01-14更新）
- **格式**：JSONL（JSON Lines），每行一个完整JSON对象
- **编码**：UTF-8
- **前缀**：`data: `
- **支持的消息类型**：仅text、photo、video
- **其他类型**：保存到物理机，不推送SSE

**示例**：
```
data: {"id":"msg_001","type":"text","sender":"张三","content":{"text":"hello"},"window_detected":false,...}
data: {"id":"msg_002","type":"photo","sender":"李四","content":{"high_res_media_path":"/host/data/photo.png"},"window_detected":true,...}
```

完整数据模型见：`services/wechat_sandbox/docs/MESSAGE_TYPES.md`

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

### 智能体模块层设计（2025-01-11更新）
- 单Agent模式：IntentAgent、VisualAgent、DecisionAgent、SandboxManagerAgent、SSEProcessorAgent
- 多Agent模式：SandboxAuthAgent、UserFeedbackAgent、TrackerAgent、ConstellationAgent
- 智能体解耦：MonitorAgent已拆分为SandboxManagerAgent（容器管理）和SSEProcessorAgent（SSE处理）
- DAG任务图：使用UFO Constellation模式，支持动态任务分解和依赖管理

### 智能体职责约定
- SandboxManagerAgent：仅负责容器生命周期管理，不处理消息流
- SSEProcessorAgent：仅负责SSE流处理（接收/验证/消费/转发），不管理容器
- 其他Agent：专注于各自的业务逻辑，保持职责单一

## 历史决策记录

### 微信沙盒目录结构重组（2025-01-12）
- 问题描述：所有实现都堆在`core/producer/`中，职责不清晰，难以维护
- 决策：按功能模块重组目录结构
  - 新建`core/atspi/`：AT-SPI相关功能（observer、chat_listener、global_listener）
  - 新建`core/message/`：消息处理功能（extractor、models）
  - 新建`core/window/`：窗口管理功能（待扩展）
  - 保留旧文件作为备份
- 影响：
  - 新增`services/wechat_sandbox/core/atspi/`目录
  - 新增`services/wechat_sandbox/core/message/`目录
  - 新增`services/wechat_sandbox/core/window/`目录
  - 新增`services/wechat_sandbox/DIRECTORY_STRUCTURE.md`文档
  - 更新导入路径：`from core.atspi.observer import ATSPIObserver`
  - 更新`services/wechat_sandbox/README.md`

### 通用消息提取实现（2025-01-12）
- 问题描述：需要自动识别消息类型并提取媒体文件
- 决策：实现通用消息提取逻辑
  - 点击所有消息判断类型（不预判）
  - 根据窗口标题自动分类（text/photo/video/file/link/other）
  - 文件自动保存到物理机
  - SSE推送改为JSONL格式
- 影响：
  - 新增`core/message/extractor.py`：通用消息提取器
  - 新增`core/producer/SSE_MESSAGE_MODEL.md`：SSE数据模型文档
  - 新增`core/producer/sse_message_model.jsonl`：JSONL格式示例
  - 新增`core/producer/UNIVERSAL_MESSAGE_EXTRACTION.md`：实现说明文档
  - 更新`core/schemas.py`：添加PHOTO类型和high_res_image_path字段
  - 更新`atspi_observer.py`：集成通用消息提取

### SSE推送格式改为JSONL（2025-01-12）
- 问题描述：原有SSE推送格式不够清晰，需要更标准化的格式
- 决策：使用JSONL（JSON Lines）格式
  - 每行一个完整的JSON对象
  - 便于解析和处理
  - 支持多种消息类型（text/photo/video/file/link/other）
- 影响：
  - 更新SSE推送逻辑
  - 新增完整的数据模型定义
  - 更新`ExtractedMessage.to_sse_json()`方法

### 前端管理员监控界面实现（2025-01-11）
- 问题描述：管理员无法从前端实时监控微信沙盒容器状态和工作流运行状态
- 决策：实现前端管理员监控界面SandboxMonitor
  - 前端组件：SandboxMonitor.tsx提供实例监控、远程桌面、容器操作、ROI配置、实时日志、服务状态
  - 后端API：sandbox_service.py提供REST API接口（instances/status/start/stop/restart/logs/roi/screenshot）
  - Agent集成：SandboxManagerAgent负责容器生命周期管理
- 影响：
  - 新增frontend/src/pages/admin/components/SandboxMonitor.tsx
  - 新增frontend/src/services/sandbox.ts前端服务层
  - 新增services/sandbox_service.py后端API服务
  - 更新架构设计文档v3.md添加9.1节前端管理员监控界面

### MonitorAgent解耦为SandboxManagerAgent和SSEProcessorAgent（2025-01-11）
- 问题描述：原MonitorAgent同时负责容器管理和消息消费，职责混杂，难以独立扩展
- 决策：将MonitorAgent解耦为两个独立智能体
  - SandboxManagerAgent：负责容器生命周期管理（创建/启动/停止/删除/健康检查）
  - SSEProcessorAgent：负责SSE流处理（接收/验证/消费/转发）
- 影响：
  - 新增agents/sandbox_manager_agent.py和agents/sse_processor_agent.py
  - 更新架构设计文档v3.md中的智能体定义和DAG任务图
  - 架构设计文档v3.md中的所有MonitorAgent引用已替换为SandboxManagerAgent/SSEProcessorAgent

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

1. ~~**MonitorAgent职责混杂**：容器管理 + 消息消费耦合，难以独立扩展~~（已解决：解耦为SandboxManagerAgent和SSEProcessorAgent）
2. **单Agent限制**：无法支持前端用户交互、微信登录引导、多群聊监控
3. **微信界面变动适配**：双生产者架构依赖固定界面区域，界面变动会导致采集失败
4. **用户交互缺失**：微信登录需要用户扫码，但没有交互层支持
5. ~~**前端监控缺失**：无法实时监控微信沙盒和工作流运行状态~~（已解决：实现前端管理员监控界面SandboxMonitor）

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

## 技术文档索引

### 核心文档
- [项目架构文档](docs/架构设计文档v3.md)
- [目录结构详细说明](services/wechat_sandbox/DIRECTORY_STRUCTURE.md)
- [SSE消息数据模型](services/wechat_sandbox/core/producer/SSE_MESSAGE_MODEL.md)

### AT-SPI相关
- [AT-SPI混合方案说明](docs/atspi_hybrid_solution.md)
- [AT-SPI部署配置](docs/atspi_deployment_config.md)
- [通用消息提取说明](services/wechat_sandbox/core/producer/UNIVERSAL_MESSAGE_EXTRACTION.md)

### Docker相关
- [Docker主文档](docker/README.md)
- [脚本说明](docker/scripts/README.md)
