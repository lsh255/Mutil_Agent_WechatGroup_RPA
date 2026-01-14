# wechat_sandbox 架构文档

## 项目概述

wechat_sandbox 是一个基于 Docker 容器的微信沙箱环境，用于在隔离的环境中运行 Linux 版微信，并通过双生产者架构实时提取和转发群聊消息。

### 核心功能
- 在 Docker 容器中运行 Linux 版微信
- 实时监控微信群聊消息气泡
- 自动提取消息精确内容（文本、图片、视频）
- 通过 SSE (Server-Sent Events) 推送消息到外部系统

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker 容器环境                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐      ┌──────────────────────────────────┐  │
│  │  Linux 微信      │      │      双生产者服务                  │  │
│  │  (运行在 Xvfb)   │◄────►│      (FastAPI + Redis)            │  │
│  └─────────────────┘      │  ┌────────────────────────────┐  │  │
│         ▲                 │  │  Producer1 Observer         │  │  │
│         │                 │  │  (监控消息气泡)              │  │  │
│         │ 屏幕监控         │  └────────────────────────────┘  │  │
│         │                 │              ▼                     │  │
│  ┌──────┴──────┐          │  ┌────────────────────────────┐  │  │
│  │  Xvfb 虚拟显示 │          │  │  Redis Stream (Raw)        │  │  │
│  │  (无头显示)   │          │  │  (原始消息队列)              │  │  │
│  └─────────────┘          │  └────────────────────────────┘  │  │
│                           │              ▼                     │  │
│                           │  ┌────────────────────────────┐  │  │
│                           │  │  Producer2 ContentFetcher   │  │  │
│                           │  │  (提取精确内容)              │  │  │
│                           │  └────────────────────────────┘  │  │
│                           │              ▼                     │  │
│                           │  ┌────────────────────────────┐  │  │
│                           │  │  Redis Stream (Precise)    │  │  │
│                           │  │  (精确消息队列)              │  │  │
│                           │  └────────────────────────────┘  │  │
│                           │              ▼                     │  │
│                           │  ┌────────────────────────────┐  │  │
│                           │  │  SSE Stream 端点            │  │  │
│                           │  │  (/stream)                  │  │  │
│                           │  └────────────────────────────┘  │  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SSE 推送
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    外部消费者系统                                  │
│  (前端 Web 应用、消息处理服务、数据分析平台等)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 组件层次

```
wechat_sandbox/
├── api/                        # API 模块
│   ├── __init__.py            # FastAPI 应用初始化
│   ├── config.py              # 配置管理端点
│   ├── health.py              # 健康检查端点
│   ├── instance.py            # 实例管理端点
│   └── stream.py              # SSE 流式输出端点
├── core/                       # 核心业务逻辑
│   ├── detector/              # 变化检测模块
│   │   ├── detector.py        # 变化检测
│   │   ├── change_detector.py # 屏幕变化检测
│   │   ├── classifier.py      # 消息类型分类
│   │   └── visual_monitor.py  # 视觉监控
│   ├── extractor/             # 内容提取模块
│   │   ├── extractor.py       # 内容提取
│   │   └── text_extractor.py  # 文本提取
│   ├── producer/              # 生产者模块
│   │   ├── monitor.py         # 屏幕监控
│   │   ├── observer.py        # 生产者1：观察者
│   │   ├── content_fetcher.py # 生产者2：内容获取器
│   │   └── agent_consumer.py  # Agent 消息消费者
│   ├── queue/                 # 队列管理模块
│   │   └── manager.py         # Redis 队列管理
│   ├── classifier/            # 分类器模块
│   │   └── classifier.py      # 消息分类器
│   └── platform/              # 平台适配模块
│       └── adapter.py        # 跨平台适配器
├── utils/                      # 工具模块
│   ├── logger.py              # 日志工具
│   ├── config.py              # 配置管理
│   └── platform_adapter.py    # 平台适配器
├── tests/                      # 测试模块
│   ├── conftest.py            # 测试配置
│   ├── test_queue_manager.py  # 队列管理测试
│   ├── test_producer_service.py # 生产者服务测试
│   ├── test_api_server.py     # API 服务器测试
│   └── test_integration.py    # 集成测试
├── services/                   # 服务模块
│   └── producer_service.py    # 生产者服务（兼容层）
├── main.py                     # 主启动脚本
├── backup_start.py            # 备用启动脚本
├── start.sh                    # Shell 启动脚本
├── start_wechat.sh             # 微信启动脚本
├── start_wechat_sandbox.bat    # Windows 启动脚本
├── Dockerfile                  # Docker 镜像定义
├── Dockerfile.test             # 测试环境镜像
├── docker-compose.test.yml     # 测试环境编排
├── config.yaml                 # 配置文件
├── config.production.yaml      # 生产环境配置
└── requirements.txt            # Python 依赖
```

