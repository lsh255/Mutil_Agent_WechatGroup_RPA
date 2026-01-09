# WeChat 沙箱服务 - 技术上下文文档

> 本文档提供 WeChat 沙箱服务的完整技术上下文，包括架构设计、组件职责、数据流和开发约定。

## 项目概述

**服务名称**: WeChat Sandbox Service (微信沙箱服务)

**核心价值**: 提供隔离的 Linux 微信运行环境，支持多实例部署，实现消息监控、内容提取和远程管理。

**主要功能**:
- Linux 微信客户端的容器化运行
- 实时屏幕监控和消息气泡检测
- 精确内容提取（文本/图片/视频）
- Redis Stream 消息队列管理
- FastAPI RESTful API 和 SSE 流式输出
- Web UI 管理界面
- 多实例部署支持

## 技术栈

| 技术/框架 | 版本 | 用途 |
|----------|------|------|
| Python | 3.12+ | 主开发语言 |
| FastAPI | 0.104+ | Web API 框架 |
| OpenCV | 4.8+ | 图像处理和计算机视觉 |
| Redis | 7.0+ | 消息队列和状态缓存 |
| Docker | 20.0+ | 容器化部署 |
| Ubuntu | 22.04 | 基础操作系统 |
| Xvfb | - | 虚拟显示服务 |
| Fluxbox | - | 窗口管理器 |
| noVNC | - | Web 远程桌面 |
| PyYAML | - | 配置文件解析 |

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container: wechat_sandbox             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Linux WeChat Client (GUI App)                   │  │
│  │           - 运行在 Xvfb 虚拟显示器                         │  │
│  │           - 通过 noVNC 远程访问                           │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ 屏幕捕获                              │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │         Producer1: Observer (屏幕观察者)                  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ VisualMonitor: 屏幕监控器                      │  │  │
│  │         │ - 定位微信窗口                                 │  │  │
│  │         │ - 定时截取屏幕                                 │  │  │
│  │         │ - ROI 区域管理                                 │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ ChangeDetector: 变化检测器                    │  │  │
│  │         │ - dHash 算法检测变化                          │  │  │
│  │         │ - HSV 颜色空间识别气泡                         │  │  │
│  │         │ - 轮廓检测和验证                               │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ MessageTypeClassifier: 消息分类器            │  │  │
│  │         │ - 文本/图片/视频/链接分类                      │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ 新消息检测                             │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │      Producer2: Content Fetcher (内容获取者)             │  │
│  │      ┌─────────────────────────────────────────────────┐  │  │
│  │      │ PrecisionContentFetcher: 精确内容提取器         │  │  │
│  │      │ - 模拟鼠标点击气泡                               │  │  │
│  │      │ - 双击复制文本内容                               │  │  │
│  │      │ - 点击打开媒体查看器                             │  │  │
│  │      │ - 截取高清图片                                   │  │  │
│  │      └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ 结构化消息                             │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │         Redis Queue Manager (队列管理器)                 │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ stream_raw: 原始消息队列                       │  │  │
│  │         │ - Producer1 入队                              │  │  │
│  │         │ - Producer2 消费                              │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ stream_precise: 精确消息队列                  │  │  │
│  │         │ - Producer2 入队                              │  │  │
│  │         │ - 外部消费者消费                              │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          │ SSE/HTTP API                          │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │         FastAPI Server (API 服务)                       │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ REST API Endpoints                            │  │  │
│  │         │ - GET /health 健康检查                        │  │  │
│  │         │ - GET /status 状态查询                        │  │  │
│  │         │ - POST /api/roi 更新 ROI                      │  │  │
│  │         │ - GET /api/screenshot 截屏                    │  │  │
│  │         │ - POST /api/restart 重启服务                  │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ SSE Streaming Endpoint                        │  │  │
│  │         │ - GET /stream 消息流式输出                     │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  │         ┌───────────────────────────────────────────────┐  │  │
│  │         │ Web UI Management Interface                  │  │  │
│  │         │ - GET /api/ui Web 管理界面                    │  │  │
│  │         └───────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 端口映射
                              │ 6080 → noVNC
                              │ 5900 → VNC
                              │ 8000 → FastAPI
                              │ 6379 → Redis
                              ↓
                    ┌─────────────────┐
                    │  Docker Host    │
                    └─────────────────┘
```

### 数据流图

```
┌──────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  WeChat  │────▶│  Producer1  │────▶│ stream_raw  │────▶│  Producer2  │
│  Screen  │     │  Observer   │     │  (Redis)    │     │  Fetcher    │
└──────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                      │                                        │
                      ▼                                        ▼
                ┌─────────────┐                          ┌─────────────┐
                │ stream_     │                          │ stream_     │
                │ precise     │◀─────────────────────────│  (Redis)    │
                │  (Redis)    │                          └─────────────┘
                └─────────────┘                                  │
                      │                                          │
                      ▼                                          │
                ┌─────────────┐                                  │
                │   SSE       │                                  │
                │   Stream    │                                  │
                └─────────────┘                                  │
                      │                                          │
                      ▼                                          │
                ┌─────────────┐                                  │
                │MonitorAgent │◀─────────────────────────────────┘
                └─────────────┘
