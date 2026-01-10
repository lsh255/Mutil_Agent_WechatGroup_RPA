# 项目记忆文档

## 项目基本信息
- 项目名称：多模态Agent微信群自动化项目
- 技术栈：Python, LangChain, LangGraph, FastAPI, Redis, Docker, OpenCV, mss, xdotool, xclip
- 项目类型：多用户/多智能体系统
- 创建时间：2025-01-10

## 目录结构
```
Mutil_Agent_WechatGroup_RPA/
├── agents/                           # 统一的智能体模块目录（已重构）
│   ├── intent_agent.py              # 意图识别智能体
│   ├── visual_agent.py              # 视觉定位智能体
│   ├── decision_agent.py            # 决策智能体
│   ├── monitor_agent.py             # 监控智能体
│   └── prompts/                     # 智能体提示词目录
├── docker/                          # Docker相关配置（统一管理）
│   ├── sandbox/                     # WeChat Sandbox Docker配置
│   │   ├── Dockerfile               # 生产环境基础镜像
│   │   ├── Dockerfile.test          # 测试环境镜像
│   │   └── docker-compose.test.yml  # 测试环境编排
│   ├── compose/                     # Docker Compose配置
│   │   ├── docker-compose.yml       # 生产单实例部署
│   │   ├── docker-compose.multi.yml # 生产多实例部署
│   │   └── docker-compose.sandbox.test.yml # 沙箱测试环境
│   ├── orchestrator/                # Orchestrator Docker配置
│   ├── scripts/                     # 统一启动脚本目录
│   │   ├── start_wechat.sh          # 微信沙箱启动脚本
│   │   ├── start_wechat_sandbox.bat # Windows启动脚本
│   │   └── start_sandbox.sh         # 通用沙箱启动脚本
│   └── frontend/                    # Frontend Docker配置
├── services/
│   └── wechat_sandbox/              # 微信沙盒服务（业务代码和文档）
│       ├── api/                     # API接口层
│       ├── core/                    # 核心业务逻辑层
│       ├── services/                # 服务编排层
│       ├── utils/                   # 工具模块
│       ├── tests/                   # 测试文件
│       ├── archive/                 # 归档文件
│       ├── README.md                # 项目总览
│       ├── QUICKSTART.md            # 快速启动指南
│       ├── ARCHITECTURE.md          # 架构说明
│       ├── BUSINESS_LOGIC_TEST.md   # 测试指南
│       ├── main.py                  # 服务入口
│       ├── backup_start.py          # 备用启动脚本
│       ├── config.yaml              # 配置文件
│       ├── config.production.yaml   # 生产环境配置
│       ├── requirements.txt         # Python依赖
│       └── run_tests.py             # 测试运行脚本
├── workflows/                        # 工作流定义
│   └── main_workflow.py             # LangGraph主工作流
├── utils/                           # 工具模块
│   ├── logger.py                    # 日志工具
│   └── config.py                    # 配置工具
└── 多模态Agent微信群自动化项目：架构设计文档V2.md  # 官方架构文档
```

## 开发规则（必须遵守）

### 智能体模块规范
- 所有智能体必须统一放在 `agents/` 目录下
- 智能体必须遵循统一的类结构：
  - `__init__`: 初始化配置和依赖
  - `_build_chain`: 构建LangChain Runnable链
  - `invoke`: 同步调用接口
  - `ainvoke`: 异步调用接口
- 智能体提示词统一放在 `agents/prompts/` 目录
- 智能体禁止直接暴露为前端服务，必须通过LangGraph Orchestrator-Worker模式调用
- 保持向后兼容性：保留原始 `invoke/ainvoke` 函数签名

### wechat_sandbox服务规范
- 采用双生产者架构：
  - Producer1 (Observer): 检测消息气泡生成小截图
  - Producer2 (ContentFetcher): 精确获取消息内容（文本/媒体）
- 使用Redis Stream队列管理消息：
  - 原始消息队列：存储小截图
  - 精确消息队列：存储完整内容
- SSE流式接口：`/stream` 端点向消费者推送消息
- 消息锁定机制：使用 Redis SET NX 避免重复处理
- ROI管理：支持多个监控区域（屏幕坐标）