## 核心模块详解

### 1. API 模块 (api/)

**职责**
- 提供 HTTP API 接口
- 管理 Producer1 和 Producer2 的生命周期
- 提供 SSE 流式输出端点

**主要文件**
- `__init__.py`: FastAPI 应用初始化和生命周期管理
- `config.py`: 配置管理端点（获取/更新配置）
- `health.py`: 健康检查端点（服务状态检查）
- `instance.py`: 实例管理端点（启动/停止/重启）
- `stream.py`: SSE 流式输出端点（消息推送）

**API 端点**
- `GET /api/config`: 获取当前配置
- `POST /api/config`: 更新配置
- `GET /api/health`: 健康检查
- `GET /api/status`: 获取服务状态
- `POST /api/instance/start`: 启动实例
- `POST /api/instance/stop`: 停止实例
- `GET /api/stream`: SSE 流式输出消息

### 2. 变化检测模块 (core/detector/)

**职责**
- 检测屏幕内容变化
- 识别新的消息气泡
- 提取消息气泡边界框

**主要文件**
- `detector.py`: 变化检测核心逻辑
- `change_detector.py`: 屏幕变化检测
- `classifier.py`: 消息类型分类
- `visual_monitor.py`: 视觉监控

**关键方法**
- `detect_change()`: 检测屏幕变化
- `detect_bubbles()`: 检测消息气泡
- `extract_bubble_boundaries()`: 提取气泡边界

**算法**
- 使用 dHash 算法进行图像哈希比较
- OpenCV 进行边界检测

### 3. 内容提取模块 (core/extractor/)

**职责**
- 从微信界面提取文本内容（通过剪贴板）
- 截取媒体消息的高清截图
- 执行鼠标点击、双击等操作

**主要文件**
- `extractor.py`: 内容提取核心逻辑
- `text_extractor.py`: 文本提取

**关键方法**
- `fetch_text()`: 获取文本内容
- `fetch_media()`: 获取媒体截图
- `click_mouse()`: 模拟鼠标点击
- `double_click_mouse()`: 模拟鼠标双击

**操作序列**
1. 点击消息气泡
2. 等待内容加载
3. 复制文本或截取媒体
4. 关闭查看器（ESC 键）

### 4. 生产者模块 (core/producer/)

**职责**
- Producer1（Observer）：监控微信群聊界面，检测新消息气泡
- Producer2（ContentFetcher）：从原始消息队列读取消息，提取精确内容
- AgentConsumer：消费消息并与外部 Agent 通信

**主要文件**
- `monitor.py`: 屏幕监控
- `observer.py`: 生产者1：观察者
- `content_fetcher.py`: 生产者2：内容获取器
- `agent_consumer.py`: Agent 消息消费者

**工作流程**
1. Observer 启动屏幕监控，检测新消息气泡，入队原始消息
2. ContentFetcher 从原始消息队列读取，分类消息类型，提取精确内容，入队精确消息
3. AgentConsumer 消费精确消息，格式化为 Agent 可识别格式，发送到外部系统

### 5. 队列管理模块 (core/queue/)

**职责**
- 管理 Redis Stream 消息队列
- 提供消息入队、出队、确认操作
- 实现消息锁定机制防止并发重复处理

**主要文件**
- `manager.py`: Redis 队列管理

**队列结构**
- `stream_raw`: 原始消息队列（Producer1 → Producer2）
- `stream_precise`: 精确消息队列（Producer2 → 外部消费）

**关键方法**
- `enqueue_raw()`: 入队原始消息
- `read_raw_for_processing()`: 读取原始消息供处理
- `ack_raw()`: 确认原始消息处理完成
- `enqueue_precise()`: 入队精确消息
- `read_precise_for_streaming()`: 读取精确消息用于 SSE

