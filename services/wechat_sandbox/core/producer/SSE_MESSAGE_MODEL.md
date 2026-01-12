# SSE消息数据模型定义 (JSONL格式)

## 概述

本文档定义了通过SSE推送的消息数据模型，使用JSONL（JSON Lines）格式，每行一个独立的JSON对象。

## JSONL格式说明

- **格式**: 每行一个完整的JSON对象
- **编码**: UTF-8
- **分隔符**: 换行符 `\n`
- **示例**: 见 `sse_message_model.jsonl`

## 数据模型

### 完整消息结构

```json
{
  "id": "msg_20250112_143022_001",
  "timestamp": 1736653822.123,
  "type": "text|photo|video|file|link|other",
  "sender": "发送者昵称",
  "content": {
    "type": "text|photo|video|file|link|other",
    "text": "消息文本内容",
    "media_path": null,
    "high_res_media_path": "/host/data/xxx",
    "media_image_base64": null
  },
  "group_name": "群聊名称",
  "window_detected": false,
  "window_title": null,
  "metadata": {
    "producer": "atspi_observer",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:22.123456",
    "extracted_at": "2025-01-12T14:30:22.234567"
  }
}
```

## 字段说明

### 基础字段

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `id` | string | ✅ | 消息唯一标识 | `msg_20250112_143022_001` |
| `timestamp` | float | ✅ | Unix时间戳（秒） | `1736653822.123` |
| `type` | string | ✅ | 消息类型 | `text`, `photo`, `video`, `file`, `link`, `other` |
| `sender` | string | ✅ | 发送者昵称 | `张三` |
| `content` | object | ✅ | 消息内容对象 | 见下方 |
| `group_name` | string | ✅ | 群聊名称 | `测试群聊` |
| `window_detected` | boolean | ✅ | 是否检测到新窗口 | `true` / `false` |
| `window_title` | string\|null | ✅ | 新窗口标题 | `Photos and Videos` |
| `metadata` | object | ✅ | 元数据 | 见下方 |

### content对象

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `type` | string | ✅ | 内容类型（与顶层type一致） | `text` |
| `text` | string | ✅ | 文本内容 | `今天作业w1作业前` |
| `media_path` | string\|null | ❌ | 缩略图路径 | `/tmp/thumb.png` |
| `high_res_media_path` | string\|null | ❌ | 高清媒体路径（保存到物理机） | `/host/data/photo.png` |
| `media_image_base64` | string\|null | ❌ | Base64编码的图片（可选） | `data:image/png;base64,...` |

**扩展字段（特定类型）**:

- `file`: `original_filename` - 原始文件名
- `link`: `url`, `title` - 链接地址和标题

### metadata对象

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `producer` | string | ✅ | 生产者类型 | `atspi_observer` |
| `production_mode` | string | ✅ | 生产模式 | `atspi`, `visual`, `hybrid` |
| `processed_at` | string | ✅ | 处理时间（ISO 8601） | `2025-01-12T14:30:22.123456` |
| `extracted_at` | string | ❌ | 提取完成时间 | `2025-01-12T14:30:22.234567` |
| `window_opened` | boolean | ❌ | 是否打开了窗口 | `true` |
| `image_saved` | boolean | ❌ | 图片是否保存 | `true` |
| `save_path` | string | ❌ | 保存路径 | `/host/data/xxx` |

## 消息类型定义

### 1. 文本消息 (text)

```json
{
  "id": "msg_20250112_143022_001",
  "timestamp": 1736653822.123,
  "type": "text",
  "sender": "张三",
  "content": {
    "type": "text",
    "text": "今天作业w1作业前",
    "media_path": null,
    "high_res_media_path": null,
    "media_image_base64": null
  },
  "group_name": "测试群聊",
  "window_detected": false,
  "window_title": null,
  "metadata": {
    "producer": "atspi_observer",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:22.123456"
  }
}
```

**特征**:
- `window_detected`: `false`
- `window_title`: `null`

### 2. 图片/视频消息 (photo/video)

```json
{
  "id": "msg_20250112_143025_002",
  "timestamp": 1736653825.456,
  "type": "photo",
  "sender": "李四",
  "content": {
    "type": "photo",
    "text": "[Photo]",
    "media_path": null,
    "high_res_media_path": "/host/data/photos/photo_20250112_143025.png",
    "media_image_base64": null
  },
  "group_name": "测试群聊",
  "window_detected": true,
  "window_title": "Photos and Videos",
  "metadata": {
    "producer": "atspi_observer",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:25.456789",
    "extracted_at": "2025-01-12T14:30:26.789012",
    "window_opened": true,
    "image_saved": true,
    "save_path": "/host/data/photos/photo_20250112_143025.png"
  }
}
```

**特征**:
- `window_detected`: `true`
- `window_title`: `Photos and Videos`
- `high_res_media_path`: 保存到物理机的路径

### 3. 文件消息 (file)

