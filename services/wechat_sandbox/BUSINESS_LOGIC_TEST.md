# WeChat Sandbox 测试快速启动指南

本指南专门用于测试 WeChat Sandbox 的业务逻辑。

## 前置条件

### 1. 本地环境要求
- Python 3.10+
- Redis 服务器（本地或 Docker）
- Linux 系统（需要 xdotool、xclip）
- 微信 Linux 版（可选，用于完整测试）

### 2. 依赖安装

```bash
cd services/wechat_sandbox

pip install -r requirements.txt
```

### 3. Redis 启动

```bash
# 使用 Docker 启动 Redis
docker run -d --name test_redis -p 6379:6379 redis:7-alpine

# 或使用本地 Redis
redis-server
```

## 测试模式

### 模式1：单元测试（无微信）

运行独立的单元测试，测试各模块功能：

```bash
cd services/wechat_sandbox

# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_queue_manager.py -v
pytest tests/test_producer_service.py -v

# 查看测试覆盖率
pytest tests/ --cov=producer_service --cov-report=html
```

### 模式2：集成测试（模拟消息）

使用模拟数据测试完整流程：

```bash
cd services/wechat_sandbox

# 启动 FastAPI 服务（会自动启动 Producer1 和 Producer2）
python main.py

# 或使用备用启动脚本
python backup_start.py
```

然后在另一个终端发送测试消息到 Redis：

```bash
# 使用 redis-cli 插入测试消息
redis-cli
> XADD wechat:messages:raw * type text content "测试消息" timestamp "2024-01-01T00:00:00" priority 10
```

访问以下端点查看状态：
- 健康检查: http://localhost:8000/api/health
- 服务状态: http://localhost:8000/api/status
- SSE 消息流: http://localhost:8000/api/stream
- 配置管理: http://localhost:8000/api/config
- 实例管理: http://localhost:8000/api/instance/start, http://localhost:8000/api/instance/stop

### 模式3：完整测试（含微信）

需要完整的微信沙箱环境：

```bash
# 1. 构建测试镜像
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest .

# 2. 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 3. 访问 noVNC 登录微信
# 打开浏览器访问: http://localhost:6080/vnc.html
# 使用密码: wechat123 登录
# 在微信中扫码登录

# 4. 查看服务日志
docker-compose -f docker/compose/docker-compose.sandbox.test.yml logs -f wechat_sandbox

# 5. 测试消息流
# 在微信群中发送消息，观察 Producer Service 是否正确捕获
```

## API 测试

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8000/api/health

# 获取服务状态
curl http://localhost:8000/api/status

# 获取配置
curl http://localhost:8000/api/config

# 启动实例
curl -X POST http://localhost:8000/api/instance/start

# 停止实例
curl -X POST http://localhost:8000/api/instance/stop

# SSE 消息流
curl -N http://localhost:8000/api/stream
```

### 使用 Python 测试

```python
import requests
import json

# 测试健康检查
response = requests.get('http://localhost:8000/api/health')
print(response.json())

# 测试服务状态
response = requests.get('http://localhost:8000/api/status')
print(response.json())

# 测试配置
response = requests.get('http://localhost:8000/api/config')
print(response.json())

# 启动实例
response = requests.post('http://localhost:8000/api/instance/start')
print(response.json())

# 测试 SSE 流
response = requests.get('http://localhost:8000/api/stream', stream=True)
for line in response.iter_lines():
    if line:
        if line.startswith(b'data: '):
            data = json.loads(line[6:].decode())
            print(f"收到消息: {data}")
```

## 手动测试各模块

### 1. 测试 QueueManager

```python
from core.queue.manager import RedisQueueManager

# 初始化
qm = RedisQueueManager()

# 写入原始消息
msg = {
    'id': 'test_001',
    'type': 'text',
    'content': '测试消息',
    'timestamp': '2024-01-01T00:00:00'
}
qm.enqueue_raw(msg)

# 读取消息
messages = qm.read_raw_for_processing()
print(messages)

# 确认消息
if messages:
    qm.ack_raw(messages[0][0])
```

### 2. 测试 ChangeDetector

```python
from core.detector.detector import ChangeDetector
from PIL import Image

# 加载测试图片
img1 = Image.open('test_image_1.png')
img2 = Image.open('test_image_2.png')

# 初始化检测器
detector = ChangeDetector()

# 检测变化
changed = detector.detect_changes(img2, img1)
print(f"是否有变化: {changed}")

# 检测气泡
bubbles = detector.detect_bubbles(img2)
print(f"检测到 {len(bubbles)} 个气泡")
```

### 3. 测试 Classifier

```python
from core.classifier.classifier import MessageTypeClassifier
from PIL import Image

# 加载测试图片
img = Image.open('bubble_test.png')