**消息锁定机制**
- 使用 Redis SET NX 实现分布式锁
- 锁键格式: `wechat:lock:{message_id}`
- 锁超时时间: 可配置（默认 300 秒）
- 在读取消息时获取锁，确认处理后释放锁

### 6. 分类器模块 (core/classifier/)

**职责**
- 判断消息类型（文本、图片、视频、链接等）
- 识别媒体消息的特征图标

**主要文件**
- `classifier.py`: 消息分类器

**支持的消息类型**
- `text`: 纯文本消息
- `image`: 图片消息
- `video`: 视频消息
- `link`: 链接消息
- `unknown`: 未知类型

### 7. 平台适配模块 (core/platform/)

**职责**
- 提供跨平台适配能力
- 封装不同平台的操作（Windows/Linux）

**主要文件**
- `adapter.py`: 跨平台适配器

**关键方法**
- `capture_screen()`: 截取屏幕
- `get_window_position()`: 获取窗口位置
- `click_mouse()`: 模拟鼠标点击
- `copy_text()`: 复制文本到剪贴板

## 数据流

### 消息处理流程

```
1. 屏幕监控
   ├─ 定期截屏
   ├─ 提取 ROI
   └─ 检测变化

2. 消息检测 (Producer1)
   ├─ 识别新气泡
   ├─ 计算位置
   ├─ 截取缩略图
   └─ 入队 stream_raw

3. 内容提取 (Producer2)
   ├─ 从 stream_raw 读取
   ├─ 分类消息类型
   ├─ 提取精确内容
   └─ 入队 stream_precise

4. 消息推送 (SSE)
   ├─ 从 stream_precise 读取
   ├─ 转换为 JSON 格式
   └─ 推送到客户端
```

### 消息数据结构

#### 原始消息 (stream_raw)
```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "bubble_img": "base64_encoded_image",
  "screen_abs_x": 1024,
  "screen_abs_y": 768,
  "timestamp": "2024-01-10T12:00:00Z"
}
```

#### 精确消息 (stream_precise)
```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "type": "text|image|video|link",
  "content": "消息文本内容",
  "position": {
    "x": 1024,
    "y": 768
  },
  "precise_content": {
    "text": "完整文本",
    "media_path": "/path/to/media.png",
    "media_img": "base64_encoded_image"
  },
  "metadata": {
    "timestamp": "2024-01-10T12:00:00Z",
    "sender": "发送者昵称"
  }
}
```

## 并发与锁定

### 消息锁定机制

**目的**
防止多个生产者实例并发处理同一消息，导致重复处理或数据不一致。

**实现**
- 使用 Redis SET NX 实现分布式锁
- 锁键格式: `wechat:lock:{message_id}`
- 锁值: `{consumer_name}_{timestamp}`
- 锁超时: 可配置（默认 300 秒）

**流程**
1. 读取消息时尝试获取锁
2. 如果锁已被占用，跳过该消息
3. 如果获取成功，处理消息
4. 确认处理后释放锁

**代码示例**
```python
# 获取锁
if self._acquire_lock(message_id):
    # 处理消息
    process_message(message_id)
    # 确认处理（自动释放锁）
    self.ack_raw(message_id)
else:
    logger.debug(f"Message {message_id} already locked, skipping")
```

## 配置说明

### 配置文件 (utils/config.py)

```python
config = {
    # Redis 配置
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'stream_raw': 'wechat:messages:raw',
        'stream_precise': 'wechat:messages:precise',
        'max_length': 10000,
        'lock_ttl': 300,
        'lock_prefix': 'wechat:lock:'
    },
    
    # 监控配置
    'monitor': {
        'interval': 0.5,  # 监控间隔（秒）
        'target_group_name': '目标群聊名称'
    },
    
    # 消息处理配置
    'message': {
        'text_copy_timeout': 1,  # 文本复制超时（秒）
        'media_load_timeout': 2  # 媒体加载超时（秒）
    },
    
    # 系统配置
    'system': {
        'instance_id': 'default'  # 实例标识
    }
}
```

### 环境变量

可以通过环境变量覆盖配置：

