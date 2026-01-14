# API 模块

微信沙盒的 FastAPI 接口层，提供 RESTful API 和 SSE 流服务。

## 📂 目录结构

```
api/
├── __init__.py      # FastAPI 应用工厂和生命周期管理
├── config.py        # 配置管理 API
├── health.py        # 健康检查 API
├── instance.py      # 实例管理 API
└── stream.py        # SSE 消息流 API
```

---

## 🎯 模块概览

### 1. 应用入口 (`__init__.py`)

**职责**：FastAPI 应用的创建和生命周期管理

**核心功能**：
- 应用工厂模式 (`create_app()`)
- 生命周期管理 (`lifespan()`)
- 路由注册
- CORS 中间件配置
- 混合生产者初始化

**应用版本**：`2.0.0`

**主要路由**：
- `/` - 根路径（服务信息）
- `/stream` - SSE 流快捷入口
- `/api/config` - 配置管理
- `/api/instance` - 实例管理
- `/api/stream` - SSE 消息流
- `/api/health` - 健康检查

---

### 2. 配置管理 (`config.py`)

**路由前缀**：`/api/config`

**功能**：管理微信沙盒的配置，包括 ROI（监控区域）等

#### API 端点

##### GET `/api/config`
获取完整配置

**响应示例**：
```json
{
  "wechat": {
    "target_group_name": "Test Group"
  },
  "monitor": {
    "capture_interval_ms": 200,
    "save_directory": "./data"
  },
  "roi": {
    "presets": {
      "send_area": {
        "name": "发送区域",
        "description": "微信消息输入和发送区域",
        "coordinates": [0, 0, 0, 0],
        "enabled": true
      },
      "receive_area": {
        "name": "接收区域",
        "description": "群消息接收和显示区域",
        "coordinates": [0, 0, 0, 0],
        "enabled": true
      }
    },
    "active_preset": "receive_area"
  },
  "redis": {
    "host": "redis",
    "port": 6379,
    "db": 0,
    "password": null,
    "stream_raw": "wechat:messages:raw",
    "stream_precise": "wechat:messages:precise"
  }
}
```

##### POST `/api/config`
更新完整配置

**请求体**：
```json
{
  "wechat": {
    "target_group_name": "New Group"
  },
  "roi": {
    "presets": {...},
    "active_preset": "receive_area"
  }
}
```

**响应**：
```json
{
  "status": "success",
  "message": "配置已保存"
}
```

##### GET `/api/config/roi`
获取当前 ROI 配置

**响应示例**：
```json
{
  "left": 100,
  "top": 200,
  "right": 800,
  "bottom": 1000,
  "active_preset": "receive_area",
  "presets": {
    "send_area": {...},
    "receive_area": {...}
  }
}
```

##### POST `/api/config/roi`
更新 ROI 配置

**请求体**：
```json
{
  "left": 100,
  "top": 200,
  "right": 800,
  "bottom": 1000,
  "preset": "receive_area",
  "active_preset": "receive_area"
}
```

**验证规则**：
- `left < right`（左边界必须小于右边界）
- `top < bottom`（上边界必须小于下边界）
- 所有坐标必须为非负整数

---

### 3. 健康检查 (`health.py`)

**路由前缀**：`/api/health`

**功能**：监控服务健康状态和生产者运行状态

#### API 端点

##### GET `/api/health/`
健康检查

**响应示例**：
```json
{
  "status": "healthy",
  "redis": true,
  "producer_running": true,
  "mode": "atspi",
  "active_mode": "atspi",
  "stats": {
    "atspi_success": 150,
    "atspi_failed": 2,
    "visual_fallback": 0,
    "total_messages": 150
  }
}
```

**状态说明**：
- `status` - `healthy` / `unhealthy`
- `redis` - Redis 连接状态
- `producer_running` - 生产者运行状态
- `stats` - 生产者统计信息

##### GET `/api/health/status`
获取详细状态

**响应示例**：
```json
{
  "producer": "initialized",
  "stats": {
    "mode": "atspi",
    "active_mode": "atspi",
    "stats": {...},
    "atspi_available": true,
    "visual_available": false
  }
}
```

---

### 4. 实例管理 (`instance.py`)

**路由前缀**：`/api/instance`

**功能**：沙盒实例管理和远程操作

#### API 端点

##### GET `/api/instance/screenshot`
获取当前屏幕截图

**响应**：PNG 图片（二进制流）

**使用场景**：
- 远程查看微信界面
- 调试 ROI 配置
- 验证消息检测效果

