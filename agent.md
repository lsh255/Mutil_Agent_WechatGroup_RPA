# AI 智能体系统架构文档

> 本文档为 AI 模型提供项目上下文信息，用于理解系统架构、组件职责和开发规范。

## 📋 项目简介

**项目名称**：多模态微信群自动化智能体系统

**项目定位**：基于 LangGraph 的有状态多模态 AI 智能体系统，用于监控微信工作群消息、理解图文混合内容、跟踪任务状态、自动更新台账和生成工作报告。

**核心价值**：
- 自动化处理微信群消息，减少人工干预
- 多模态理解（文本+图像）能力
- 智能任务状态跟踪和管理
- 自动化文档生成（Excel、Word）
- 生产级多实例部署支持
- 浏览器远程访问和配置管理

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     微信沙盒容器 (Docker)                      │
│  ├── Linux 微信客户端                                         │
│  ├── 生产者服务 (http://localhost:8000)                       │
│  │   ├── FastAPI 服务器 (api_server.py)                      │
│  │   │   └── @asynccontextmanager lifespan                    │
│  │   ├── Producer1 (观察器 - 屏幕监控)                         │
│  │   ├── Producer2 (内容获取器 - 消息提取)                     │
│  │   ├── ChangeDetector (变化检测器)                           │
│  │   ├── MessageTypeClassifier (消息分类器)                   │
│  │   └── RedisQueueManager (队列管理器)                        │
│  ├── noVNC 远程桌面 (http://localhost:6080)                   │
│  └── Web UI 管理界面 (http://localhost:8000/api/ui)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ SSE 消息流 / HTTP API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  MonitorAgent (监控智能体)                     │
│  ├── Docker 容器生命周期管理                                    │
│  ├── Server-Sent Events 消息消费                              │
│  ├── 消息解析和预处理                                          │
│  └── 工作流触发                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /workflow/trigger
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Orchestrator (工作流编排中心)                     │
│  ├── FastAPI Web 服务 (http://localhost:8000)                │
│  ├── LangGraph 工作流引擎                                      │
│  ├── API 请求处理和响应                                        │
│  └── 健康检查和监控                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph 工作流引擎                         │
│  ┌─────────┐    ┌──────────────┐    ┌─────────────┐         │
│  │ Monitor │ →  │  Multimodal  │ →  │ StateTracker │         │
│  │  Node   │    │     Node     │    │    Node     │         │
│  └─────────┘    └──────────────┘    └──────┬──────┘         │
│                                             │                 │
│                                   ┌─────────┴─────────┐       │
│                                   │                   │       │
│                           任务完成?  否              │ 是     │
│                                   ↓                   ↓       │
│                                 END              ┌─────────┐  │
│                                                  │Document │  │
│                                                  │  Node   │  │
│                                                  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   外部服务与基础设施                           │
│  ├── Redis (状态缓存、分布式锁、消息队列)                       │
│  ├── Ollama (本地 AI 模型服务)                                │
│  │   ├── Qwen3-VL (视觉理解)                                  │
│  │   └── Qwen3-Chat (对话生成)                                │
│  ├── SiliconFlow (云 AI 模型服务)                             │
│  │   └── Qwen3-Embedding (文本嵌入)                           │
│  ├── ChromaDB (向量数据库)                                    │
│  └── 文档工具 (Word/Excel 生成)                               │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈说明

| 技术/框架 | 版本要求 | 用途 |
|----------|---------|------|
| Python | 3.12+ | 主要开发语言 |
| LangGraph | 0.0.50+ | 工作流编排框架 |
| LangChain | 0.1.0+ | AI 工具集成框架 |
| FastAPI | 0.104+ | Web API 框架 |
| OpenCV | 4.8+ | 图像处理和计算机视觉 |
| Ollama | latest | 本地 AI 模型服务 |
| SiliconFlow | - | 云 AI 模型服务（Embedding） |
| ChromaDB | latest | 向量数据库 |
| Redis | 7.0+ | 缓存、状态存储、消息队列 |
| Docker | 20.0+ | 容器化部署 |
| noVNC | latest | Web 远程桌面 |
| Xvfb & Fluxbox | - | 虚拟显示和窗口管理器 |

### AI 模型配置

```yaml
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"       # 图像理解
    chat_model: "qwen3-72b:latest"           # 对话生成
  siliconflow:
    api_key: "your-api-key"
    base_url: "https://api.siliconflow.cn/v1"
    embedding_model: "Qwen/Qwen3-Embedding-8B"  # 文本嵌入
```

## 🔧 核心组件详解

### 1. 微信沙盒容器（WeChat Sandbox）

**文件路径**：`services/wechat_sandbox/`

**核心职责**：
- 提供隔离的 Linux 微信运行环境
- 通过 noVNC 提供浏览器访问界面
- 实现屏幕监控和消息捕获
- 提供生产者服务 API 接口
- 支持 Web UI 管理界面
- 支持多实例部署

**技术架构**：

```
┌─────────────────────────────────────────┐
│         Docker 容器                      │
│  ┌──────────────────────────────────┐  │
│  │   Linux 微信客户端                │  │
│  │   (无头模式，运行在 Xvfb)        │  │
│  └────────────┬─────────────────────┘  │
│               │ 屏幕截图                  │
│  ┌────────────▼─────────────────────┐  │
│  │   Producer1 (观察器)             │  │
│  │   - ChangeDetector (变化检测)    │  │
│  │   - MessageTypeClassifier       │  │
│  │   - ROI 监控区域管理              │  │
│  └────────────┬─────────────────────┘  │
│               │ 检测到新消息             │
│  ┌────────────▼─────────────────────┐  │
│  │   Producer2 (内容获取器)         │  │
│  │   - 消息气泡提取                  │  │
│  │   - 文本/图像解析                │  │
│  │   - OCR 文字识别                  │  │
│  └────────────┬─────────────────────┘  │
│               │ 结构化消息              │
│  ┌────────────▼─────────────────────┐  │
│  │   RedisQueueManager              │  │
│  │   - Redis Streams                │  │
│  │   - 消息持久化                    │  │
│  │   - 多消费者支持                  │  │
│  └────────────┬─────────────────────┘  │
│               │ SSE / HTTP             │
│  ┌────────────▼─────────────────────┐  │
│  │   FastAPI 服务器                  │  │
│  │   - REST API 端点                │  │
│  │   - SSE 消息流                   │  │
│  │   - Web UI 服务                  │  │
│  └────────────┬─────────────────────┘  │
└───────────────┼────────────────────────┘
                │
        ┌───────▼───────┐
        │  noVNC 界面   │
        │  (端口 6080)  │
        └───────────────┘
```

**关键模块**：

#### 1.1 生产者服务（Producer Service）

**文件**：`producer_service/api_server.py`

**核心功能**：
- FastAPI 服务器，提供 REST API 和 SSE 接口
- 管理生产者服务生命周期（lifespan 管理）
- 提供健康检查和状态查询
- 集成 Web UI 管理界面

**生命周期管理**：
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

**API 端点**：

| 端点 | 方法 | 功能 | 说明 |
|------|------|------|------|
| `/` | GET | 服务信息 | 返回版本和状态 |
| `/health` | GET | 健康检查 | 检查服务健康状态 |
| `/status` | GET | 获取状态 | 获取详细服务状态 |
| `/api/screenshot` | GET | 屏幕截图 | 获取当前屏幕截图 |
| `/api/roi` | POST | 更新ROI | 更新监控区域配置 |
| `/stream` | GET | 消息流 | SSE 实时消息流 |
| `/api/ui` | GET | Web UI | 管理界面 |

#### 1.2 观察器（Producer1 Observer）

**文件**：`producer_service/producer1_observer.py`

**核心功能**：
- 持续监控屏幕变化
- 使用 ROI（感兴趣区域）提高效率
- 检测新消息气泡
- 调用内容获取器处理

**工作流程**：
```
1. 初始化 Xvfb 虚拟显示
2. 配置 ROI 监控区域
3. 循环执行：
   - 捕获屏幕截图
   - 使用 ChangeDetector 检测变化
   - 检测到变化 → 调用 Producer2
   - 使用 MessageTypeClassifier 分类
   - 将消息推送到 Redis
```

#### 1.3 内容获取器（Producer2 Content Fetcher）

**文件**：`producer_service/producer2_content_fetcher.py`

**核心功能**：
- 提取消息气泡边界
- 解析消息内容（文本、图像）
- OCR 文字识别（如需要）
- 生成结构化消息

**消息结构**：
```python
{
    "sender": "发送者",
    "content": "消息内容",
    "message_type": "text",  # text/image/video/link
    "timestamp": "2026-01-09T10:30:00",
    "metadata": {
        "bubble_bbox": [x, y, w, h],
        "has_avatar": True,
        "group_id": "group_123"
    }
}
```

#### 1.4 变化检测器（ChangeDetector）

**文件**：`producer_service/detector.py`

**核心功能**：
- 使用 dHash 算法检测帧间差异
- HSV 颜色空间识别消息气泡
- 轮廓检测和验证
- 阈值和形态学操作

**关键方法**：
```python
class ChangeDetector:
    def compute_dhash(image):        # 计算图像哈希
    def hash_distance(hash1, hash2): # 计算汉明距离
    def detect_changes(current, prev): # 检测显著变化
    def detect_bubbles(image):      # 识别消息气泡
```

**配置参数**：
- `threshold`: 0.05（变化阈值）
- `hash_diff_threshold`: 2（哈希距离阈值）
- `hsv_lower/upper`: HSV 颜色范围（绿色气泡）
- `min_area`: 500（最小气泡面积）

#### 1.5 消息类型分类器（MessageTypeClassifier）

**文件**：`producer_service/classifier.py`

**核心功能**：
- 基于图像特征分类消息类型
- HSV 颜色空间检测图标
- 支持的类型：text、image、video、link、unknown

**分类逻辑**：
```
1. 检测黄色/蓝色图标 → 媒体消息
2. 进一步区分图片 vs 视频
3. 检测蓝色链接图标 → 链接消息
4. 检查宽高比 → 辅助判断
5. 默认 → 文本消息
```

#### 1.6 Redis 队列管理器（RedisQueueManager）

**文件**：`producer_service/queue_manager.py`

**核心功能**：
- 使用 Redis Streams 实现消息队列
- 支持多消费者并发读取
- 消息持久化和容错
- 提供队列状态查询

**数据结构**：
```
Stream: wechat_messages
Fields: sender, content, message_type, timestamp, metadata
```

#### 1.7 Web UI 管理界面

**文件**：`static/index.html`

**核心功能**：
- 实时查看屏幕截图
- 可视化配置 ROI 区域
- 服务状态监控
- 消息流实时显示
- 响应式设计，支持移动端

**界面布局**：
```
┌─────────────────────────────────┐
│         标题栏                    │
├──────────────┬──────────────────┤
│              │   状态卡片        │
│              │   - 服务状态      │
│   屏幕截图    │   - 消息计数      │
│   (noVNC)    │   - 检测器状态    │
│              │                   │
│              │   ROI 配置        │
│              │   - 坐标输入      │
│              │   - 更新按钮      │
│              │                   │
│              │   消息流          │
│              │   - 实时显示      │
└──────────────┴──────────────────┘
```

**主要功能模块**：

1. **VNC 集成**
   - 嵌入 noVNC iframe，提供远程桌面访问
   - 支持全屏模式和窗口模式切换
   - 实时同步微信界面状态

2. **ROI 配置面板**
   - 左边距（Left）、上边距（Top）、宽度（Width）、高度（Height）输入
   - 实时预览 ROI 区域
   - 一键应用配置到 Producer1

3. **状态监控**
   - 服务运行状态（运行/停止/错误）
   - 消息计数统计
   - 检测器状态（ChangeDetector、MessageTypeClassifier）
   - Redis 连接状态

4. **消息流显示**
   - 实时显示捕获的微信消息
   - 消息类型图标（文本、图片、视频、链接）
   - 发送者头像和时间戳
   - 支持滚动查看历史消息

### 2. 多实例部署支持

**文件**：`services/wechat_sandbox/docker-compose.multi.yml`

**核心特性**：
- 支持同时运行多个微信实例
- 每个实例独立端口映射
- 共享 Redis 队列
- 独立的数据卷隔离

**端口映射**：

| 实例 | FastAPI | noVNC | VNC |
|------|---------|-------|-----|
| 1 | 8001 | 6081 | 5901 |
| 2 | 8002 | 6082 | 5902 |
| 3 | 8003 | 6083 | 5903 |

**配置详情**：
```yaml
producer_service_1:
  build: .
  container_name: wechat_producer_service_1
  ports:
    - "8001:8000"    # FastAPI service port
    - "6081:6080"    # noVNC Web interface port
    - "5901:5900"    # VNC service port
  environment:
    - DISPLAY=:99
    - REDIS_HOST=redis
    - VNC_PASSWORD=vnc123
    - INSTANCE_ID=1
  volumes:
    - wechat_data_1:/app/data
    - wechat_config_1:/root/.deepin-wine
  depends_on:
    - redis
```

**启动命令**：
```bash
docker-compose -f docker-compose.multi.yml up -d
```

**访问地址**：
- 实例 1: http://localhost:8001/api/ui, http://localhost:6081
- 实例 2: http://localhost:8002/api/ui, http://localhost:6082
- 实例 3: http://localhost:8003/api/ui, http://localhost:6083

### 3. 测试框架

**文件路径**：`services/wechat_sandbox/tests/`

**测试类型**：
1. **单元测试**：测试单个组件
   - `test_queue_manager.py` - RedisQueueManager 队列管理器
   - `test_producer_service.py` - 生产者服务组件（ChangeDetector、MessageTypeClassifier）

2. **API 测试**：测试 FastAPI 接口
   - `test_api_server.py` - 所有 REST API 端点

3. **集成测试**：测试完整流程
   - `test_integration.py` - 端到端工作流
   - Docker 服务测试
   - 多实例测试

**测试工具**：
- pytest + pytest-asyncio
- pytest-html（HTML 报告）
- pytest-cov（覆盖率）
- Mock/patch（外部依赖隔离）
- numpy（视觉组件测试）

**运行测试**：
```bash
# 运行所有测试
pytest tests/ -v --html=reports/test_report.html

# 运行特定测试
pytest tests/test_queue_manager.py -v
pytest tests/test_producer_service.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看详细输出
pytest tests/ -v -s
```

**测试修复记录**：
- 修复了 `test_producer_service.py` 中的错误：
  - 移除了不存在的 `ConsumerProcessor` 导入
  - 更新了 `ChangeDetector` 测试方法使用正确的阈值（0.05）
  - 修正了 `detect_changes` 返回值检查（bool 而非 len）
  - 为 `MessageTypeClassifier` 测试创建了 numpy 图像输入
  - 修正了分类结果断言（字符串而非 dict）

### 4. MonitorAgent（监控智能体）

**文件路径**：`agents/monitor_agent.py`

**核心职责**：
- 管理微信沙盒 Docker 容器的启动和停止
- 订阅微信消息流（Server-Sent Events）
- 解析和验证消息格式
- 触发工作流执行

**关键方法**：
```python
class MonitorAgent:
    async def start_container()    # 启动微信沙盒容器
    async def stop_container()     # 停止容器
    async def start()              # 开始监控消息
    def stop()                     # 停止监控
    def set_message_callback()     # 设置消息回调函数
```

**端口映射**：
- `5800` → noVNC Web 界面
- `5900` → VNC 协议
- `6789` → 生产者服务 API

**使用示例**：
```python
from agents.monitor_agent import MonitorAgent

agent = MonitorAgent(orchestrator_url="http://localhost:8000")
await agent.start()
# ... 运行 ...
agent.stop()
```

### 5. Orchestrator（工作流编排中心）

**文件路径**：`services/orchestrator/main.py`

**核心职责**：
- 提供 RESTful API 接口
- 管理工作流实例和执行
- 处理并发请求和状态管理
- 返回执行结果和错误处理

**API 端点**：

| 端点 | 方法 | 功能 | 请求示例 |
|------|------|------|----------|
| `/` | GET | 服务信息 | - |
| `/health` | GET | 健康检查 | - |
| `/workflow/trigger` | POST | 触发工作流 | 见下方 |
| `/workflow/status` | GET | 查询状态 | - |

**触发工作流请求格式**：
```json
POST /workflow/trigger
{
  "sender": "张三",
  "content": "请生成本周工作周报",
  "message_type": "text",
  "group_id": "group_123",
  "timestamp": "2026-01-09T10:30:00",
  "metadata": {
    "priority": "high",
    "mentions": ["@all"]
  }
}
```

**响应格式**：
```json
{
  "success": true,
  "workflow_id": "wf_20260109_103000_abc123",
  "status": "completed",
  "result": {
    "task_status": "completed",
    "document_path": "/output/report_20260109.docx"
  }
}
```

### 6. LangGraph 工作流节点

**文件路径**：`core/workflows/`

#### 6.1 监控节点 (Monitor Node)

**文件**：`nodes/monitor_node.py`

**功能**：
- 接收原始消息
- 验证消息格式和类型
- 消息预处理（清理、标准化）
- 路由到下一个节点

**输入**：`raw_message: RawMessage`
**输出**：更新后的 `AgentState`

#### 6.2 多模态分析节点 (Multimodal Node)

**文件**：`nodes/multimodal_node.py`

**功能**：
- **文本消息**：使用 LLM 进行意图识别和任务提取
- **图片消息**：使用视觉模型（Qwen3-VL）进行图像内容理解
- **混合消息**：融合文本和图像信息进行综合分析
- **RAG 增强**：从向量数据库检索相关上下文

**处理流程**：
```
消息输入 → 判断类型 → 选择模型 → 生成分析结果 → RAG检索 → 融合结果 → 输出
```

**AI 能力**：
- 文本意图识别（任务类型、紧急程度、执行者）
- 图像内容识别（截图、文档、照片、二维码）
- 实体提取（人名、时间、地点、任务内容）
- 上下文理解（结合历史对话和知识库）

#### 6.3 状态跟踪节点 (StateTracker Node)

**文件**：`nodes/state_tracker_node.py`

**功能**：
- 维护任务状态机（待处理 → 进行中 → 已完成）
- 记录任务上下文和历史
- 判断任务是否完成
- 更新 Redis 缓存

**状态转换**：
```
┌──────────┐    任务开始    ┌──────────┐
│  待处理   │ ───────────→ │  进行中   │
└──────────┘               └──────────┘
     ↑                        │
     │                    任务完成
     │                        ↓
┌──────────┐              ┌──────────┐
│  已完成   │ ←─────────── │  进行中   │
└──────────┘               └──────────┘
```

#### 6.4 文档生成节点 (Document Node)

**文件**：`nodes/document_node.py`

**功能**：
- 生成 Excel 台账更新
- 生成 Word 工作报告
- 文档模板管理
- 输出文件存储

**文档类型**：
1. **Excel 台账**
   - 任务列表
   - 进度追踪
   - 负责人分配

2. **Word 报告**
   - 工作总结
   - 任务详情
   - 下一步计划

**条件路由**：
```python
def should_generate_document(state: AgentState) -> str:
    """Determine if document should be generated"""
    analysis = state.get("multimodal_analysis", {})
    if any(signal in analysis.get("text", "") for signal in ["complete", "end", "report"]):
        return "yes"
    return "no"
```

## 📦 数据模型

### 核心数据结构

#### RawMessage（原始消息）

```python
@dataclass
class RawMessage:
    sender: str              # 发送者
    content: str             # 消息内容
    message_type: str        # 消息类型
    timestamp: str           # 时间戳
    metadata: dict           # 元数据
```

#### AgentState（智能体状态）

```python
@dataclass
class AgentState:
    raw_message: RawMessage          # 原始消息
    message_analysis: dict            # 消息分析结果
    multimodal_analysis: dict         # 多模态分析结果
    task_status: str                  # 任务状态
    task_history: List[dict]          # 任务历史
    document_generated: bool         # 是否生成文档
    document_path: str                # 文档路径
```

#### RedisMessage（Redis 消息）

```python
{
    "sender": "张三",
    "content": "任务已完成",
    "message_type": "text",
    "timestamp": "2026-01-09T10:30:00",
    "metadata": {
        "bubble_bbox": [100, 200, 300, 150],
        "has_avatar": True,
        "group_id": "group_123"
    }
}
```

## 🔀 数据流转

### 消息处理流程

```
1. 微信消息
   ↓
2. Producer1 屏幕监控
   - ChangeDetector 检测变化
   - MessageTypeClassifier 分类
   ↓
3. Producer2 内容提取
   - 消息气泡提取
   - 文本/图像解析
   ↓
4. RedisQueueManager
   - 推送到 Redis Streams
   ↓
5. FastAPI SSE 端点
   - 实时推送消息流
   ↓
6. MonitorAgent
   - 订阅 SSE 消息
   - 解析和验证
   ↓
7. Orchestrator
   - 接收 HTTP POST 请求
   - 触发 LangGraph 工作流
   ↓
8. LangGraph 节点
   - Monitor Node: 消息预处理
   - Multimodal Node: AI 分析
   - StateTracker Node: 状态跟踪
   - Document Node: 文档生成（条件触发）
   ↓
9. 输出结果
   - 更新 Excel 台账
   - 生成 Word 报告
```

### 状态流转

```
消息接收 → 消息分析 → 任务识别 → 状态更新 → 文档生成（可选）→ 完成
```

## 🗂️ 项目目录结构

```
Mutil_Agent_WechatGroup_RPA/
├── agent.md                      # AI 智能体系统架构文档
├── claude.md                     # 项目记忆文档（英文）
├── claude-cn.md                  # 项目记忆文档（中文）
├── CLAUDE.md                     # AI 开发规范
│
├── agents/                       # 智能体模块
│   ├── __init__.py
│   └── monitor_agent.py          # 监控智能体
│
├── core/                         # 核心模块
│   ├── __init__.py
│   ├── workflows/                # 工作流定义
│   │   ├── __init__.py
│   │   ├── agent_graph.py        # LangGraph 工作流图
│   │   └── state.py              # 状态定义
│   └── nodes/                    # 工作流节点
│       ├── __init__.py
│       ├── monitor_node.py       # 监控节点
│       ├── multimodal_node.py    # 多模态分析节点
│       ├── state_tracker_node.py # 状态跟踪节点
│       └── document_node.py     # 文档生成节点
│
├── services/                     # 服务模块
│   ├── orchestrator/             # 工作流编排服务
│   │   ├── main.py               # FastAPI 主服务
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── wechat_sandbox/           # 微信沙盒服务
│       ├── producer_service/     # 生产者服务
│       │   ├── __init__.py
│       │   ├── api_server.py     # FastAPI 服务器
│       │   ├── queue_manager.py  # Redis 队列管理器
│       │   ├── producer1_observer.py    # 观察器
│       │   ├── producer2_content_fetcher.py  # 内容获取器
│       │   ├── detector.py       # 变化检测器
│       │   └── classifier.py     # 消息类型分类器
│       │
│       ├── static/               # 静态资源
│       │   └── index.html        # Web UI 管理界面
│       │
│       ├── tests/                # 测试文件
│       │   ├── __init__.py
│       │   ├── conftest.py       # pytest 配置和 fixtures
│       │   ├── test_queue_manager.py
│       │   ├── test_producer_service.py
│       │   └── test_api_server.py
│       │
│       ├── QUICKSTART.md         # 快速开始指南
│       ├── docker-compose.yml    # 单实例部署配置
│       ├── docker-compose.multi.yml  # 多实例部署配置
│       ├── requirements.txt
│       └── Dockerfile
│
├── output/                       # 输出目录
│   ├── excel/                    # Excel 台账
│   └── reports/                  # Word 报告
│
├── config/                       # 配置文件
│   ├── config.yaml               # 主配置文件
│   ├── ai_config.yaml            # AI 模型配置
│   └── redis_config.yaml         # Redis 配置
│
└── logs/                         # 日志目录
    ├── producer_service.log
    ├── orchestrator.log
    └── monitor_agent.log
```

## ⚙️ 配置管理

### 配置文件优先级

```
命令行参数 > 环境变量 > 配置文件 > 默认值
```

### 环境变量命名规范

- 服务配置：`{SERVICE}_{CONFIG_KEY}`（如 `PRODUCER_SERVICE_PORT`）
- AI 配置：`AI_{MODEL}_{KEY}`（如 `AI_OLLAMA_BASE_URL`）
- Redis 配置：`REDIS_{KEY}`（如 `REDIS_HOST`）
- Docker 配置：`{CONTAINER}_{KEY}`（如 `VNC_PASSWORD`）

### 主要配置项

#### Producer Service 配置

```yaml
producer_service:
  host: "0.0.0.0"
  port: 8000
  redis:
    host: "redis"
    port: 6379
    db: 0
    stream_name: "wechat_messages"
  producer1:
    display: ":99"
    monitor_interval: 0.5  # 秒
    roi:
      left: 0
      top: 0
      width: 1920
      height: 1080
  producer2:
    ocr_enabled: true
    image_quality: 95
```

#### AI 模型配置

```yaml
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
    chat_model: "qwen3-72b:latest"
    timeout: 30
  siliconflow:
    api_key: "${SILICONFLOW_API_KEY}"
    base_url: "https://api.siliconflow.cn/v1"
    embedding_model: "Qwen/Qwen3-Embedding-8B"
    timeout: 30
```

#### LangGraph 配置

```yaml
langgraph:
  workflow:
    name: "wechat_agent_workflow"
    state_schema: "AgentState"
    interrupt_before: []
    interrupt_after: []
  nodes:
    - monitor
    - multimodal
    - state_tracker
    - document
```

## 🚀 部署指南

### 单实例部署

**启动 Redis**：
```bash
docker run -d --name redis -p 6379:6379 redis:7.0
```

**启动微信沙盒**：
```bash
cd services/wechat_sandbox
docker-compose up -d
```

**验证部署**：
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f producer_service

# 访问 Web UI
# http://localhost:8000/api/ui

# 访问 noVNC
# http://localhost:6080
```

### 多实例部署

**启动多实例**：
```bash
cd services/wechat_sandbox
docker-compose -f docker-compose.multi.yml up -d
```

**访问不同实例**：
- 实例 1: http://localhost:8001/api/ui, http://localhost:6081
- 实例 2: http://localhost:8002/api/ui, http://localhost:6082
- 实例 3: http://localhost:8003/api/ui, http://localhost:6083

**验证多实例**：
```bash
# 检查所有容器状态
docker-compose -f docker-compose.multi.yml ps

# 查看特定实例日志
docker logs wechat_producer_service_1
docker logs wechat_producer_service_2
docker logs wechat_producer_service_3
```

## 🧪 测试指南

### 运行测试

```bash
cd services/wechat_sandbox

# 运行所有测试
pytest tests/ -v

# 生成 HTML 报告
pytest tests/ -v --html=reports/test_report.html

# 运行特定测试文件
pytest tests/test_queue_manager.py -v
pytest tests/test_producer_service.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

### 测试类型

1. **单元测试**
   - 测试单个组件功能
   - 使用 mock 隔离外部依赖
   - 快速执行，无网络/数据库依赖

2. **API 测试**
   - 测试 FastAPI 端点
   - 验证请求/响应格式
   - 测试错误处理

3. **集成测试**
   - 测试完整工作流
   - 需要 Redis 和 Docker 环境
   - 验证组件间协作

## 📊 性能优化

### 微信沙盒优化

1. **ROI 配置**
   - 只监控消息区域，减少截图面积
   - 提高检测效率，降低 CPU 使用率

2. **检测间隔**
   - 根据消息频率调整监控间隔
   - 建议值：0.3-1.0 秒

3. **图像处理**
   - 降低截图分辨率（如 720p）
   - 使用灰度图像进行变化检测

### LangGraph 工作流优化

1. **缓存策略**
   - Redis 缓存分析结果
   - 避免重复计算

2. **并发控制**
   - 使用异步处理提高吞吐量
   - 限制并发工作流数量

3. **模型选择**
   - 根据任务复杂度选择合适的模型
   - 简单任务使用小模型

## 🔒 安全注意事项

1. **敏感信息保护**
   - 不要在代码中硬编码 API Key
   - 使用环境变量或密钥管理系统
   - 日志中脱敏敏感信息

2. **网络安全**
   - 生产环境使用 HTTPS
   - 配置防火墙规则
   - 限制 API 访问频率

3. **容器安全**
   - 使用非 root 用户运行容器
   - 定期更新基础镜像
   - 限制容器资源使用

## 🛠️ 故障排查

### 微信沙盒问题

**问题：无法启动微信客户端**
- 检查 Xvfb 虚拟显示是否正常
- 查看 Docker 容器日志：`docker logs wechat_producer_service`
- 确认 DISPLAY 环境变量配置正确

**问题：无法检测到新消息**
- 检查 ROI 区域配置是否正确
- 查看屏幕截图：`curl http://localhost:8000/api/screenshot`
- 调整 ChangeDetector 阈值参数

**问题：noVNC 无法连接**
- 检查 noVNC 容器是否正常运行
- 确认 VNC 密码配置正确
- 查看浏览器控制台错误信息

### LangGraph 工作流问题

**问题：工作流执行失败**
- 检查 Orchestrator 日志
- 验证 AI 模型服务是否可用
- 确认 Redis 连接正常

**问题：状态跟踪异常**
- 检查 Redis 缓存数据
- 验证状态转换逻辑
- 查看工作流执行日志

## 📚 参考资源

- [LangGraph 官方文档](https://python.langchain.com/docs/langgraph)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Ollama 官方文档](https://ollama.ai/docs)
- [Redis Streams 文档](https://redis.io/docs/data-types/streams/)
- [OpenCV Python 教程](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

## 📝 开发规范

### 代码风格

- 遵循 PEP 8 Python 编码规范
- 使用类型注解（Type Hints）
- 编写清晰的文档字符串（Docstrings）
- 函数和变量命名使用 snake_case
- 类名使用 PascalCase

### Git 提交规范

```
<类型>: <简要描述>

类型：新增 | 修复 | 重构 | 优化 | 文档 | 配置
```

示例：
```
新增: 添加多实例 Docker 部署支持
修复: 修复 ChangeDetector 阈值配置错误
优化: 优化 ROI 检测性能
```

### 测试要求

1. 新功能必须编写单元测试
2. 测试覆盖率不低于 80%
3. 提交前运行所有测试
4. 集成测试需要完整的 Docker 环境

## 🎯 项目路线图

### 已完成 ✅

- [x] 微信沙盒容器化部署
- [x] 屏幕监控和消息捕获
- [x] FastAPI 服务和 SSE 消息流
- [x] LangGraph 工作流引擎
- [x] 多模态 AI 分析（文本+图像）
- [x] 任务状态跟踪
- [x] Web UI 管理界面
- [x] noVNC 远程桌面集成
- [x] 多实例 Docker 部署
- [x] Redis 队列管理
- [x] 单元测试和集成测试
- [x] 文档生成（Excel/Word）

### 进行中 🚧

- [ ] 完善 RAG 增强功能
- [ ] 优化 AI 模型性能
- [ ] 增加更多消息类型识别
- [ ] 改进 ROI 自动配置

### 计划中 📋

- [ ] 支持更多 AI 模型
- [ ] 添加消息模板系统
- [ ] 实现多用户权限管理
- [ ] 支持自定义工作流
- [ ] 添加性能监控和告警
- [ ] 支持云原生部署（Kubernetes）
- [ ] 移动端应用
