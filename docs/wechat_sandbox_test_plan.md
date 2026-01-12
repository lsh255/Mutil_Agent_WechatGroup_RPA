# 微信沙盒数据采集和SSE推送测试方案

## 测试目标

验证 wechat_sandbox 双生产者架构和 AT-SPI 混合方案的完整数据流：

### 双生产者架构（视觉方案）
- **Producer1 (Observer)**: 检测消息气泡 → 推送到原始队列
- **Producer2 (ContentFetcher)**: 消费原始队列 → 提取精确内容 → 推送到精确队列
- **SSE Stream**: 从精确队列推送消息到前端

### AT-SPI 混合方案
- **主要方案**: AT-SPI UI控件监听 → 直接提取文本内容 → 推送到精确队列
- **兜底方案**: 视觉技术（当AT-SPI不可用时自动降级）
- **SSE Stream**: 从精确队列推送消息到前端

## 测试环境要求

### 1. 基础服务
- **Redis**: 7.2+ (用于消息队列)
- **Docker**: 20.10+ (用于容器化微信沙盒)
- **Python**: 3.10+ (用于测试脚本)

### 2. 微信环境
- **微信PC客户端**: 已登录状态（版本 4.1.13+）
- **测试群聊**: 至少包含3个成员（用于测试多人消息）
- **测试消息类型**:
  - 纯文本消息
  - 图片消息
  - 视频消息
  - 链接消息
  - 表情消息

### 3. AT-SPI 环境（可选，用于AT-SPI测试）
- **AT-SPI 支持**: Linux 微信版本需支持辅助功能
- **环境变量**:
  - `QT_ACCESSIBILITY=1`
  - `GNOME_ACCESSIBILITY=1`
  - `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`
- **工具**: Accerciser（用于调试UI控件树）

### 4. 配置检查清单

```bash
# 检查Redis连接
redis-cli ping
# 预期输出: PONG

# 检查Redis Stream队列（测试前应为空或已清空）
redis-cli XLEN wechat:messages:raw
redis-cli XLEN wechat:messages:precise

# 检查Docker服务
docker ps

# 检查AT-SPI环境（可选）
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY"
```

## 测试方案设计

### 测试一：AT-SPI 基础功能测试

#### 目标
验证 AT-SPI 方案的基础功能：初始化、窗口查找、控件遍历、消息提取

#### 适用场景
- AT-SPI 混合方案测试环境（`wechat_sandbox-test:latest` 镜像）
- 需要验证微信是否支持 AT-SPI

#### 步骤

**1.1 启动测试环境**

```bash
# 方式1: 使用 docker-compose（推荐）
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 方式2: 从 sandbox 目录
cd docker/sandbox
docker-compose -f docker-compose.test.yml up -d
```

**1.2 运行 AT-SPI 简单测试**

```bash
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py
```

**预期结果**:
```
✅ pyatspi已导入
   版本: 2.x.x

✅ 获取Registry成功

✅ 获取Desktop成功
Desktop类型: <class 'pyatspi.Accessible'>
Desktop名称: main
Desktop角色: frame
Desktop子项数量: 2

正在遍历2个应用...
  [0] wechat (application)
  [1] accerciser (application)
```

**1.3 运行 AT-SPI 完整测试**

```bash
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh
```

**测试内容**:
- 测试1: AT-SPI 观察者基础功能
- 测试2: 实时监听新消息（10秒）
- 测试3: 混合生产者测试（可选）

**预期结果**:
```
========================================
AT-SPI混合方案测试脚本
========================================

✅ QT_ACCESSIBILITY=1

✅ AT-SPI服务正在运行

✅ pyatspi已安装

✅ 微信正在运行

========================================
测试1：AT-SPI观察者基础功能
========================================

正在初始化AT-SPI观察者...

✅ AT-SPI初始化成功
   微信窗口: Weixin (角色: frame)

正在获取当前消息列表...
✅ 找到 X 条消息

最近的消息:
  1. [张三] 今天天气不错
  2. [李四] 是啊，适合出去玩
  ...

✅ 测试1通过
```

#### 故障排查

**问题1**: 找不到微信应用
```bash
# 检查微信是否运行
docker exec -it wechat_sandbox_test ps aux | grep wechat

# 检查QT_ACCESSIBILITY环境变量
docker exec -it wechat_sandbox_test env | grep QT_ACCESSIBILITY

# 解决方案：重启微信并设置环境变量
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/restart_wechat_with_dbus.sh
```

**问题2**: AT-SPI 服务未运行
```bash
# 检查 AT-SPI 进程
docker exec -it wechat_sandbox_test ps aux | grep at-spi

# 启动 AT-SPI 服务
docker exec -it wechat_sandbox_test /usr/libexec/at-spi-bus-launcher --launch-immediately &
```

### 测试二：AT-SPI 混合生产者测试

#### 目标
验证 AT-SPI 混合生产者：UI控件监听 + 视觉兜底

