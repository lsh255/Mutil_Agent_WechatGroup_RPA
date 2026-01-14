# 消息类型处理方案 v2.0

## 📋 概述

简化消息类型处理，**仅处理3种消息类型**，其他类型直接保存到物理机。

## 🎯 支持的消息类型

### SSE推送消息（3种）
| 类型 | 英文 | 说明 | 示例 |
|------|------|------|------|
| 文本 | text | 纯文本消息 | "你好" |
| 图片 | photo | 图片消息（含缩略图） | [图片] |
| 视频 | video | 视频消息 | [视频00:30] |

### 保存到物理机（其他类型）
| 类型 | 说明 | 保存路径 |
|------|------|---------|
| 文件 | 文档、压缩包等 | `/host/data/others/file_*.json` |
| 链接 | URL链接 | `/host/data/others/link_*.json` |
| 表情包 | 表情、贴纸等 | `/host/data/others/other_*.json` |
| 其他 | 其他未识别类型 | `/host/data/others/other_*.json` |

## 🔄 处理流程

### AT-SPI方案
```
1. 监听控件树
   ↓
2. 判断消息类型（text/photo/video/other）
   ↓
3a. 如果是text/photo/video → 组装JSONL → 推送SSE
   ↓
3b. 如果是other → 保存元数据到物理机 → 不推送SSE
```

### 视觉方案
```
1. 点击消息
   ↓
2. 检测窗口标题
   ↓
3. 判断消息类型
   ├─ 无窗口 → text → 推送SSE
   ├─ "Photos and Videos" → photo/video → 推送SSE
   └─ 其他窗口 → 保存元数据到物理机 → 不推送SSE
```

### 混合方案
```
1. AT-SPI识别类型（快速）
   ↓
2. 如果是text/photo/video → 立即推送SSE
   ↓
3. 如果是photo/video且需要保存文件 → 异步视觉提取
   ↓
4. 如果是other → 保存到物理机 → 不推送SSE
```

## 📂 文件结构

```
/host/data/
├── photos/          # 图片文件（仅photo类型）
├── videos/          # 视频文件（仅video类型）
└── others/          # 其他类型元数据（JSON格式）
    ├── file_*.json  # 文件元数据
    ├── link_*.json  # 链接元数据
    └── other_*.json # 其他类型元数据
```

## 💻 代码示例

### AT-SPI方案
```python
from core.atspi.observer import ATSPIObserver

# 仅处理3种类型：text/photo/video
observer = ATSPIObserver(
    enable_universal_extraction=False
)

if observer.initialize():
    def on_message(message):
        # 只会收到text/photo/video类型
        if message.message_type in ["text", "photo", "video"]:
            print(f"类型: {message.message_type}")
            print(f"发送者: {message.sender}")
            print(f"内容: {message.content}")

    observer.add_callback(on_message)
    observer.start_monitoring(interval=0.5)
```

### 视觉方案
```python
from core.extractor import UniversalMessageExtractor

extractor = UniversalMessageExtractor(save_dir="/host/data")

if extractor.initialize():
    # 只会返回text/photo/video类型
    extracted = extractor.extract_message(message_item, sender="张三")

    if extracted:
        # text/photo/video → 推送SSE
        sse_json = extracted.to_sse_json()
        print(sse_json)
    else:
        # other类型 → 已保存到物理机，不推送SSE
        print("其他类型已保存到物理机")
```

## 📊 SSE消息格式

### 文本消息
```json
{
  "id": "msg_20250114_143022_001",
  "timestamp": 1736856622.123,
  "type": "text",
  "sender": "张三",
  "content": {
    "type": "text",
    "text": "你好",
    "media_path": null,
    "high_res_media_path": null,
    "media_image_base64": null
  },
  "group_name": "微信群聊",
  "window_detected": false,
  "window_title": null,
  "metadata": {...}
}
```

### 图片消息
```json
{
  "id": "msg_20250114_143025_002",
  "timestamp": 1736856625.456,
  "type": "photo",
  "sender": "李四",
  "content": {
    "type": "photo",
    "text": "[图片]",
    "media_path": "/host/data/photos/photo_20250114_143025.png",
    "high_res_media_path": "/host/data/photos/photo_20250114_143025.png",
    "media_image_base64": null
  },
  "group_name": "微信群聊",
  "window_detected": true,
  "window_title": "Photos and Videos",
  "metadata": {...}
}
```

