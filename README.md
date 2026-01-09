# 多模态Agent微信群自动化项目 (LangGraph版)

基于LangGraph的有状态多模态Agent自动化系统，用于监控微信工作群消息，理解图文混合内容，跟踪任务状态，并自动更新台账和生成工作报告。

## 项目架构

本项目采用"中心化工作流引擎 + 外围服务"的混合架构：

- **LangGraph工作流引擎**: 核心处理层，负责从消息理解到文档生成的全过程
- **微信沙盒容器**: 独立的Docker化服务，提供微信客户端运行环境
- **AI与知识库服务**: Ollama提供多模态模型，Chroma提供向量数据库
- **协调中心**: FastAPI应用，提供管理界面和工作流触发接口

## 项目结构

```
wechat-workflow-ai-agent/
├── config/                          # 配置管理
│   ├── settings.yaml                # 主配置文件
│   └── settings.py                  # Pydantic配置类
├── core/                            # 核心框架
│   ├── schemas.py                   # 数据模型定义
│   ├── state.py                     # LangGraph状态定义
│   └── workflows/                   # 工作流定义
│       ├── main_workflow.py         # 主工作流
│       └── nodes/                   # 工作流节点
│           ├── monitor_node.py      # 监控节点
│           ├── multimodal_node.py   # 多模态分析节点
│           ├── state_tracker_node.py # 状态跟踪节点
│           └── document_node.py     # 文档执行节点
├── tools/                           # 工具层
│   ├── excel_tool.py                # Excel更新工具
│   └── word_tool.py                 # Word报告生成工具
├── knowledge_base/                  # 知识库管理
│   ├── vector_store.py              # 向量存储管理
│   └── embeddings.py                # 嵌入模型管理
├── services/                        # 服务层
│   ├── orchestrator/                # 协调中心
│   │   └── main.py                  # FastAPI应用
│   └── wechat_sandbox/              # 微信沙盒
│       ├── Dockerfile
│       ├── start.sh
│       └── producer_service/        # 消息生产者服务
├── agents/                          # Agent模块
│   └── monitor_agent.py             # 监控Agent
├── scripts/                         # 部署脚本
│   ├── init_knowledge_base.py       # 初始化知识库
│   └── start_all.py                 # 启动所有服务
├── templates/                       # 模板文件
│   └── daily_report.j2              # 报告模板
├── pyproject.toml                   # 项目依赖配置
└── docker-compose.yml               # Docker编排配置
```

## 技术栈

- **Python**: 3.12+
- **LangGraph**: 0.0.50+ (工作流编排)
- **LangChain**: 0.1.0+ (AI工具集成)
- **FastAPI**: 0.104+ (Web框架)
- **Ollama**: 本地AI模型服务 (Qwen3-VL, Qwen3-Embedding-4B)
- **Chroma**: 向量数据库
- **Redis**: 状态存储和缓存
- **Docker**: 容器化部署

## 快速开始

### 方式一：使用Conda虚拟环境（推荐）

#### Windows用户

```bash
# 1. 创建并激活Conda环境
conda create -n wechat-workflow-agent python=3.12


# 2. 激活环境（如果需要）
conda activate wechat-workflow-agent

# 3. 启动基础设施
docker-compose up -d redis ollama

# 4. 拉取AI模型
ollama pull qwen3-vl:latest
ollama pull qwen3-embedding-4b

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
ollama pull qwen3-embedding-4b

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
docker-compose up -d redis ollama
```

#### 3. 拉取AI模型

```bash
ollama pull qwen3-vl:latest
ollama pull qwen3-embedding-4b
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

1. **Monitor Node**: 接收原始消息并载入工作流状态
2. **Multimodal Node**: 调用Qwen3-VL模型进行图文理解，结合RAG检索增强上下文
3. **StateTracker Node**: 更新任务状态，判断任务是否完成
4. **Document Node**: 如果任务完成，调用工具更新Excel和生成Word报告

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
    embedding_model: "qwen3-embedding-4b"

vector_store:
  type: "chroma"
  persist_directory: "./data/chroma_db"
  collection_name: "work_knowledge_base"
```

## API接口

协调中心提供以下主要接口：

- `GET /`: 根路径
- `GET /health`: 健康检查
- `POST /workflow/trigger`: 触发工作流执行
- `GET /workflow/status`: 获取工作流状态

## 扩展性

- **新增节点**: 在 `core/workflows/nodes/` 中创建新节点，并在 `main_workflow.py` 中注册
- **新增工具**: 在 `tools/` 中创建新工具类
- **更换消息源**: 实现 `IMessageSource` 接口，支持企业微信等平台

## 许可证

MIT License