#### 适用场景
- 验证 AT-SPI 为主、视觉为兜底的混合方案
- 测试自动降级切换机制

#### 步骤

**2.1 启动混合生产者**

```bash
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer
```

**预期行为**:
1. 初始化 AT-SPI 观察者
2. 初始化视觉兜底方案
3. 启动混合生产者
4. 监听新消息并推送到 Redis

**2.2 监控 Redis 队列**

```bash
# 监控精确队列
docker exec -it wechat_redis_test redis-cli XLEN wechat:messages:precise

# 实时查看最新消息
docker exec -it wechat_redis_test redis-cli XREVRANGE wechat:messages:precise - + COUNT 1
```

**2.3 发送测试消息**

在微信群中发送测试消息：
- 纯文本："测试消息1"
- 带图片：发送一张图片
- 带链接：分享一个链接

**2.4 验证数据流**

```bash
# 使用测试脚本监听SSE流
cd tests
python sse_client.py
```

**预期结果**:
```
[INFO] 连接到SSE流: http://localhost:8000/api/stream/messages
[INFO] 等待消息...

[2025-01-12 12:00:00] 收到新消息:
  发送者: 张三
  内容: 测试消息1
  类型: text
  来源: atspi  # ← AT-SPI 成功提取

[2025-01-12 12:01:00] 收到新消息:
  发送者: 李四
  内容: [图片]
  类型: image
  来源: visual  # ← 视觉兜底方案

[2025-01-12 12:02:00] 收到新消息:
  发送者: 王五
  内容: https://example.com
  类型: link
  来源: atspi
```

#### 性能指标

| 指标 | AT-SPI | 视觉兜底 | 说明 |
|------|--------|----------|------|
| 消息提取速度 | <100ms | 500-1000ms | AT-SPI 更快 |
| CPU 占用 | 5-10% | 30-50% | AT-SPI 更低 |
| 内存占用 | 50MB | 200MB | AT-SPI 更少 |
| 准确率 | 99% | 95% | AT-SPI 更准确 |
| 兼容性 | 特定版本 | 通用 | 视觉更兼容 |

### 测试三：双生产者架构测试（视觉方案）

#### 目标
验证传统的双生产者架构：Observer + ContentFetcher

#### 适用场景
- 不支持 AT-SPI 的环境
- 验证视觉方案的基础功能

#### 步骤

**3.1 启动双生产者**

```bash
docker exec -it wechat_sandbox python3 -m core.producer.visual_producer
```

**3.2 监控原始队列**

```bash
# 查看原始队列长度
docker exec -it wechat_redis_test redis-cli XLEN wechat:messages:raw

# 查看原始队列内容
docker exec -it wechat_redis_test redis-cli XREVRANGE wechat:messages:raw - + COUNT 10
```

**预期结果**:
```json
{
  "message_id": "msg_001",
  "timestamp": "2025-01-12T12:00:00",
  "sender": "张三",
  "content_snapshot": "测试消息",
  "image_path": "/app/media/msg_001.png",
  "bbox": [100, 200, 300, 250]
}
```

**3.3 监控精确队列**

```bash
# 查看精确队列
docker exec -it wechat_redis_test redis-cli XREVRANGE wechat:messages:precise - + COUNT 10
```

**预期结果**:
```json
{
  "message_id": "msg_001",
  "timestamp": "2025-01-12T12:00:00",
  "sender": "张三",
  "content": "测试消息",
  "type": "text",
  "source": "visual"
}
```

### 测试四：SSE 推送测试

#### 目标
验证 SSE 接口实时推送消息到前端

#### 步骤

**4.1 使用测试客户端**

```bash
cd tests
python sse_client.py
```

**4.2 监听特定群聊**

```bash
curl -N http://localhost:8000/api/stream/messages?group_id=测试群
```

**4.3 验证消息格式**

**预期SSE格式**:
```
event: message
data: {"id":"msg_001","sender":"张三","content":"测试消息","type":"text","timestamp":"2025-01-12T12:00:00"}

event: heartbeat
data: {"timestamp":"2025-01-12T12:00:05"}
```

### 测试五：性能和稳定性测试

#### 目标
验证系统在高负载下的性能和稳定性

#### 步骤

**5.1 性能测试**

```bash
cd tests
python sse_performance_test.py --messages 100 --interval 1
```

**测试指标**:
- 消息处理延迟
- SSE 推送延迟
- Redis 队列堆积
- CPU/内存占用

**5.2 长时间运行测试**

```bash
# 运行24小时测试
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer --duration 86400
```

**5.3 内存泄漏检测**

```bash
# 监控内存使用
docker stats wechat_sandbox_test --no-stream

# 检查内存增长
docker exec -it wechat_sandbox_test python3 -c "
import psutil
import time
process = psutil.Process()
for i in range(10):
    print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB')
    time.sleep(60)
"
```

## 测试结果记录

### 测试结果模板

