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
├── services/
│   └── wechat_sandbox/              # 微信沙盒服务
│       ├── producer_service/        # 双生产者架构
│       │   ├── extractor.py         # 消息内容提取器（Linux专用）
│       │   ├── classifier.py        # 消息类型分类器
│       │   ├── visual_monitor.py    # 视觉监控器
│       │   ├── change_detector.py   # 变化检测器
│       │   └── api_server.py        # SSE流式API服务器
│       ├── main.py                  # 服务入口
│       └── config.yaml              # 配置文件
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

### 2025-01-10: 平台适配层设计（待实施）
**决策**: 设计PlatformAdapter抽象层支持Windows/Linux跨平台
**原因**:
- 当前 `extractor.py` 仅支持Linux（xdotool/xclip）
- 项目需要支持Windows环境下的微信客户端
- 避免硬编码平台特定逻辑

**实施计划**:
- 创建 `producer_service/platform_adapter.py`
- 定义抽象接口：`click_mouse`, `double_click`, `copy_to_clipboard`, `get_clipboard`
- 实现Linux适配器（xdotool/xclip）
- 实现Windows适配器（pywin32/ctypes）
- 工厂模式根据操作系统选择适配器

## 技术栈版本约束
- Python: 3.9+
- LangChain: 使用requirements.txt中的指定版本
- LangGraph: 使用requirements.txt中的指定版本
- langchain-ollama: >=0.1.0
- Redis: 6.0+
- Docker: 20.10+
- OpenCV: 4.5+
