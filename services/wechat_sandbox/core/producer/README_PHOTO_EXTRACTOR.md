# Photo消息高清图片提取功能说明

## 概述

本模块实现了微信Photo消息的自动检测和高清图片提取功能。当指定聊天窗口收到Photo消息时，系统会自动：

1. 检测photo类型的消息
2. 点击photo消息区域唤起"Photos and Videos"窗口
3. 从"Photos and Videos"窗口提取高清图片
4. 将高清图片保存到指定目录

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    Photo提取流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. ATSPIObserver                                            │
│     ├── 监听消息列表控件                                      │
│     └── 检测新消息                                            │
│            ↓                                                 │
│  2. 消息类型判断                                              │
│     ├── is_photo_message()  → 判断是否为photo消息            │
│     └── 普通消息 → 跳过                                       │
│            ↓ (如果是photo)                                    │
│  3. PhotoExtractor                                           │
│     ├── get_message_bounds()   → 获取消息坐标               │
│     ├── click_message()        → 点击photo消息              │
│     ├── wait_for_photos_window() → 等待Photos窗口打开       │
│     ├── extract_high_res_image() → 提取高清图片             │
│     └── close_photos_window()   → 关闭Photos窗口            │
│            ↓                                                 │
│  4. 保存高清图片                                              │
│     └── /path/to/save_dir/photo_YYYYMMDD_HHMMSS.png         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 消息流

```
RawMessage (AT-SPI)
    ├── sender: "张三"
    ├── content: "[Photo]"
    ├── message_type: "photo"
    ├── image_path: null (缩略图)
    └── high_res_image_path: "/tmp/wechat_photos/photo_20250112_143022.png"
                              ↓
                         HybridProducer
                              ↓
                         Redis Stream (Precise Queue)
                              ↓
                         SSEConsumer / MultimodalNode
```

## 使用方法

### 1. 基本使用（独立使用PhotoExtractor）

```python
from core.producer.photo_extractor import PhotoExtractor

# 创建提取器，指定保存目录
extractor = PhotoExtractor(save_dir="/tmp/wechat_photos")

# 初始化AT-SPI连接
if extractor.initialize():
    # 检查消息是否为photo类型
    is_photo = extractor.is_photo_message(message_item)

    if is_photo:
        # 提取高清图片
        photo_msg = extractor.extract_photo_message(message_item)

        if photo_msg:
            print(f"发送者: {photo_msg.sender}")
            print(f"高清图片: {photo_msg.high_res_path}")
```

### 2. 集成到ATSPIObserver（推荐）

```python
from core.producer.atspi_observer import ATSPIObserver

# 创建观察者，启用photo提取功能
observer = ATSPIObserver(
    enable_photo_extraction=True,  # 启用photo提取
    photo_save_dir="/tmp/wechat_photos"  # 指定保存目录
)

# 初始化
if observer.initialize():
    # 添加回调函数
    def on_new_message(message):
        if message.message_type == "photo":
            print(f"收到Photo消息: {message.sender}")
            print(f"高清图片路径: {message.high_res_image_path}")
        else:
            print(f"收到普通消息: {message.content}")

    observer.add_callback(on_new_message)

    # 开始监听
    observer.start_monitoring(interval=0.5)
```

### 3. 在HybridProducer中使用

```python
from core.producer.hybrid_producer import HybridProducer, ProductionMode

# 创建混合生产者（自动使用ATSPIObserver的photo功能）
producer = HybridProducer(
    redis_client=redis_client,
    mode=ProductionMode.HYBRID
)

# 初始化
if producer.initialize():
    # 启动生产者
    producer.start()

    # 在ATSPIObserver中启用photo提取（需要在初始化前配置）
    # 修改 hybrid_producer.py 中的 _init_atspi_observer 方法：
    # self.atspi_observer = ATSPIObserver(
    #     enable_photo_extraction=True,
    #     photo_save_dir="/tmp/wechat_photos"
    # )
```

## 配置说明

### PhotoExtractor初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `save_dir` | `str` | `/tmp/wechat_photos` | 图片保存目录 |

### ATSPIObserver初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_photo_extraction` | `bool` | `False` | 是否启用photo提取 |
| `photo_save_dir` | `str` | `None` | 图片保存目录 |

## 消息格式

### ATSPIMessage（Photo消息）

```python
@dataclass
class ATSPIMessage:
    sender: str                          # 发送者
    content: str                         # 内容（通常是"[Photo]"）
    timestamp: str                       # 时间戳
    message_type: str                    # "photo"
    image_path: Optional[str] = None     # 缩略图路径（通常为None）
    high_res_image_path: Optional[str]   # 高清图片路径
    raw_object: Optional[object] = None  # 原始AT-SPI对象
```

### RawMessage（Schema）

```python
class RawMessage(BaseModel):
    msg_id: str
    timestamp: float
    sender: str
    content: str
    message_type: MessageType  # PHOTO
    image_path: Optional[str]  # 缩略图
    high_res_image_path: Optional[str]  # 高清图片
    group_id: Optional[str]
    metadata: Dict[str, Any]
```

### 精确消息队列（Redis Stream）

```json
{
  "id": "msg_20250112_143022_123456",
  "timestamp": "2025-01-12T14:30:22.123456",
  "type": "photo",
  "sender": "张三",
  "content": {
    "type": "photo",
    "text": "[Photo]",
    "media_path": null,
    "high_res_media_path": "/tmp/wechat_photos/photo_20250112_143022.png",
    "media_image_base64": null
  },
  "metadata": {
    "producer": "hybrid_producer_atspi",
    "production_mode": "atspi",
    "processed_at": "2025-01-12T14:30:23.000000",
    "is_photo": true
  }
}
```

