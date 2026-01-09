# 多模态Agent微信群自动化项目 (LangGraph版)

基于LangGraph的有状态多模态Agent自动化系统，用于监控微信工作群消息，理解图文混合内容，跟踪任务状态，并自动更新台账和生成工作报告。

## 项目架构

本项目采用"中心化工作流引擎 + 外围服务"的混合架构：

- **LangGraph工作流引擎**: 核心处理层，负责从消息理解到文档生成的全过程
- **微信沙盒容器**: 独立的Docker化服务，提供微信客户端运行环境
- **AI与知识库服务**: Ollama提供本地多模态模型，SiliconFlow提供云端Embedding模型，Chroma提供向量数据库
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
- **Ollama**: 本地AI模型服务 (Qwen3-VL)
- **SiliconFlow**: 云AI模型服务 (Qwen3-Embedding)
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
docker-compose up -d redis ollama
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
  siliconflow:
    api_key: "your-api-key"
    base_url: "https://api.siliconflow.cn/v1"
    embedding_model: "Qwen/Qwen3-Embedding-8B"

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

## 微信消息生产者服务

微信沙盒容器提供双生产者模型的消息生产服务，通过Redis和FastAPI暴露消息流供monitor_agent.py消费。

### 架构说明

- **Producer1 (Observer)**: 监控微信群消息界面，检测新消息气泡，返回小截图 + 气泡像素位置
- **Producer2 (Content Fetcher)**: 根据气泡位置点击获取高精度内容（高清图片/文本），返回精确内容
- **Redis Stream**: 使用Redis Streams作为消息队列，支持消息持久化和多消费者
- **FastAPI Server**: 提供SSE流式端点，将precise队列消息实时推送

### 数据流

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
python start_service.py
```

### Docker部署

#### 单实例部署

```bash
cd services/wechat_sandbox
docker-compose up -d
```

docker-compose.yml会启动两个容器：
1. **redis**: Redis消息队列服务
2. **producer_service**: 双生产者服务（包含Linux微信）

#### 多实例部署（多用户多群组）

```bash
cd services/wechat_sandbox
docker-compose -f docker-compose.multi.yml up -d
```

docker-compose.multi.yml会启动多个生产者服务实例：
1. **redis**: Redis消息队列服务
2. **producer_service_1**: 实例1（端口8001/6081/5901）
3. **producer_service_2**: 实例2（端口8002/6082/5902）
4. **producer_service_3**: 实例3（端口8003/6083/5903）

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
   cd services/wechat_sandbox
   docker-compose up -d
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

- `producer_service/queue_manager.py`: Redis队列管理器（使用Redis Streams）
- `producer_service/producer1_observer.py`: 生产者1 - 消息观察者
- `producer_service/producer2_content_fetcher.py`: 生产者2 - 内容获取者
- `producer_service/monitor.py`: 视觉监控器（Linux微信版本）
- `producer_service/detector.py`: 变化检测器
- `producer_service/extractor.py`: 内容提取器（Linux微信版本）
- `producer_service/classifier.py`: 消息类型分类器
- `producer_service/api_server.py`: FastAPI服务器（含Web管理接口）
- `utils/logger.py`: 日志工具
- `utils/config.py`: 配置工具
- `static/index.html`: Web管理界面
- `start_service.py`: 服务启动脚本
- `start.sh`: 容器启动脚本（VNC/noVNC初始化）
- `docker-compose.yml`: 单实例Docker编排配置
- `docker-compose.multi.yml`: 多实例Docker编排配置
- `Dockerfile`: 生产者服务镜像构建（含VNC/noVNC）

## 扩展性

- **新增节点**: 在 `core/workflows/nodes/` 中创建新节点，并在 `main_workflow.py` 中注册
- **新增工具**: 在 `tools/` 中创建新工具类
- **更换消息源**: 实现 `IMessageSource` 接口，支持企业微信等平台

## 许可证

MIT License