# 初始化分类器
classifier = MessageTypeClassifier()

# 分类
msg_type = classifier.classify(img)
print(f"消息类型: {msg_type}")
```

### 4. 测试 Monitor（需要 xdotool）

```python
from core.producer.monitor import VisualMonitor

# 初始化监控器
monitor = VisualMonitor()

# 设置 ROI
monitor.set_roi(100, 100, 800, 600)

# 定位微信窗口
monitor.locate_wechat()

# 截取屏幕
screenshot = monitor.capture()
screenshot.save('screenshot.png')
```

## 调试技巧

### 1. 查看日志

```bash
# 查看 Redis Stream 状态
redis-cli
> XINFO STREAM wechat:messages:raw
> XINFO STREAM wechat:messages:precise

# 查看消费者组状态
> XINFO GROUPS wechat:messages:raw

# 查看特定消费者
> XINFO CONSUMERS wechat:messages:raw producer2_group
```

### 2. 清理测试数据

```bash
# 清空 Redis Stream
redis-cli
> DEL wechat:messages:raw
> DEL wechat:messages:precise

# 重置消费者组
> XGROUP DESTROY wechat:messages:raw producer2_group
```

### 3. 模拟消息

创建测试脚本 `test_send_message.py`:

```python
import json
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

# 模拟原始消息
raw_msg = {
    'id': f"test_{int(time.time())}",
    'timestamp': datetime.now().isoformat(),
    'type': 'raw_bubble',
    'bubble_img_base64': '',  # 填入 base64 图片
    'position': {'roi_x': 100, 'roi_y': 200, 'screen_x': 1100, 'screen_y': 400, 'width': 300, 'height': 80},
    'priority': 10,
    'metadata': {'producer': 'test', 'detection_time': datetime.now().isoformat()}
}

# 序列化并发送
fields = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in raw_msg.items()}
r.xadd('wechat:messages:raw', fields)
```

## 常见问题排查

### Producer1 未启动
```bash
# 检查微信窗口是否存在
xdotool search --name "WeChat"

# 检查 xdotool 是否可用
which xdotool
```

### Producer2 无法读取消息
```bash
# 检查 Redis Stream 是否有数据
redis-cli
> XRANGE wechat:messages:raw - + COUNT 10

# 检查消费者组状态
> XINFO GROUPS wechat:messages:raw
```

### 消息分类错误
```python
# 调试分类器
from core.classifier.classifier import MessageTypeClassifier
import cv2

classifier = MessageTypeClassifier()
img = cv2.imread('bubble.png')

# 查看中间结果
img_hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
# 在调试器中检查 img_hsv 的值
```

### SSE 流断开
```bash
# 检查 FastAPI 日志
docker-compose -f docker/compose/docker-compose.sandbox.test.yml logs -f wechat_sandbox | grep stream

# 使用 curl 测试连接
curl -N http://localhost:8000/stream
```

## 性能测试

### 1. 消息吞吐量测试

```python
import time
import redis

r = redis.Redis(host='localhost', port=6379, db=0)
start_time = time.time()

# 发送 1000 条消息
for i in range(1000):
    msg = {
        'id': f'perf_test_{i}',
        'timestamp': time.time(),
        'type': 'text',
        'content': f'性能测试消息 {i}'
    }
    fields = {k: str(v) for k, v in msg.items()}
    r.xadd('wechat:messages:raw', fields)

end_time = time.time()
print(f"发送 1000 条消息耗时: {end_time - start_time:.2f} 秒")
print(f"平均吞吐量: {1000 / (end_time - start_time):.2f} msg/s")
```

### 2. 内存使用监控

```bash
# 监控容器内存
docker stats wechat_sandbox_test

# 监控 Python 进程内存
docker exec wechat_sandbox_test ps aux | grep python
```

## 测试清单

### 基础功能
- [ ] QueueManager 能正确读写 Redis Stream
- [ ] ChangeDetector 能检测屏幕变化
- [ ] ChangeDetector 能正确识别消息气泡
- [ ] Classifier 能正确分类消息类型
- [ ] Monitor 能定位微信窗口并截屏

### 集成功能
- [ ] Producer1 能检测到新消息并入队
- [ ] Producer2 能从队列读取消息
- [ ] Producer2 能提取文本内容
- [ ] Producer2 能提取媒体内容
- [ ] SSE 流能正确推送消息

### API 功能
- [ ] /health 返回正确状态
- [ ] /status 显示服务详情
- [ ] /stream 正常推送消息
- [ ] /api/screenshot 能截取屏幕
- [ ] /api/restart 能重启服务

## 下一步

测试通过后，可以：
1. 部署到生产环境
2. 调整性能参数（捕获间隔、批处理大小）
3. 添加监控和告警
4. 扩展消息类型支持
