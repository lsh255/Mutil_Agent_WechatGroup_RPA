# 多模态Agent微信群自动化项目 (LangGraph版)

基于LangGraph的有状态多模态Agent自动化系统，采用UFO Constellation DAG任务分解模式，用于监控微信工作群消息，理解图文混合内容，跟踪任务状态，并自动更新台账和生成工作报告。

## 项目架构

本项目采用 **UFO Constellation DAG任务分解模式**，支持单Agent轻量模式和交互式多Agent扩展模式：

- **UFO Constellation全局协调器**: 分解用户意图为动态DAG任务图，编排多智能体协作
- **LangGraph工作流引擎**: 核心处理层，负责从消息理解到文档生成的全过程
- **微信沙盒容器**: 独立的Docker化服务，提供微信客户端运行环境
- **AI与知识库服务**: Ollama提供本地多模态模型，SiliconFlow提供云端Embedding模型，Chroma提供向量数据库
- **协调中心**: FastAPI应用，提供管理界面和工作流触发接口
- **前端管理界面**: React + TypeScript + Vite + Tailwind CSS，提供可视化的监控、管理和交互功能

### 架构演进

- **v2（原架构）**: Orchestrator-Worker（协调器-工作器）模式，单Agent工作流
- **v3（新架构）**: UFO Constellation模式，动态DAG任务分解，支持多Agent交互和前端用户交互

### 核心设计原则

| 原则 | 说明 |
|------|------|
| 状态驱动 | LangGraph状态机驱动工作流流转 |
| 异步解耦 | Redis Streams实现服务间解耦通信 |
| 智能编排 | 多Agent协同处理复杂业务场景 |
| 容错设计 | 检查点机制支持工作流恢复 |
| DAG任务分解 | ConstellationAgent将用户意图分解为动态DAG任务图 |
| 图演化机制 | 根据任务执行结果动态调整DAG结构 |
| 向后兼容 | 保留原有单Agent工作流，支持轻量模式 |
| 前端交互 | WebSocket实时通信，支持用户扫码登录和意图确认 |

### 微信沙盒架构

微信沙盒采用分层架构设计（v2.0 - AT-SPI混合架构）：

- **API接口层 (`api/`)**: FastAPI路由，提供REST API和SSE流式接口
- **核心业务逻辑层 (`core/`)**: 包含消息生产者、队列管理、AT-SPI监听、消息提取等核心模块
  - **AT-SPI模块 (`core/atspi/`)**: AT-SPI UI控件监听和消息观察
  - **消息处理模块 (`core/message/`)**: 通用消息提取、分类和模型定义
  - **窗口管理模块 (`core/window/`)**: 窗口检测、交互和自动化操作
  - **生产者模块 (`core/producer/`)**: 混合生产者（AT-SPI + 视觉方案）
  - **视觉检测模块 (`core/detector/`)**: 基于视觉的消息检测（兜底方案）
- **服务编排层 (`services/`)**: 统一管理组件生命周期和服务编排
- **工具模块 (`utils/`)**: 配置管理、日志记录、跨平台适配等工具函数

**核心特性**:
- **AT-SPI优先**: 使用Linux AT-SPI (Assistive Technology Service Provider Interface) 直接访问微信UI控件树
- **通用消息提取**: 点击所有消息，通过检测新窗口来判断消息类型
- **混合架构**: AT-SPI失败时自动降级到视觉检测方案
- **JSONL格式**: SSE流使用JSONL (JSON Lines) 格式推送消息

### Docker配置统一管理

所有Docker相关文件统一放在 `docker/` 目录下：

- `docker/base/`: 基础镜像
- `docker/compose/`: Docker Compose编排文件（开发、生产、测试环境）
- `docker/frontend/`: 前端镜像
- `docker/orchestrator/`: 协调中心镜像
- `docker/sandbox/`: 微信沙盒镜像
- `docker/scripts/`: 统一的启动脚本

## 项目结构