```json
{
  "id": "msg_20250112_143031_004",
  "timestamp": 1736653831.012,
  "type": "file",
  "sender": "赵六",
  "content": {
    "type": "file",
    "text": "[File] document.pdf",
    "media_path": null,
    "high_res_media_path": "/host/data/files/document_20250112_143031.pdf",
    "media_image_base64": null
  },
  "group_name": "测试群聊",
  "window_detected": true,
  "window_title": "File Transfer",
  "metadata": {
    "producer": "atspi_observer",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:31.012345",
    "extracted_at": "2025-01-12T14:30:31.345678",
    "window_opened": true,
    "file_saved": true,
    "save_path": "/host/data/files/document_20250112_143031.pdf",
    "original_filename": "document.pdf"
  }
}
```

**特征**:
- `window_detected`: `true`
- `window_title**: `File Transfer` 或其他（非Photos and Videos）
- 文件保存到物理机

### 4. 链接消息 (link)

```json
{
  "id": "msg_20250112_143034_005",
  "timestamp": 1736653834.345,
  "type": "link",
  "sender": "孙七",
  "content": {
    "type": "link",
    "text": "https://example.com/article",
    "media_path": null,
    "high_res_media_path": null,
    "media_image_base64": null,
    "url": "https://example.com/article",
    "title": "示例文章"
  },
  "group_name": "测试群聊",
  "window_detected": true,
  "window_title": "Browser",
  "metadata": {
    "producer": "atspi_observer",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:34.345678",
    "extracted_at": "2025-01-12T14:30:34.567890",
    "window_opened": true,
    "link_data": true,
    "url": "https://example.com/article"
  }
}
```

## 消息检测逻辑

### 决策流程

```
1. 检测新消息
   ↓
2. 点击消息
   ↓
3. 检测是否有新窗口打开
   ├─ 否 → 文本消息 (text)
   └─ 是 → 继续判断
           ↓
       获取窗口标题
           ↓
       ├─ "Photos and Videos" → 图片/视频 (photo/video)
       └─ 其他 → 文件/链接/其他 (file/link/other)
                  ↓
              保存到物理机
```

### 窗口标题映射

| 窗口标题 | 消息类型 | 处理方式 |
|---------|---------|---------|
| (无窗口) | text | 直接推送，不保存文件 |
| Photos and Videos | photo/video | 提取并保存到 `/host/data/photos/` 或 `/host/data/videos/` |
| File Transfer | file | 保存到 `/host/data/files/` |
| Browser | link | 记录链接信息 |
| 其他 | other | 保存到 `/host/data/others/` |

## 文件保存路径规范

### 物理机挂载点

```yaml
# docker-compose.yml
services:
  wechat_sandbox:
    volumes:
      - /host/path/to/data:/host/data
    # 容器内路径: /host/data
    # 物理机路径: /host/path/to/data
```

### 目录结构

```
/host/data/
├── photos/          # 图片文件
├── videos/          # 视频文件
├── files/           # 其他文件
├── links/           # 链接元数据（JSON文件）
└── others/          # 其他类型
```

### 文件命名规范

```
{type}_{YYYYMMDD}_{HHMMSS}{ext}
```

示例:
- `photo_20250112_143025.png`
- `video_20250112_143028.mp4`
- `file_20250112_143031.pdf`

## SSE推送格式

### HTTP响应头

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### 事件格式

```
data: {"id":"msg_20250112_143022_001",...}
data: {"id":"msg_20250112_143025_002",...}
data: {"id":"msg_20250112_143028_003",...}
```

### 客户端示例

```javascript
const eventSource = new EventSource('/api/stream/messages');

eventSource.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);

    // 根据类型处理
    switch(message.type) {
        case 'text':
            console.log('文本消息:', message.content.text);
            break;
        case 'photo':
        case 'video':
            console.log('媒体文件:', message.content.high_res_media_path);
            break;
        case 'file':
            console.log('文件:', message.content.high_res_media_path);
            break;
    }
};
```

## 数据验证

### JSON Schema（可选）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "timestamp", "type", "sender", "content", "group_name", "window_detected", "metadata"],
  "properties": {
    "id": {"type": "string"},
    "timestamp": {"type": "number"},
    "type": {"enum": ["text", "photo", "video", "file", "link", "other"]},
    "sender": {"type": "string"},
    "content": {
      "type": "object",
      "required": ["type", "text"],
      "properties": {
        "type": {"type": "string"},
        "text": {"type": "string"},
        "media_path": {"type": ["string", "null"]},
        "high_res_media_path": {"type": ["string", "null"]},
        "media_image_base64": {"type": ["string", "null"]}
      }
    },
    "group_name": {"type": "string"},
    "window_detected": {"type": "boolean"},
    "window_title": {"type": ["string", "null"]},
    "metadata": {"type": "object"}
  }
}
```

## 示例文件

完整的示例数据见: `sse_message_model.jsonl`

---

**版本**: v1.0
**最后更新**: 2025-01-12