```

## 核心组件说明

### 1. Producer1: Observer (屏幕观察者)

**文件**: `producer_service/producer1_observer.py`

**职责**:
- 持续监控屏幕变化
- 检测新的消息气泡
- 对消息类型进行初步分类
- 将消息推送到原始队列

**工作流程**:
```
1. 初始化监控器（VisualMonitor）
2. 加载 ROI 配置
3. 启动监控循环
   - 定时截取屏幕
   - 使用 ChangeDetector 检测变化
   - 使用 MessageTypeClassifier 分类
   - 将消息推送到 stream_raw
```

**关键类**:
- `VisualMonitor`: 视觉监控器，负责窗口定位和屏幕截取
- `ChangeDetector`: 变化检测器，使用 dHash 算法
- `MessageTypeClassifier`: 消息分类器，基于图像特征分类

### 2. Producer2: Content Fetcher (内容获取者)

**文件**: `producer_service/producer2_content_fetcher.py`

**职责**:
- 从原始队列读取消息
- 模拟鼠标点击获取精确内容
- 提取文本或高清图片
- 将结构化消息推送到精确队列

**工作流程**:
```
1. 从 stream_raw 读取消息（消费者组模式）
2. 根据消息类型获取精确内容
   - 文本: 双击复制
   - 图片/视频: 点击打开查看器，截取高清图
3. 保存高清图片到本地
4. 构造完整消息数据
5. 推送到 stream_precise
6. 确认消息处理完成
```

**关键类**:
- `PrecisionContentFetcher`: 精确内容提取器，模拟用户操作

### 3. Redis Queue Manager (队列管理器)

**文件**: `producer_service/queue_manager.py`

**职责**:
- 管理 Redis Stream 消息队列
- 提供生产者入队操作
- 提供消费者读取操作
- 管理消息去重和持久化

**数据结构**:
```
stream_raw: wechat:messages:raw
  Fields:
    - id: 消息唯一ID
    - timestamp: 时间戳
    - type: 消息类型
    - position: 气泡位置 {screen_x, screen_y}
    - bubble_img_base64: 气泡图片（base64编码）
    - metadata: 元数据

stream_precise: wechat:messages:precise
  Fields:
    - id: 消息唯一ID
    - timestamp: 时间戳
    - type: 消息类型
    - position: 气泡位置
    - bubble_img_base64: 气泡图片
    - precise_content: 精确内容 {type, text, media_path, media_image_base64}
    - priority: 优先级
    - metadata: 元数据
```

**消费者组**:
- `producer2_group`: 消费 stream_raw
- `external_consumers`: 消费 stream_precise

### 4. API Server (API 服务)

**文件**: `producer_service/api_server.py`

**职责**:
- 提供 RESTful API 端点
- 实现 SSE 流式输出
- 管理 Web UI 界面
- 健康检查和状态查询

**API 端点**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/status` | GET | 获取状态 |
| `/api/screenshot` | GET | 截取屏幕 |
| `/api/roi` | POST | 更新 ROI |
| `/stream` | GET | SSE 消息流 |
| `/api/ui` | GET | Web 管理界面 |
| `/api/restart` | POST | 重启服务 |

**生命周期管理**:
- 启动时: 初始化队列管理器、启动生产者线程
- 运行时: 处理 API 请求、SSE 流式输出
- 关闭时: 停止生产者线程、清理资源

### 5. Web UI (Web 管理界面)

**文件**: `static/index.html`

**职责**:
- 提供 noVNC 远程桌面访问
- 显示服务状态
- ROI 区域配置界面
- 实时日志显示
- 截屏预览功能

**界面布局**:
```
┌─────────────────────────────────────────┐
│           Header (标题)                 │
├──────────────────┬──────────────────────┤
│                  │  服务状态卡片         │
│                  │  - Producer1 状态    │
│   远程桌面       │  - Producer2 状态    │
│   (noVNC)        │  - Redis 状态       │
│                  │                      │
│                  │  ROI 配置            │
│                  │  - 坐标输入          │
│                  │  - 更新按钮          │
│                  │                      │
│                  │  实时日志            │
│                  │  - 日志滚动显示      │
│                  │                      │
│                  │  重启服务按钮        │
└──────────────────┴──────────────────────┘
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `REDIS_HOST` | localhost | Redis 主机地址 |
| `REDIS_PORT` | 6379 | Redis 端口 |
| `REDIS_DB` | 0 | Redis 数据库编号 |
| `REDIS_PASSWORD` | - | Redis 密码 |
| `INSTANCE_ID` | default | 实例标识 |

### 配置文件

**config.yaml**:
```yaml
redis:
  host: localhost
  port: 6379
  db: 0
  password: null
  stream_raw: wechat:messages:raw
  stream_precise: wechat:messages:precise
  max_length: 10000

system:
  instance_id: default
  save_directory: ./data