```
Mutil_Agent_WechatGroup_RPA/
├── agents/                           # 智能体模块
│   ├── prompts/                     # 智能体提示词
│   │   ├── decision_prompts.py
│   │   ├── intent_prompts.py
│   │   └── visual_prompts.py
│   ├── decision_agent.py            # 决策智能体
│   ├── intent_agent.py              # 意图识别智能体
│   ├── monitor_agent.py             # 监控智能体
│   └── visual_agent.py              # 视觉定位智能体
├── config/                           # 配置管理
│   ├── settings.py                  # Pydantic配置类
│   └── settings.yaml                # 配置文件
├── core/                             # 核心业务逻辑
│   ├── workflows/                    # LangGraph工作流
│   │   ├── nodes/                   # 工作流节点
│   │   │   ├── document_node.py     # 文档执行节点
│   │   │   ├── monitor_node.py      # 监控节点
│   │   │   ├── multimodal_node.py   # 多模态分析节点
│   │   │   └── state_tracker_node.py # 状态跟踪节点
│   │   └── main_workflow.py         # 主工作流
│   ├── schemas.py                   # 数据模型定义
│   └── state.py                     # LangGraph状态定义
├── docker/                           # Docker配置
│   ├── base/                        # 基础镜像
│   ├── compose/                     # Docker Compose配置
│   │   ├── nginx/
│   │   ├── docker-compose.dev.yml
│   │   ├── docker-compose.multi.yml
│   │   ├── docker-compose.prod.yml
│   │   └── docker-compose.sandbox.test.yml
│   ├── frontend/                    # 前端镜像
│   ├── orchestrator/                # Orchestrator镜像
│   ├── sandbox/                     # WeChat Sandbox镜像
│   └── scripts/                     # 启动脚本
├── docs/                             # 文档
│   ├── ENVIRONMENT_INIT.md          # 环境初始化
│   ├── ENVIRONMENT_SETUP.md         # 环境搭建
│   ├── 架构设计文档v3.md            # 架构设计文档（UFO Constellation模式）
│   ├── 技术栈文档v2.md              # 技术栈文档
│   ├── 方案1.md                     # UFO Constellation DAG任务分解架构
│   ├── 方案2.md                     # UFO AIP分层协作架构
│   ├── 开发计划.md                  # 8周开发计划
│   └── todolist.md                  # 任务清单
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── pages/
│   │   │   ├── admin/               # 管理员页面
│   │   │   └── chat/                # 聊天交互页面
│   │   ├── store/                   # Zustand状态管理
│   │   ├── services/                # API服务
│   │   └── types/                   # TypeScript类型定义
│   ├── package.json
│   └── vite.config.ts
├── knowledge_base/                   # 知识库管理
│   ├── vector_store.py              # 向量存储管理
│   └── embeddings.py                # 嵌入模型管理
├── scripts/                          # 部署脚本
│   ├── create_excel_template.py     # 创建Excel模板
│   ├── init_knowledge_base.py       # 初始化知识库
│   ├── start_all.py                 # 启动所有服务
│   └── test_workflow.py             # 测试工作流
├── services/                         # 服务层
│   ├── orchestrator/                # 协调中心服务
│   │   └── main.py                  # FastAPI应用
│   └── wechat_sandbox/              # 微信沙盒服务
│       ├── api/                     # API接口层
│       ├── core/                    # 核心业务逻辑层
│       ├── services/                # 服务编排层
│       ├── utils/                   # 工具模块
│       ├── config.yaml              # 配置文件
│       └── main.py                  # 统一入口脚本
├── templates/                        # 模板文件
│   └── daily_report.j2              # 报告模板
├── tools/                            # 工具层
│   ├── excel_tool.py                # Excel更新工具
│   └── word_tool.py                 # Word报告生成工具
├── CLAUDE.md                         # 项目记忆文档
├── pyproject.toml                    # 项目依赖配置
└── requirements.txt                 # Python依赖
```

## 技术栈

### 核心框架层

| 技术 | 版本 | 用途 |
|------|------|------|
| LangGraph | >=0.0.50 | 工作流编排引擎，构建有状态多智能体系统 |
| LangChain | >=0.1.0 | AI模型调用链、提示词管理、工具集成 |
| LangChain-Community | >=0.0.10 | 集成ChatOllama等社区模型 |
| LangChain-Chroma | >=0.1.0 | 向量数据库连接器 |

### Web服务层

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | >=0.104.0 | HTTP服务框架，提供异步支持和自动API文档 |
| Uvicorn | >=0.24.0 | ASGI服务器，运行FastAPI应用 |
| Pydantic | >=2.5.0 | 数据验证、配置管理、API请求响应模型 |
| Pydantic-Settings | >=2.1.0 | 多源配置管理（YAML + 环境变量） |
| WebSocket | - | 前后端实时双向通信，用户交互反馈 |