### 视频消息
```json
{
  "id": "msg_20250114_143030_003",
  "timestamp": 1736856630.789,
  "type": "video",
  "sender": "王五",
  "content": {
    "type": "video",
    "text": "[视频00:30]",
    "media_path": null,
    "high_res_media_path": "/host/data/videos/video_20250114_143030.mp4",
    "media_image_base64": null
  },
  "group_name": "微信群聊",
  "window_detected": true,
  "window_title": "Photos and Videos",
  "metadata": {...}
}
```

## 🗂️ 物理机保存格式

### 文件元数据（`/host/data/others/file_*.json`）
```json
{
  "type": "file",
  "sender": "赵六",
  "window_title": "File Transfer",
  "file_path": "/path/to/file.pdf",
  "timestamp": "2025-01-14T14:30:35.123456"
}
```

### 链接元数据（`/host/data/others/link_*.json`）
```json
{
  "type": "link",
  "sender": "钱七",
  "url": "https://example.com",
  "window_title": "Browser",
  "timestamp": "2025-01-14T14:30:40.654321"
}
```

### AT-SPI保存的其他类型（`/host/data/others/others/file_*.json`）
```json
{
  "type": "link",
  "sender": "孙八",
  "url": "https://example.com",
  "timestamp": "2025-01-14T14:30:45.987654",
  "attributes": {...}
}
```

## ⚙️ 配置

### Docker Compose
```yaml
services:
  wechat_sandbox:
    volumes:
      - /path/on/host:/host/data  # 挂载物理机目录
    environment:
      - SAVE_DIR=/host/data
```

### 目录权限
```bash
# 确保容器有写权限
chmod 777 /path/on/host

# 或者使用特定用户
chown -R 1000:1000 /path/on/host
```

## 🔧 实现细节

### AT-SPI观察者修改
- 文件：`core/atspi/observer.py`
- 修改：`_extract_message_from_item`方法
- 逻辑：
  1. 从控件树提取消息类型
  2. 如果是other类型，调用`_save_other_type_to_disk`保存
  3. 如果是text/photo/video，构造消息对象返回

### 视觉提取器修改
- 文件：`core/message/extractor.py`
- 修改：`extract_message`、`determine_message_type`方法
- 逻辑：
  1. 点击消息，检测窗口
  2. 根据窗口标题判断类型
  3. 如果是other类型，调用`_save_other_type_to_disk`保存并返回None
  4. 如果是text/photo/video，构造消息对象返回

### SSE推送修改
- 文件：`core/message/extractor.py`
- 修改：`to_sse_json`方法
- 逻辑：
  1. 如果是OTHER类型，返回空字符串
  2. 如果是text/photo/video，组装JSONL格式返回

## 📝 注意事项

1. **消息类型限制**：
   - SSE只推送text/photo/video
   - 其他类型不推送，仅保存到物理机

2. **消费者处理**：
   - 消费者只需处理3种消息类型
   - 其他类型可以从物理机读取（如需要）

3. **性能优化**：
   - AT-SPI方案快速识别类型（~100ms）
   - 视觉方案仅用于photo/video文件提取（异步）
   - 不阻塞消息流

4. **文件清理**：
   - `/host/data/others/`目录会持续增长
   - 建议定期清理旧文件
   - 可添加定时任务清理N天前的文件

## 🚀 使用场景

### 场景1：只需要文本消息
```python
observer = ATSPIObserver(enable_universal_extraction=False)
# 只会收到text类型的消息
```

### 场景2：需要图片和视频
```python
observer = ATSPIObserver(enable_universal_extraction=True, save_dir="/host/data")
# 会收到text/photo/video类型的消息
# 图片和视频会异步保存到物理机
```

### 场景3：需要保存其他类型
```python
# 其他类型会自动保存到 /host/data/others/
# 可以定期读取和处理
import json
from pathlib import Path

others_dir = Path("/host/data/others")
for json_file in others_dir.glob("*.json"):
    with open(json_file) as f:
        data = json.load(f)
        print(f"类型: {data['type']}, 发送者: {data.get('sender')}")
```

---

**文档版本**：v2.0
**最后更新**：2025-01-14
**维护者**：Claude Code
