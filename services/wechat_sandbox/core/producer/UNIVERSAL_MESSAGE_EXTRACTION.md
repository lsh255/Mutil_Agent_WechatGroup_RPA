# 通用消息提取实现总结

## 概述

本文档总结了针对微信消息的通用提取实现，通过点击所有消息来判断类型并提取内容。

## 新逻辑流程

```
1. 检测新消息
   ↓
2. 点击消息（所有消息）
   ↓
3. 检测是否唤起新窗口
   ├─ 否 → 文本消息
   └─ 是 → 继续判断
           ↓
       获取窗口标题
           ↓
       ├─ "Photos and Videos" → 图片/视频
       ├─ "File Transfer" → 文件
       ├─ "Browser" → 链接
       └─ 其他 → 其他类型
                  ↓
              保存到物理机 (/host/data/)
```

## 文件变更

### 1. 新建文件

#### `photo_extractor.py` (已重构)
- **类**: `UniversalMessageExtractor`
- **功能**:
  - 点击所有消息
  - 检测新窗口
  - 根据窗口标题判断消息类型
  - 提取并保存文件到物理机

#### `sse_message_model.jsonl`
- SSE推送的JSONL格式示例文件

#### `SSE_MESSAGE_MODEL.md`
- SSE消息数据模型的详细定义文档

### 2. 修改的文件

#### `atspi_observer.py`
- 修改构造函数: `enable_universal_extraction`, `save_dir`
- 修改 `_extract_message_from_item()`: 集成通用提取逻辑

#### `hybrid_producer.py`
- 添加 `save_dir` 参数
- 修改 `_init_atspi_observer()`: 传递save_dir参数

#### `core/schemas.py`
- 已添加 `PHOTO` 消息类型
- 已添加 `high_res_image_path` 字段

## 消息类型映射

| 窗口标题 | 消息类型 | 保存目录 |
|---------|---------|---------|
| (无窗口) | text | 不保存 |
| Photos and Videos | photo/video | /host/data/photos/ 或 /host/data/videos/ |
| File Transfer | file | /host/data/files/ |
| Browser | link | /host/data/links/ |
| 其他 | other | /host/data/others/ |

## SSE推送格式 (JSONL)

### 格式说明
- 每行一个独立的JSON对象
- 通过SSE推送，每行前缀 `data: `
- 编码: UTF-8

### 示例

```javascript
// 文本消息
data: {"id":"msg_20250112_143022_001","timestamp":1736653822.123,"type":"text",...}

// 图片消息
data: {"id":"msg_20250112_143025_002","timestamp":1736653825.456,"type":"photo",...}
```

### 完整数据结构

```json
{
  "id": "msg_20250112_143022_001",
  "timestamp": 1736653822.123,
  "type": "text|photo|video|file|link|other",
  "sender": "发送者",
  "content": {
    "type": "text|photo|video|file|link|other",
    "text": "消息内容",
    "media_path": null,
    "high_res_media_path": "/host/data/photos/xxx.png",
    "media_image_base64": null
  },
  "group_name": "群聊名称",
  "window_detected": false,
  "window_title": null,
  "metadata": {
    "producer": "universal_extractor",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:22.123456",
    "extracted_at": "2025-01-12T14:30:22.234567",
    "window_opened": false
  }
}
```

## Docker配置

### 挂载物理机目录

```yaml
# docker-compose.yml
services:
  wechat_sandbox:
    volumes:
      - /path/on/host:/host/data
    environment:
      - SAVE_DIR=/host/data
```

### 目录结构

```
/host/data/
├── photos/    # 图片文件
├── videos/    # 视频文件
├── files/     # 其他文件
├── links/     # 链接元数据
└── others/    # 其他类型
```

## 使用示例

### 基本使用

```python
from core.producer.atspi_observer import ATSPIObserver

# 创建观察者，启用通用消息提取
observer = ATSPIObserver(
    enable_universal_extraction=True,
    save_dir="/host/data"
)

if observer.initialize():
    def on_message(message):
        print(f"类型: {message.message_type}")
        print(f"发送者: {message.sender}")
        print(f"内容: {message.content}")

    observer.add_callback(on_message)
    observer.start_monitoring(interval=0.5)
```

### 集成到HybridProducer

```python
from core.producer.hybrid_producer import HybridProducer, ProductionMode

producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.HYBRID,
    save_dir="/host/data"  # 文件保存到物理机
)

if producer.initialize():
    producer.start()
```

## 关键特性

1. **点击所有消息**: 不预判类型，统一处理
2. **窗口检测**: 通过检测新窗口判断消息类型
3. **文件保存**: 自动保存到物理机挂载目录
4. **异步处理**: 不阻塞消息流
5. **SSE推送**: JSONL格式，实时推送

## 依赖项

### 系统依赖
```bash
xdotool    # 点击工具
scrot      # 截图工具（可选）
```

### Python依赖
```bash
pyatspi    # AT-SPI绑定
```

## 注意事项

1. **性能影响**: 点击和窗口检测会增加处理时间
2. **异步处理**: 媒体提取在后台线程，不影响消息流
3. **文件权限**: 确保挂载目录有写权限
4. **窗口管理**: 确保窗口能正确关闭

## 测试方法

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 测试通用提取器
cd /app
python3 -m core.producer.photo_extractor

# 测试ATSPI观察者
python3 -m core.producer.atspi_observer
```

## 后续改进

1. **同步/异步模式切换**: 提供配置选项
2. **窗口标题白名单**: 可配置窗口标题映射
3. **文件分类**: 更精细的文件类型判断
4. **进度通知**: SSE推送提取进度
5. **失败重试**: 提取失败时的重试机制

---

**版本**: v1.0
**更新时间**: 2025-01-12
**作者**: Claude Code