### 消息队列与状态管理

| 技术 | 版本 | 用途 |
|------|------|------|
| Redis | >=7.2.0 | 消息持久化、分发、状态管理 |
| Redis-Checkpointer | - | LangGraph状态持久化 |

### AI模型层

| 技术 | 用途 |
|------|------|
| ChatOllama (LangChain-Community) | 调用本地Ollama大语言模型 |
| OpenAIEmbeddings (LangChain) | 文本向量化（兼容硅基流动API） |
| Qwen3-VL-8B | 视觉语言模型，理解图文混合内容 |
| Qwen3-Embedding-8B | 文本嵌入模型，用于RAG检索 |
| Qwen3-72B | 大语言模型，用于意图识别和决策 |

### 向量数据库层

| 技术 | 用途 |
|------|------|
| ChromaDB | 向量数据库，存储知识库向量 |
| Chroma (langchain-chroma) | LangChain与ChromaDB的集成 |

### 图像处理与自动化

| 技术 | 版本 | 用途 |
|------|------|------|
| OpenCV-Python | >=4.8.0 | 图像处理、屏幕变化检测、气泡识别 |
| Pillow | >=10.0.0 | 图像操作、截图处理 |

### 文档操作层

| 技术 | 版本 | 用途 |
|------|------|------|
| openpyxl | >=3.1.0 | Excel文档读写和更新 |
| python-docx | >=1.1.0 | Word文档生成 |
| Jinja2 | >=3.1.0 | 模板引擎，报告渲染 |

### 容器与编排层

| 技术 | 版本 | 用途 |
|------|------|------|
| Docker (Python SDK) | >=7.0.0 | 容器生命周期管理 |
| Docker Compose | - | 多容器编排 |

### 日志与监控层

| 技术 | 版本 | 用途 |
|------|------|------|
| structlog | >=23.2.0 | 结构化日志生成 |
| Prometheus-client | >=0.19.0 | 指标收集与暴露 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18.3+ | 前端框架 |
| Vite | 5.4+ | 构建工具 |
| TypeScript | 5.5+ | 类型安全开发 |
| React Router | 6.26+ | 单页应用路由 |
| Zustand | 4.5+ | 状态管理 |
| Tailwind CSS | 3.4+ | CSS框架 |
| Axios | 1.7.7 | HTTP客户端 |
| Recharts | 2.12.7 | 图表库 |

## 快速开始

### 方式一：使用Conda虚拟环境（推荐）

#### Windows用户

```bash
# 1. 创建并激活Conda环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境（如果需要）
conda activate wechat-workflow-agent

# 3. 启动基础设施
docker-compose -f docker/compose/docker-compose.dev.yml up -d redis ollama

# 4. 拉取AI模型
ollama pull qwen3-vl:latest

# 5. 初始化知识库
python scripts/init_knowledge_base.py

# 6. 启动协调中心
uvicorn services.orchestrator.main:app --reload
```

#### Linux/Mac用户

```bash
# 1. 创建并激活Conda环境
chmod +x scripts/setup_conda_env.sh
./scripts/setup_conda_env.sh

# 2. 激活环境（如果需要）
conda activate wechat-workflow-agent

# 3. 启动基础设施
docker-compose up -d redis ollama

# 4. 拉取AI模型
ollama pull qwen3-vl:latest

# 5. 初始化知识库
python scripts/init_knowledge_base.py

# 6. 启动协调中心
uvicorn services.orchestrator.main:app --reload
```

### 方式二：直接安装依赖

#### 1. 安装依赖

```bash
pip install -e .
```

#### 2. 启动基础设施

```bash
docker-compose -f docker/compose/docker-compose.dev.yml up -d redis ollama
```

#### 3. 拉取AI模型

```bash
ollama pull qwen3-vl:latest
```

#### 4. 初始化知识库

```bash
python scripts/init_knowledge_base.py
```

#### 5. 启动协调中心

```bash
uvicorn services.orchestrator.main:app --reload
```

#### 6. 启动监控Agent

```bash
python scripts/start_all.py
```

## 工作流说明