```markdown
## 测试执行记录

**测试日期**: 2025-01-12
**测试环境**: Docker (wechat_sandbox-test:latest)
**测试人员**: [姓名]

### 测试一：AT-SPI 基础功能测试
- [ ] AT-SPI 初始化
- [ ] 微信窗口查找
- [ ] 消息列表获取
- [ ] 实时监听
- **结果**: ✅ 通过 / ❌ 失败

### 测试二：AT-SPI 混合生产者测试
- [ ] AT-SPI 消息提取
- [ ] 视觉兜底切换
- [ ] Redis 队列推送
- **结果**: ✅ 通过 / ❌ 失败
- **性能指标**:
  - 消息延迟: XXms
  - CPU 占用: XX%
  - 内存占用: XXMB

### 测试三：双生产者架构测试
- [ ] Observer 检测
- [ ] ContentFetcher 提取
- [ ] 队列流转
- **结果**: ✅ 通过 / ❌ 失败

### 测试四：SSE 推送测试
- [ ] SSE 连接建立
- [ ] 实时消息推送
- [ ] 心跳保持
- **结果**: ✅ 通过 / ❌ 失败

### 测试五：性能测试
- [ ] 100条消息处理
- [ ] 24小时稳定性
- [ ] 内存泄漏检测
- **结果**: ✅ 通过 / ❌ 失败

### 问题记录
1. [问题描述]
   - 重现步骤:
   - 错误日志:
   - 解决方案:

### 总结
[测试总结和改进建议]
```

## 常见问题和解决方案

### 问题1: AT-SPI 找不到微信窗口

**症状**:
```
❌ 找不到微信窗口
```

**排查步骤**:
1. 检查微信是否运行
2. 检查 QT_ACCESSIBILITY 环境变量
3. 使用 Accerciser 查看 UI 控件树

**解决方案**:
```bash
# 重启微信（使用 DBus 会话）
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/restart_wechat_with_dbus.sh

# 或使用 Accerciser 调试
docker exec -it wechat_sandbox_test bash -c "accerciser &"
```

### 问题2: Redis 连接失败

**症状**:
```
Error: Cannot connect to Redis
```

**解决方案**:
```bash
# 检查 Redis 容器状态
docker ps | grep redis

# 检查 Redis 日志
docker logs wechat_redis_test

# 重启 Redis
docker restart wechat_redis_test
```

### 问题3: SSE 连接断开

**症状**:
```
[ERROR] SSE connection lost
```

**解决方案**:
```bash
# 检查服务状态
docker exec -it wechat_sandbox_test ps aux | grep python

# 查看服务日志
docker logs wechat_sandbox_test

# 重启服务
docker restart wechat_sandbox_test
```

## 相关文档

- [AT-SPI 混合方案说明](atspi_hybrid_solution.md)
- [AT-SPI 部署配置说明](atspi_deployment_config.md)
- [Docker 主文档](../docker/README.md)
- [微信沙盒架构文档](../services/wechat_sandbox/ARCHITECTURE.md)

## 测试脚本位置

所有测试脚本位于 `tests/` 目录：

```
tests/
├── atspi/                      # AT-SPI 测试
│   ├── test_atspi_observer.py  # AT-SPI 观察者单元测试
│   └── test_atspi_integration.py  # AT-SPI 集成测试
├── wechat_sandbox/             # 微信沙盒测试
│   ├── sse_client.py           # SSE 客户端
│   ├── sse_performance_test.py # SSE 性能测试
│   ├── queue_monitor.py        # Redis 队列监控
│   └── quick_test.sh           # 快速测试脚本
└── README.md                   # 测试文档
```

## 快速测试命令

```bash
# 1. 启动测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 2. 运行 AT-SPI 简单测试
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py

# 3. 运行 AT-SPI 完整测试
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh

# 4. 启动混合生产者
docker exec -it wechat_sandbox_test python3 -m core.producer.hybrid_producer

# 5. 监听 SSE 流
cd tests && python wechat_sandbox/sse_client.py

# 6. 监控 Redis 队列
cd tests && python wechat_sandbox/queue_monitor.py
```

## 附录

### A. Redis 命令参考

```bash
# 查看队列长度
XLEN wechat:messages:raw
XLEN wechat:messages:precise

# 查看最新消息
XREVRANGE wechat:messages:precise - + COUNT 10

# 清空队列
DEL wechat:messages:raw
DEL wechat:messages:precise

# 监控队列操作
MONITOR
```

### B. Docker 命令参考

```bash
# 查看容器日志
docker logs -f wechat_sandbox_test

# 进入容器
docker exec -it wechat_sandbox_test bash

# 查看资源占用
docker stats wechat_sandbox_test

# 复制文件到容器
docker cp test.py wechat_sandbox_test:/app/
```

### C. AT-SPI 调试工具

**Accerciser 使用**:
```bash
# 启动 Accerciser
docker exec -it wechat_sandbox_test bash -c "DISPLAY=:99 accerciser &"

# 在 noVNC 中使用 Accerciser
# 1. 打开 http://localhost:6080
# 2. 在终端运行: accerciser
# 3. 浏览 UI 控件树
```