**示例**：
```bash
# 下载截图
curl http://localhost:8000/api/instance/screenshot --output screenshot.png

# 在浏览器中查看
open http://localhost:8000/api/instance/screenshot
```

##### POST `/api/instance/restart`
重启服务

**响应**：
```json
{
  "status": "success",
  "message": "重启请求已接收（需配置 systemd 或 Docker 重启策略）"
}
```

**注意**：实际重启需要配合 systemd 或 Docker 的重启策略。

---

### 5. SSE 消息流 (`stream.py`)

**路由前缀**：`/api/stream`

**功能**：Server-Sent Events (SSE) 实时消息流

#### API 端点

##### GET `/api/stream/messages`
SSE 实时消息流（主要端点）

**响应格式**：`text/event-stream`

**消息格式**：JSONL (JSON Lines)
```
data: {"id":"msg_001","type":"text","sender":"张三","content":{"text":"hello"},"window_detected":false,...}
data: {"id":"msg_002","type":"photo","sender":"李四","content":{"high_res_media_path":"/host/data/photo.png"},"window_detected":true,...}
```

**消息结构**：
```typescript
{
  id: string;              // 消息ID
  timestamp: string;       // 时间戳（ISO格式）
  type: MessageType;       // 消息类型（text/photo/video）
  sender: string;          // 发送者
  content: {
    text?: string;                    // 文本内容
    high_res_media_path?: string;     // 媒体文件路径
    media_image_base64?: string;      // Base64图片（可选）
  };
  window_detected: boolean;  // 是否唤起新窗口
  metadata: {
    producer: string;       // 生产者标识
    production_mode: string; // 生产模式
    processed_at: string;   // 处理时间
    is_photo?: boolean;     // 是否为photo消息
  };
}
```

**支持的消息类型**：
- `text` - 文本消息
- `photo` - 图片消息（高清）
- `video` - 视频消息

**其他类型**（不推送SSE，仅保存到物理机）：
- `file` - 文件消息
- `link` - 链接消息
- `other` - 其他类型

**使用示例**：
```bash
# curl 监听
curl -N http://localhost:8000/api/stream/messages

# JavaScript EventSource
const eventSource = new EventSource('http://localhost:8000/api/stream/messages');
eventSource.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`[${message.sender}] ${message.content.text}`);
};
```

##### GET `/api/stream/status`
SSE 状态流

**响应**：定期发送心跳和队列信息

**示例**：
```
data: {"status":"alive","queue_info":{...}}
data: {"status":"alive","queue_info":{...}}
```

---

## 🚀 快速开始

### 启动服务

```python
from api import app
import uvicorn

# 方式1：直接运行
uvicorn.run(app, host="0.0.0.0", port=8000)

# 方式2：使用命令行
# uvicorn api:app --host 0.0.0.0 --port 8000
```

### API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 基础使用

#### 1. 健康检查

```bash
curl http://localhost:8000/api/health/
```

#### 2. 获取配置

```bash
curl http://localhost:8000/api/config
```

#### 3. 更新 ROI

```bash
curl -X POST http://localhost:8000/api/config/roi \
  -H "Content-Type: application/json" \
  -d '{
    "left": 100,
    "top": 200,
    "right": 800,
    "bottom": 1000,
    "preset": "receive_area"
  }'
```

#### 4. 监听消息流

```bash
curl -N http://localhost:8000/api/stream/messages
```

#### 5. 获取截图

```bash
curl http://localhost:8000/api/instance/screenshot --output screenshot.png
```

---

## 📊 SSE 流协议

### 连接建立

```http
GET /api/stream/messages HTTP/1.1
Host: localhost:8000
Accept: text/event-stream
Cache-Control: no-cache
```

### 消息格式

每条消息包含两个部分：
1. **前缀**：`data: `
2. **内容**：JSON 对象

示例：
```
data: {"id":"msg_123","type":"text","sender":"张三","content":{"text":"hello"}}

```

### 客户端实现

#### JavaScript (浏览器)

```javascript
const eventSource = new EventSource('http://localhost:8000/api/stream/messages');

eventSource.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`收到消息:`, message);

  // 处理不同类型的消息
  switch (message.type) {
    case 'text':
      console.log(`文本: ${message.content.text}`);
      break;
    case 'photo':
      console.log(`图片: ${message.content.high_res_media_path}`);
      break;
    case 'video':
      console.log(`视频: ${message.content.high_res_media_path}`);
      break;
  }
};

eventSource.onerror = (error) => {
  console.error('SSE 连接错误:', error);
};

// 关闭连接
// eventSource.close();
```