系统通过LangGraph工作流处理每条微信消息：

### 单Agent工作流（轻量模式）

```
monitor → multimodal → state_tracker → document → END
```

1. **Monitor Node**: 接收原始消息并载入工作流状态
2. **Multimodal Node**: 调用Qwen3-VL模型进行图文理解，结合RAG检索增强上下文
3. **StateTracker Node**: 更新任务状态，判断任务是否完成
4. **Document Node**: 如果任务完成，调用工具更新Excel和生成Word报告

### 多Agent交互工作流（扩展模式）

```
SandboxAuthAgent → MonitorAgent → MultimodalAgent → TrackerAgent → UserFeedbackAgent → DocumentAgent
```

1. **SandboxAuthAgent**: 检查微信沙盒容器状态和登录状态
2. **MonitorAgent**: 接收原始消息并载入工作流状态
3. **MultimodalAgent**: 调用Qwen3-VL模型进行图文理解，结合RAG检索增强上下文
4. **TrackerAgent**: 更新任务状态，判断任务是否完成
5. **UserFeedbackAgent**: 通过WebSocket与前端交互，接收用户反馈
6. **DocumentAgent**: 如果任务完成，调用工具更新Excel和生成Word报告

### UFO Constellation全局协调

```
用户请求 → 意图解析 → DAG生成 → 任务调度 → Agent执行 → 结果收集 → 任务完成
```

1. **意图解析**: ConstellationAgent识别用户意图类型
2. **DAG生成**: DAGBuilder根据意图类型生成动态任务依赖图
3. **任务调度**: 将DAG任务分发给对应的Agent执行
4. **Agent执行**: 各Agent并行或串行执行任务
5. **结果收集**: 收集各Agent执行结果
6. **任务完成**: 判断所有任务完成，返回结果

## 配置说明

主要配置文件位于 `config/settings.yaml`：

```yaml
project:
  name: "wechat-workflow-agent"
  env: "development"

ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
  siliconflow:
    api_key: "your-api-key"
    base_url: "https://api.siliconflow.cn/v1"
    embedding_model: "Qwen/Qwen3-Embedding-8B"

vector_store:
  type: "chroma"
  persist_directory: "./data/chroma_db"
  collection_name: "work_knowledge_base"

workflow:
  mode: "single"  # single: 单Agent模式 | multi: 多Agent模式
  enable_frontend_interaction: false
```

## API接口

协调中心提供以下主要接口：

- `GET /`: 根路径
- `GET /health`: 健康检查
- `POST /workflow/trigger`: 触发工作流执行
- `GET /workflow/status`: 获取工作流状态
- `POST /constellation/request`: 接收用户请求，触发ConstellationAgent（多Agent模式）
- `POST /constellation/feedback`: 接收前端用户反馈（多Agent模式）
- `GET /constellation/status`: 获取DAG任务执行状态（多Agent模式）
- `WebSocket /ws/{user_id}`: WebSocket连接，实时推送交互请求（多Agent模式）

## 测试

### 运行测试

项目提供完整的测试套件，包括单元测试、API测试和集成测试。

#### 安装测试依赖

```bash
cd services/wechat_sandbox
pip install -r requirements.txt
```

#### 运行所有测试

```bash
# 使用便捷脚本
python run_tests.py all

# 或直接使用pytest
pytest tests/ -v
```

#### 运行特定类型测试

```bash
# 单元测试
python run_tests.py unit

# API测试
python run_tests.py api

# 集成测试
python run_tests.py integration

# Docker测试
python run_tests.py docker
```

#### 在Docker中运行测试

```bash
# 启动服务
docker-compose up -d

# 运行测试
docker-compose exec producer_service python run_tests.py all
```

#### 测试覆盖率