roi: [100, 200, 500, 800]  # left, top, right, bottom
```

## 端口映射

### 单实例部署

| 容器端口 | 主机端口 | 服务 |
|----------|----------|------|
| 6080 | 6080 | noVNC Web 界面 |
| 5900 | 5900 | VNC 服务 |
| 8000 | 8000 | FastAPI 服务 |
| 6379 | 6379 | Redis |

### 多实例部署

| 实例 | FastAPI | noVNC | VNC |
|------|---------|-------|-----|
| 1 | 8001 | 6081 | 5901 |
| 2 | 8002 | 6082 | 5902 |
| 3 | 8003 | 6083 | 5903 |

## 部署方式

### 1. 开发环境（单实例）

```bash
docker-compose -f docker-compose.test.yml up -d --build
```

访问地址:
- noVNC: http://localhost:6080
- FastAPI: http://localhost:8000

### 2. 生产环境（单实例）

```bash
docker-compose -f docker-compose.yml up -d --build
```

### 3. 生产环境（多实例）

```bash
docker-compose -f docker-compose.multi.yml up -d --build
```

## 开发规范

### 代码组织

```
producer_service/
├── __init__.py
├── api_server.py              # FastAPI 服务器
├── monitor.py                 # 视觉监控器
├── detector.py                # 变化检测器
├── classifier.py              # 消息分类器
├── extractor.py               # 精确内容提取器
├── producer1_observer.py      # 生产者1
├── producer2_content_fetcher.py  # 生产者2
├── queue_manager.py           # 队列管理器
└── main.py                    # 主入口
```

### 日志规范

**日志级别**:
- `ERROR`: 功能异常、需要人工介入
- `WARN`: 潜在问题、但程序可继续
- `INFO`: 关键业务节点
- `DEBUG`: 调试信息

**必须添加日志的位置**:
- try-catch 的 catch 块
- 外部调用前后
- 业务入口
- 状态变更

**日志格式**:
```python
logger.info("消息描述", {key1: value1, key2: value2})
logger.error("错误描述", {error: exception_obj, context: {...}})
```

### 异常处理

```python
try:
    # 可能失败的操作
    pass
except Exception as e:
    logger.error("操作失败", {error: e, context: {...}})
    # 根据业务需要决定是否继续或抛出
```

### 线程安全

使用 `threading.Lock` 保护共享资源:

```python
import threading

class Example:
    def __init__(self):
        self.lock = threading.Lock()
        self.shared_data = None
    
    def update_data(self, data):
        with self.lock:
            self.shared_data = data
```

## 测试规范

### 测试类型

**单元测试** (`tests/test_producer_service.py`):
- 测试单个组件功能
- 使用 Mock 隔离外部依赖

**API 测试** (`tests/test_api_server.py`):
- 测试所有 API 端点
- 验证请求/响应格式

**集成测试** (`tests/test_integration.py`):
- 测试完整工作流
- 验证组件协作

### 运行测试

```bash
# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行 API 测试
python run_tests.py api

# 运行集成测试
python run_tests.py integration

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

## 故障排查

### 常见问题

**1. 容器无法启动**
- 检查 Docker 日志: `docker-compose logs`
- 检查端口是否被占用: `netstat -ano | findstr "6080"`
- 检查镜像构建是否成功

**2. 微信窗口无法定位**
- 检查 xdotool 是否正常工作
- 检查微信窗口名称是否匹配
- 查看 monitor.py 日志

**3. 消息检测不准确**
- 调整 ChangeDetector 的阈值参数
- 检查 ROI 区域配置是否正确
- 查看 HSV 颜色范围是否匹配

**4. Redis 连接失败**
- 检查 Redis 服务是否运行
- 检查 Redis 连接配置
- 查看 queue_manager.py 日志

## 性能优化

### 监控频率

根据实际需求调整监控间隔:
- 高频监控: `interval = 0.1` (100ms)
- 标准监控: `interval = 0.2` (200ms)
- 低频监控: `interval = 0.5` (500ms)

### ROI 优化

- 尽量缩小 ROI 区域，减少不必要的屏幕截取
- 避免包含动态内容区域（如时间显示）

### Redis 优化

- 设置合理的 `max_length` 限制内存占用
- 定期清理过期的消息

## 安全说明

### 访问控制

- VNC 默认密码: `wechat123`，生产环境请修改
- 建议使用防火墙限制端口访问
- 不要将服务暴露到公网

### 敏感信息

- 禁止在代码中硬编码密码和密钥
- 使用环境变量或配置文件存储敏感信息

## 相关文档

- [README.md](./README.md) - 项目快速开始
- [WECHAT_SANDBOX.md](./WECHAT_SANDBOX.md) - 微信沙箱使用说明
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始指南
- [../../CLAUDE.md](../../CLAUDE.md) - 项目整体记忆文档

## 更新日志

### v1.0.0 (2026-01-10)
- 初始版本发布
- 实现基础的消息监控和提取功能
- 支持 FastAPI 和 SSE 流式输出
- 支持 Web UI 管理界面
- 支持多实例部署