```bash
export REDIS_HOST=redis-server
export REDIS_PORT=6379
export MONITOR_INTERVAL=0.5
export TARGET_GROUP_NAME="测试群"
```

## 部署架构

### Docker 容器依赖

```
wechat_sandbox 容器
├── Xvfb (虚拟显示)
├── Linux 微信客户端
├── xdotool (鼠标/键盘模拟)
├── xwininfo (窗口信息查询)
├── Redis (消息队列)
└── Python 双生产者服务
```

### 网络配置

```
宿主机 (Host)
├── 端口 8000 (FastAPI 服务)
├── 端口 6379 (Redis 可选暴露)
└── 端口 5900 (VNC 可选用于调试)

Docker 容器
├── FastAPI 服务: 0.0.0.0:8000
├── Redis: localhost:6379
└── Xvfb: :99
```

## 性能优化

### 监控优化
- 使用 mss 库替代 PIL.ImageGrab 提升截图性能
- 只监控感兴趣区域 (ROI) 减少计算量
- 调整监控间隔平衡性能和实时性

### 队列优化
- Redis Stream 自动修剪（max_length）
- 使用消费者组实现消息负载均衡
- 消息锁定机制防止重复处理

### 提取优化
- 异步处理消息提取
- 缓存分类模型
- 并行处理多个消息

## 错误处理

### 常见错误及处理

1. **微信窗口未找到**
   - 检查微信是否正常启动
   - 检查窗口标题是否匹配

2. **Redis 连接失败**
   - 检查 Redis 服务是否运行
   - 检查网络连接和防火墙

3. **截图失败**
   - 检查 Xvfb 是否正常运行
   - 检查显示环境变量

4. **内容提取失败**
   - 检查剪贴板工具是否可用
   - 增加超时时间

## 日志规范

### 日志级别

- **ERROR**: 功能异常、需要人工介入
  - 数据库连接失败、API 调用异常
- **WARN**: 潜在问题、但程序可继续
  - 配置缺失、重试后成功
- **INFO**: 关键业务节点
  - 消息入队、内容提取完成
- **DEBUG**: 调试信息
  - 查询参数、内部状态

### 关键日志点

- try-catch 的 catch 块（必须）
- 外部调用前后（API、数据库、文件 IO）
- 业务入口（函数/接口入口）
- 状态变更（重要对象状态改变）
- 消息锁定（获取锁、释放锁）

## 扩展建议

### 功能扩展
- 支持多个群聊同时监控
- 添加消息过滤规则
- 支持语音消息识别
- 添加消息存储和查询功能

### 性能扩展
- 使用消息队列缓冲高并发
- 添加消息优先级机制
- 实现消息去重和去重策略

### 监控扩展
- 添加性能指标收集
- 实现告警机制
- 添加可视化监控面板

## 安全考虑

1. **敏感信息保护**
   - 禁止在代码中硬编码密码和 API Key
   - 使用环境变量存储敏感配置

2. **访问控制**
   - FastAPI 端点添加认证
   - Redis 访问控制

3. **数据安全**
   - 消息数据加密存储
   - 定期清理过期数据

## 维护指南

### 日常维护
- 检查日志文件大小
- 监控 Redis 内存使用
- 清理过期的消息队列

### 故障排查
1. 检查 Docker 容器状态
2. 查看服务日志
3. 测试 API 端点
4. 检查 Redis 队列状态

### 更新升级
1. 停止服务
2. 拉取新代码
3. 更新依赖
4. 重启服务
5. 验证功能

## 版本历史

- **v1.0.0**: 初始版本，实现双生产者架构
  - 支持消息监控和内容提取
  - Redis Stream 队列管理
  - SSE 消息推送

- **v1.1.0**: 消息锁定机制
  - 添加分布式锁防止并发重复处理
  - 优化日志级别
  - 修复 Docker Xvfb 兼容性问题

- **v2.0.0**: 目录结构重构
  - 重构为 `api/` 和 `core/` 目录结构
  - 添加跨平台适配模块
  - 集成 Agent 消息消费者
  - 更新文档和测试路径

## 参考资料

- [Redis Stream 文档](https://redis.io/docs/data-types/streams/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [mss 屏幕截图库](https://python-mss.readthedocs.io/)
- [xdotool 文档](https://www.semicomplete.com/projects/xdotool/)