```bash
# 生成HTML覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 测试文档

详细的测试文档请参考：[tests/README.md](services/wechat_sandbox/tests/README.md)

---

## 微信沙盒服务

微信沙盒容器提供混合生产者模型的消息生产服务（v2.0 - AT-SPI优先架构），通过Redis和FastAPI暴露消息流供monitor_agent.py消费。

### 架构说明

**混合生产者架构**:

- **AT-SPI模式（优先）**: 使用Linux AT-SPI直接访问微信UI控件树，监听消息列表变化
- **视觉模式（兜底）**: 当AT-SPI不可用时，自动降级到基于视觉的消息检测

**AT-SPI工作流程**:
1. **AT-SPI Observer**: 监听微信消息列表UI控件树变化
2. **Universal Message Extractor**: 点击所有消息，检测是否唤起新窗口
3. **窗口类型判断**: 根据窗口标题分类消息
   - 无窗口 → text
   - "Photos and Videos" → photo/video
   - "File Transfer" → file
   - "Browser" → link
4. **媒体保存**: 将图片/视频/文件保存到物理机（`/host/data/`）
5. **消息推送**: 以JSONL格式推送到Redis Stream

**视觉兜底流程**（当AT-SPI失败时）:
- **Producer1 (Observer)**: 监控微信群消息界面，检测新消息气泡，返回小截图 + 气泡像素位置
- **Producer2 (Content Fetcher)**: 根据气泡位置点击获取高精度内容（高清图片/文本），返回精确内容

**数据流（AT-SPI模式）**:
```
微信UI控件树 (AT-SPI)
    ↓ [AT-SPI Observer - UI控件监听]
消息列表变化检测
    ↓ [Universal Message Extractor - 点击消息判断类型]
窗口检测与类型判断
    ↓ [媒体保存到物理机]
Redis Stream (stream_precise)
    ↓ [FastAPI SSE端点 - JSONL格式]
monitor_agent.py (SSE消费)
```

**数据流（视觉兜底模式）**:
```
微信群界面 (Linux微信)
    ↓ [Producer1 - 观察者]
Redis Stream (stream_raw)
    ↓ [Producer2 - 内容获取者]
Redis Stream (stream_precise)
    ↓ [FastAPI SSE端点]
monitor_agent.py (SSE消费)
```

### 本地运行

```bash
cd services/wechat_sandbox
pip install -r requirements.txt
python main.py
```

### Docker部署

#### 单实例部署

```bash
docker-compose -f docker/compose/docker-compose.yml up -d
```

docker-compose.yml会启动以下容器：
1. **redis**: Redis消息队列服务
2. **sandbox**: 微信沙盒服务（包含Linux微信）

#### 多实例部署（多用户多群组）

```bash
docker-compose -f docker/compose/docker-compose.multi.yml up -d
```

docker-compose.multi.yml会启动多个沙盒服务实例：
1. **redis**: Redis消息队列服务
2. **sandbox_1**: 实例1（端口8001/6081/5901）
3. **sandbox_2**: 实例2（端口8002/6082/5902）
4. **sandbox_3**: 实例3（端口8003/6083/5903）

### Web管理界面

服务启动后，可以通过浏览器访问以下界面：

#### VNC远程桌面（微信登录）

- **访问地址**: http://localhost:6080（单实例）
- **多实例**: http://localhost:6081/6082/6083（对应不同实例）
- **密码**: vnc123
- **用途**: 
  - 操作Linux微信扫码登录
  - 手动配置监控区域（ROI）
  - 实时查看微信界面

#### Web管理控制台

- **访问地址**: http://localhost:8000/api/ui（单实例）
- **多实例**: http://localhost:8001/api/ui/8002/api/ui/8003/api/ui（对应不同实例）
- **功能**:
  - 实时查看服务状态
  - 配置监控区域（ROI）
  - 屏幕截图预览
  - 重启服务
  - 查看实时日志

### 使用流程

1. **启动服务**
   ```bash
   docker-compose -f docker/compose/docker-compose.yml up -d
   ```

2. **通过VNC登录微信**
   - 访问 http://localhost:6080
   - 输入密码：vnc123
   - 操作Linux微信扫码登录

3. **配置监控区域**
   - 方法1：通过Web界面配置
     - 访问 http://localhost:8000/api/ui
     - 在右侧面板输入ROI坐标
     - 点击"更新监控区域"
   - 方法2：通过VNC界面选择
     - 在VNC中手动确定监控区域坐标
     - 在Web界面输入坐标

4. **查看服务状态**
   - 访问 http://localhost:8000/status
   - 或使用Web管理界面查看

### 配置说明

#### Redis配置
```yaml
redis:
  host: redis
  port: 6379
  db: 0
  stream_raw: wechat:messages:raw
  stream_precise: wechat:messages:precise