### 日志规范
- 使用项目统一的日志工具 `utils.logger.logger`
- 日志级别选择：
  - ERROR: 功能异常、需要人工介入（数据库连接失败、API调用异常）
  - WARN: 潜在问题、但程序可继续（配置缺失用默认值、重试后成功）
  - INFO: 关键业务节点（用户登录登出、订单状态变更、任务开始/结束）
  - DEBUG: 调试信息（入参出参、SQL语句、缓存命中情况）
- 必须添加日志的位置：
  - try-catch 的 catch 块（logger.error）
  - 外部调用前后（DEBUG → INFO/ERROR）
  - 业务入口（INFO）
  - 状态变更（INFO）
  - 重要条件分支（DEBUG）

## 架构约定

### LangGraph多智能体架构
- 采用 Orchestrator-Worker 模式
- Orchestrator负责任务分发和协调
- Worker（各类智能体）负责具体业务处理
- 通过Redis Checkpoint机制实现状态持久化

### 智能体交互流程
1. 用户意图识别 → IntentAgent
2. 视觉定位 → VisualAgent（生成屏幕坐标）
3. 沙盒启动 → Sandbox Launcher Node
4. 消息监控 → wechat_sandbox服务
5. 决策执行 → DecisionAgent

### 消息处理流程
1. VisualMonitor 检测屏幕变化
2. ChangeDetector 计算dHash识别新消息
3. Classifier 分类消息类型（text/image/video）
4. ContentFetcher 提取精确内容
5. API Server 通过SSE推送消息
6. Agent Consumer 接收并处理消息

## 历史决策记录

### 2025-01-10: 智能体模块统一
**决策**: 将 `intent_recognition/`, `visual_locator/`, `agent_decision/` 统一到 `agents/` 目录
**原因**: 
- 避免模块分散，提高代码可维护性
- 统一智能体接口规范，便于LangGraph集成
- 避免直接暴露为前端服务，遵循微服务最佳实践

**实施**:
- 创建 `agents/prompts/` 目录迁移提示词文件
- 将三个模块重构为统一的智能体类结构
- 保持向后兼容性，保留原始函数签名

### 2025-01-10: wechat_sandbox双生产者架构
**决策**: 采用双生产者架构（Observer + ContentFetcher）
**原因**:
- 分离消息检测和内容获取，提高性能
- 支持高并发场景下的消息处理
- 降低单一生产者的负载压力

**实施**:
- Producer1: 检测消息气泡，生成小截图推送到原始队列
- Producer2: 从原始队列消费，提取精确内容推送到精确队列
- 使用Redis Stream XREADGROUP实现消费者组模式

### 2025-01-10: SSE流式传输
**决策**: 使用Server-Sent Events (SSE)推送消息
**原因**:
- 实时性要求高，HTTP轮询效率低
- 单向通信场景，SSE比WebSocket更轻量
- 原生支持断线重连

**实施**:
- FastAPI实现 `/stream` 端点
- 使用 `asyncio.Queue` 和 `Event` 管理客户端连接
- 支持多客户端并发连接

### 2025-01-10: 平台适配层设计
**决策**: 设计PlatformAdapter抽象层支持Windows/Linux跨平台
**原因**:
- 当前 `extractor.py` 仅支持Linux（xdotool/xclip）
- 项目需要支持Windows环境下的微信客户端
- 避免硬编码平台特定逻辑

**实施**:
- 创建 `core/platform/adapter.py`
- 定义抽象接口：`click_mouse`, `double_click`, `copy_to_clipboard`, `get_clipboard`
- 实现Linux适配器（xdotool/xclip）
- 实现Windows适配器（pywin32/ctypes）
- 工厂模式根据操作系统选择适配器

### 2025-01-10: wechat_sandbox目录结构重构（方案一）
**决策**: 采用方案一重构 `wechat_sandbox` 目录结构
**原因**:
- 原目录结构杂乱，`app/` 和 `producer_service/` 职责不清晰
- 核心业务逻辑分散，难以维护
- 缺乏清晰的功能分层