## 工作流程详解

### 1. Photo消息检测

系统通过以下方式检测photo消息：

```python
def is_photo_message(self, message_item) -> bool:
    # 方法1: 通过角色名称判断（image/icon/picture）
    # 方法2: 通过控件名称判断（photo/图片/照片）
    # 方法3: 通过AT-SPI属性判断
    # 方法4: 通过父级结构判断
```

### 2. 点击Photo消息

```python
# 获取消息的屏幕坐标
bounds = extractor.get_message_bounds(message_item)
# {'x': 100, 'y': 200, 'width': 300, 'height': 400}

# 点击消息中心点
extractor.click_message(bounds)
# 使用xdotool或pyautogui执行点击
```

### 3. 等待Photos窗口

```python
# 等待"Photos and Videos"窗口打开（最多5秒）
success = extractor.wait_for_photos_window(timeout=5.0)
```

### 4. 提取高清图片

系统尝试两种方式提取高清图片：

**方法1: 查找图片路径**
```python
# 在Photos窗口的UI控件树中查找图片路径
image_path = extractor._find_image_path_in_window()
# 如果找到路径，复制或下载到保存目录
```

**方法2: 截图保存**
```python
# 如果找不到路径，截取Photos窗口的截图
screenshot_path = extractor._screenshot_photos_window()
```

### 5. 关闭Photos窗口

```python
# 使用AT-SPI或快捷键关闭窗口
extractor.close_photos_window()
```

## 性能优化

### 异步处理

为了避免阻塞消息流，高清图片的提取在后台线程中异步执行：

```python
# 在ATSPIObserver中
def extract_photo_async():
    photo_msg = self.photo_extractor.extract_photo_message(item)
    # 异步处理，不阻塞其他消息

photo_thread = threading.Thread(target=extract_photo_async, daemon=True)
photo_thread.start()
```

### 非阻塞消息流

即使photo消息的高清图片正在提取，消息也会立即推送到队列：

- 消息立即推送到Redis Stream
- `high_res_image_path` 字段初始为 `None`
- 高清图片提取完成后，可以触发回调通知（可选）

## 依赖项

### 系统依赖

```bash
# AT-SPI相关
libatspi2.0-0
at-spi2-core
python3-pyatspi

# 点击工具
xdotool

# 截图工具（备选）
scrot
imagemagick
```

### Python依赖

```bash
pyautogui  # 可选，用于点击
```

## 故障排查

### 问题1: Photo消息检测失败

**症状**: 无法识别photo消息

**解决方案**:
1. 使用Accerciser查看UI控件树结构
2. 调整 `is_photo_message()` 中的检测逻辑
3. 检查photo消息的AT-SPI属性和角色

### 问题2: 点击操作失败

**症状**: 点击photo消息后没有反应

**解决方案**:
1. 检查xdotool是否已安装: `which xdotool`
2. 验证坐标计算是否正确
3. 尝试使用pyautogui代替xdotool

### 问题3: Photos窗口未打开

**症状**: 点击后等待超时

**解决方案**:
1. 增加等待时间: `wait_for_photos_window(timeout=10.0)`
2. 检查微信窗口是否在前台
3. 手动测试点击photo消息是否能打开窗口

### 问题4: 高清图片提取失败

**症状**: 窗口打开但无法提取图片

**解决方案**:
1. 使用Accerciser查看Photos窗口的UI控件树
2. 调整 `_find_image_path_in_window()` 的查找逻辑
3. 确保截图工具（scrot/imagemagick）已安装

## 测试方法

### 手动测试

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 运行Photo提取器测试
cd /app
python3 -m core.producer.photo_extractor

# 或运行ATSPIObserver测试（启用photo功能）
python3 -m core.producer.atspi_observer
```

### 自动化测试

```python
# 测试Photo提取功能
from core.producer.atspi_observer import ATSPIObserver
import time

observer = ATSPIObserver(
    enable_photo_extraction=True,
    photo_save_dir="/tmp/test_photos"
)

if observer.initialize():
    def on_message(msg):
        if msg.message_type == "photo":
            print(f"✅ Photo消息检测成功")
            print(f"   发送者: {msg.sender}")
            print(f"   高清图片: {msg.high_res_image_path}")

    observer.add_callback(on_message)
    observer.start_monitoring(interval=1.0)

    # 监听60秒
    time.sleep(60)
```

## 配置示例

### Docker Compose配置

```yaml
services:
  wechat_sandbox:
    environment:
      - PHOTO_EXTRACTION_ENABLED=true
      - PHOTO_SAVE_DIR=/app/data/photos
    volumes:
      - ./data/photos:/app/data/photos
```

### 环境变量

```bash
# 启用Photo提取
export PHOTO_EXTRACTION_ENABLED=true

# 设置保存目录
export PHOTO_SAVE_DIR=/app/data/photos
```

## 限制和注意事项

1. **性能影响**: photo提取需要点击和等待窗口，可能影响消息处理速度
2. **后台处理**: 建议启用异步处理，避免阻塞消息流
3. **窗口管理**: 确保Photos窗口能正确关闭，避免窗口堆积
4. **依赖工具**: 需要安装xdotool和截图工具
5. **UI变化**: 微信界面变化可能影响photo检测逻辑，需要定期维护

## 未来改进

1. **批量处理**: 支持批量提取多个photo消息的高清图片
2. **缓存机制**: 缓存已提取的photo，避免重复提取
3. **失败重试**: 添加提取失败的重试机制
4. **进度通知**: 通过SSE推送photo提取进度
5. **多格式支持**: 支持提取video等其他媒体类型

---

**文档版本**: v1.0
**最后更新**: 2025-01-12
**维护者**: Claude Code