```

#### 微信监控配置
```yaml
monitor:
  target_group_name: "你的群名称"
  roi: [left, top, right, bottom]  # 监控区域坐标
  capture_interval_ms: 200
```

### API接口

生产者服务提供以下接口：

#### 基础接口
- `GET /`: 服务信息
- `GET /health`: 健康检查
- `GET /status`: 服务状态
- `GET /stream`: SSE流式消息端点（供monitor_agent.py消费）

#### Web管理接口
- `GET /api/ui`: Web管理界面（HTML）
- `POST /api/roi`: 更新监控区域配置
  ```json
  {
    "left": 100,
    "top": 200,
    "right": 500,
    "bottom": 800
  }
  ```
- `GET /api/screenshot`: 获取当前屏幕截图
- `POST /api/restart`: 重启生产者服务

### 服务文件说明

**核心模块（v2.0新架构）**:
- `services/wechat_sandbox/core/atspi/observer.py`: AT-SPI观察者，监听微信UI控件树变化
- `services/wechat_sandbox/core/message/extractor.py`: 通用消息提取器，点击消息判断类型
- `services/wechat_sandbox/core/window/manager.py`: 窗口管理器，检测和操作窗口
- `services/wechat_sandbox/core/producer/hybrid.py`: 混合生产者，协调AT-SPI和视觉方案

**保留模块（视觉兜底方案）**:
- `services/wechat_sandbox/core/producer/observer.py`: 生产者1 - 消息观察者（视觉方案）
- `services/wechat_sandbox/core/producer/content_fetcher.py`: 生产者2 - 内容获取者（视觉方案）
- `services/wechat_sandbox/core/producer/monitor.py`: 视觉监控器（Linux微信版本）
- `services/wechat_sandbox/core/detector/detector.py`: 变化检测器
- `services/wechat_sandbox/core/extractor/extractor.py`: 内容提取器（Linux微信版本）
- `services/wechat_sandbox/core/classifier/classifier.py`: 消息类型分类器

**通用模块**:
- `services/wechat_sandbox/core/queue/manager.py`: Redis队列管理器（使用Redis Streams）
- `services/wechat_sandbox/api/__init__.py`: FastAPI应用入口（含Web管理接口）
- `services/wechat_sandbox/utils/logger.py`: 日志工具
- `services/wechat_sandbox/utils/config.py`: 配置工具
- `services/wechat_sandbox/main.py`: 服务启动脚本

**Docker配置**:
- `docker/scripts/start_wechat.sh`: 容器启动脚本（VNC/noVNC初始化）
- `docker/compose/docker-compose.yml`: 单实例Docker编排配置
- `docker/compose/docker-compose.multi.yml`: 多实例Docker编排配置
- `docker/sandbox/Dockerfile`: 生产者服务镜像构建（含VNC/noVNC）

**文档**:
- `services/wechat_sandbox/README.md`: 微信沙盒详细文档（v2.0）
- `services/wechat_sandbox/DIRECTORY_STRUCTURE.md`: 目录结构说明
- `services/wechat_sandbox/core/producer/SSE_MESSAGE_MODEL.md`: SSE JSONL数据模型文档

## 扩展性

- **新增节点**: 在 `core/workflows/nodes/` 中创建新节点，并在 `main_workflow.py` 中注册
- **新增工具**: 在 `tools/` 中创建新工具类
- **更换消息源**: 实现 `IMessageSource` 接口，支持企业微信等平台
- **新增Agent**: 在 `agents/` 中创建新Agent，并在 `core/workflows/` 中集成
- **扩展前端交互**: 在 `frontend/src/` 中添加新的页面和组件

## 文档

项目文档位于 `docs/` 目录：

- [环境初始化](docs/ENVIRONMENT_INIT.md): 环境搭建指南
- [环境搭建](docs/ENVIRONMENT_SETUP.md): 详细环境配置
- [架构设计文档v3.md](docs/架构设计文档v3.md): UFO Constellation架构设计
- [技术栈文档v2.md](docs/技术栈文档v2.md): 技术栈详细说明
- [方案1.md](docs/方案1.md): UFO Constellation DAG任务分解架构
- [方案2.md](docs/方案2.md): UFO AIP分层协作架构
- [开发计划.md](docs/开发计划.md): 8周开发计划
- [todolist.md](docs/todolist.md): 任务清单

## 许可证

MIT License