**新目录结构**:
```
wechat_sandbox/
├── api/                           # API接口层
│   ├── __init__.py               # FastAPI应用入口（统一路由注册）
│   ├── config.py                 # 配置管理路由
│   ├── instance.py               # 服务实例管理路由
│   ├── stream.py                 # SSE流式接口
│   └── health.py                 # 健康检查接口
├── core/                          # 核心业务逻辑层
│   ├── producer/                 # 消息生产者
│   │   ├── monitor.py            # 视觉监控器
│   │   ├── observer.py           # 消息气泡观察者
│   │   └── content_fetcher.py    # 精确内容获取器
│   ├── queue/                    # Redis队列管理
│   │   └── manager.py
│   ├── detector/                 # 变化检测与边界识别
│   │   └── detector.py
│   ├── extractor/                # 消息内容提取
│   │   └── extractor.py
│   ├── classifier/               # 消息类型分类
│   │   └── classifier.py
│   └── platform/                 # 跨平台适配层
│       └── adapter.py
├── services/                      # 服务编排层
│   └── producer_service.py       # 生产者服务编排
├── utils/                         # 工具模块
│   ├── logger.py
│   └── config.py
├── config.yaml                    # 配置文件
└── main.py                        # 统一入口脚本
```

**实施**:
- 创建备份目录 `wechat_sandbox.backup/`
- 新建 `api/` 目录迁移所有API路由
- 新建 `core/` 目录迁移核心业务逻辑（按功能划分子目录）
- 新建 `services/` 目录实现服务编排层
- 重写 `main.py` 使用新的目录结构
- 更新 `Dockerfile` 和测试文件

**关键改进**:
- 清晰的分层架构（API → Services → Core）
- 按功能组织核心逻辑，提高可维护性
- 统一的入口点（`api/__init__.py` 注册所有路由）
- 服务编排层统一管理组件生命周期

### 2025-01-10: Docker和启动脚本统一管理
**决策**: 将Docker相关文件和启动脚本从 `wechat_sandbox/` 迁移到 `docker/` 统一管理
**原因**:
- Docker配置和启动脚本是基础设施，不属于业务代码
- 避免业务代码目录杂乱，提高可维护性
- 便于跨服务复用Docker配置
- 符合微服务最佳实践：基础设施与业务代码分离

**实施**:
- 迁移Docker文件到 `docker/sandbox/`：
  - `Dockerfile` - 生产环境基础镜像
  - `Dockerfile.test` - 测试环境镜像
  - `docker-compose.test.yml` - 测试环境编排
- 迁移Docker Compose文件到 `docker/compose/`：
  - `docker-compose.yml` - 生产单实例部署
  - `docker-compose.multi.yml` - 生产多实例部署
  - `docker-compose.sandbox.test.yml` - 沙箱测试环境
- 迁移启动脚本到 `docker/scripts/`：
  - `start_wechat.sh` - 微信沙箱启动脚本
  - `start_wechat_sandbox.bat` - Windows启动脚本
  - `start_sandbox.sh` - 通用沙箱启动脚本
- 保留配置文件在 `services/wechat_sandbox/`：
  - `config.yaml` - WeChat特定配置，与业务代码紧密相关
  - `config.production.yaml` - 生产环境配置
- 保留文档文件在 `services/wechat_sandbox/`：
  - `README.md` - 项目总览
  - `QUICKSTART.md` - 快速启动指南
  - `ARCHITECTURE.md` - 架构说明
  - `BUSINESS_LOGIC_TEST.md` - 测试指南
- 删除 `CONTEXT.md`（与 README.md 内容重复）

**关键改进**:
- 基础设施与业务代码分离，职责更清晰
- Docker配置集中管理，便于版本控制和复用
- 启动脚本统一目录，避免散落在各处
- 更新所有相关文档中的路径引用
- 配置文件保留在业务目录，与代码紧密耦合

## 技术栈版本约束
- Python: 3.9+
- LangChain: 使用requirements.txt中的指定版本
- LangGraph: 使用requirements.txt中的指定版本
- langchain-ollama: >=0.1.0
- Redis: 6.0+
- Docker: 20.10+
- OpenCV: 4.5+