#### Python

```python
import requests
import json

def stream_messages():
    url = "http://localhost:8000/api/stream/messages"
    response = requests.get(url, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]  # 移除 "data: " 前缀
                message = json.loads(data)
                print(f"[{message['sender']}] {message['content']}")

# 运行
stream_messages()
```

#### curl

```bash
curl -N http://localhost:8000/api/stream/messages
```

---

## 🔧 配置说明

### CORS 配置

默认允许所有来源（开发环境）：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

生产环境建议限制来源：

```python
allow_origins=["https://yourdomain.com"]
```

### 生命周期管理

应用启动时：
1. 初始化 Redis 客户端
2. 创建混合生产者（AT-SPI 模式）
3. 启动生产者
4. 设置全局组件

应用关闭时：
1. 停止生产者
2. 清理资源

---

## 📝 生产者统计

### 统计字段

| 字段 | 说明 |
|------|------|
| `mode` | 配置的生产模式 |
| `active_mode` | 当前活跃模式 |
| `stats.atspi_success` | AT-SPI 成功次数 |
| `stats.atspi_failed` | AT-SPI 失败次数 |
| `stats.visual_fallback` | 视觉兜底次数 |
| `stats.total_messages` | 总消息数 |
| `atspi_available` | AT-SPI 是否可用 |
| `visual_available` | 视觉方案是否可用 |

### 示例响应

```json
{
  "mode": "atspi",
  "active_mode": "atspi",
  "stats": {
    "atspi_success": 150,
    "atspi_failed": 2,
    "visual_fallback": 0,
    "total_messages": 150
  },
  "atspi_available": true,
  "visual_available": false
}
```

---

## ⚠️ 注意事项

### SSE 连接

1. **保持连接**
   - SSE 是长连接，确保客户端处理断线重连
   - 建议实现指数退避重连策略

2. **消息顺序**
   - SSE 按时间顺序推送消息
   - 客户端按顺序处理

3. **心跳检测**
   - 服务端定期发送心跳（`/api/stream/status`）
   - 客户端监控连接状态

### 性能优化

1. **消息过滤**
   - 只推送 `text`、`photo`、`video` 类型
   - 其他类型保存到物理机但不推送

2. **缓存控制**
   - SSE 响应头包含 `Cache-Control: no-cache`
   - 禁用代理缓存

3. **连接数限制**
   - 监控并发 SSE 连接数
   - 避免过多连接消耗资源

### 错误处理

1. **Redis 连接失败**
   - 健康检查返回 `redis: false`
   - 生产者无法推送消息

2. **生产者未初始化**
   - 返回 `producer: "not_initialized"`
   - SSE 连接无法获取消息

3. **ROI 配置错误**
   - 验证 ROI 坐标合法性
   - 返回 422 错误和详细原因

---

## 🧪 测试

### 单元测试

```bash
# 测试配置 API
pytest tests/test_api_config.py

# 测试健康检查
pytest tests/test_api_health.py

# 测试 SSE 流
pytest tests/test_api_stream.py
```

### 手动测试

```bash
# 1. 健康检查
curl http://localhost:8000/api/health/

# 2. 获取配置
curl http://localhost:8000/api/config

# 3. 更新 ROI
curl -X POST http://localhost:8000/api/config/roi \
  -H "Content-Type: application/json" \
  -d '{"left":100,"top":200,"right":800,"bottom":1000}'

# 4. 监听消息流
curl -N http://localhost:8000/api/stream/messages

# 5. 获取截图
curl http://localhost:8000/api/instance/screenshot --output test.png
```

---

## 📖 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SSE 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [消息类型说明](../docs/MESSAGE_TYPES.md)
- [架构设计文档](../docs/ARCHITECTURE.md)

---

## 📝 版本历史

### v2.0.0 (2025-01-14)
- ✅ 使用混合生产者替代旧的双生产者架构
- ✅ 更新 SSE 流格式为 JSONL
- ✅ 添加多预设 ROI 配置支持
- ✅ 更新健康检查以支持新的统计信息
- ✅ 重构实例管理 API

### v1.0.0 (2025-01-10)
- ✅ 初始版本
- ✅ 基础 REST API
- ✅ SSE 消息流

---

**维护者**: Claude Code
**最后更新**: 2025-01-14
**版本**: 2.0.0
