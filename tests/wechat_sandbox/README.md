# 微信沙盒测试工具集

本目录包含用于测试 wechat_sandbox 数据采集和SSE推送功能的完整测试工具。

## 目录结构

```
tests/wechat_sandbox/
├── README.md                    # 本文件
├── sse_client.py                # SSE客户端工具
├── sse_performance_test.py      # SSE性能测试工具
├── queue_monitor.sh             # Redis队列监控脚本（Bash）
├── queue_monitor.py             # Redis队列监控工具（Python）
└── test_results/                # 测试结果输出目录
    ├── messages_*.json          # 保存的消息记录
    └── queue_export_*.json      # 导出的队列数据
```

## 快速开始

### 1. 环境准备

**安装依赖**:
```bash
pip install redis aiohttp
```

**检查Redis连接**:
```bash
redis-cli ping
# 应该返回: PONG
```

**启动微信沙盒服务**:
```bash
cd services/wechat_sandbox
python main.py
```

### 2. 基础测试

#### 测试一：监听SSE流（基础验证）

**目标**: 验证SSE流是否正常工作

**步骤**:
```bash
# 终端1: 启动SSE客户端
python tests/wechat_sandbox/sse_client.py

# 终端2: 发送测试消息
# 在微信测试群中发送几条消息
```

**预期结果**:
- ✅ SSE客户端显示"连接成功"
- ✅ 接收到消息并显示内容
- ✅ 消息包含正确的字段（id, type, timestamp, precise_content等）

**成功标准**:
```
✅ 连接成功 (Status: 200)
📨 [消息 #1] 14:30:22
ID:         msg_20250112_143022_abc123
类型:       text
文本内容:   测试消息1
```

---

#### 测试二：监控队列状态（验证双生产者）

**目标**: 验证原始队列和精确队列的数据流转

**步骤**:
```bash
# 终端1: 启动队列监控
python tests/wechat_sandbox/queue_monitor.py

# 终端2: 发送测试消息
# 在微信群中发送消息
```

**预期结果**:
```
📥 原始队列 (Raw):            5 条消息
📤 精确队列 (Precise):        5 条消息
📊 处理进度:                100% (5/5)
```

**验证要点**:
- ✅ 原始队列消息数 ≥ 精确队列消息数
- ✅ 处理进度达到100%
- ✅ 消息延迟 < 3秒

---

#### 测试三：性能测试（验证实时性）

**目标**: 测试SSE推送的延迟和吞吐量

**步骤**:
```bash
# 启动性能测试（60秒）
python tests/wechat_sandbox/sse_performance_test.py --duration 60 --benchmark

# 在测试期间持续发送消息（建议至少50条）
```

**预期结果**:
```
📊 SSE性能测试报告
══════════════════════════════════════════════════════════════

📈 基本统计:
────────────────────────────────────────────────────────────
测试时长:           60.23 秒
接收消息数:         50 条
平均吞吐量:         0.83 条/秒

⏱️  消息延迟统计:
────────────────────────────────────────────────────────────
平均延迟:           850.32 ms
最小延迟:           234.12 ms
最大延迟:           2100.45 ms
中位数延迟:         780.00 ms

🎯 性能评级:
────────────────────────────────────────────────────────────
🟢 平均延迟 850ms - A (良好)
🟡 吞吐量 0.8 条/秒 - B (一般)
```

**成功标准**:
- ✅ 平均延迟 < 1秒
- ✅ 无错误、无重连
- ✅ 延迟标准差 < 500ms

---

## 详细测试场景

### 场景1：单用户单消息测试

**目的**: 验证基本功能

**步骤**:
```bash
# 1. 启动SSE客户端
python sse_client.py --verbose

# 2. 在微信群发送1条文本消息
# 3. 观察客户端输出
```

**验证**:
- [ ] 消息ID唯一
- [ ] 时间戳准确（误差<5秒）
- [ ] 消息类型正确（text/image/video）
- [ ] 文本内容完整

---

### 场景2：连续发送测试

**目的**: 验证消息不丢失、不乱序

**步骤**:
```bash
# 1. 启动SSE客户端并保存消息
python sse_client.py --save-json --client-id test1

# 2. 快速连续发送20条消息（使用脚本或手动）
# 3. 检查保存的JSON文件
```

**验证**:
- [ ] 接收消息数 = 发送消息数
- [ ] 消息ID按时间递增
- [ ] 消息内容完整
- [ ] 无重复消息

---

### 场景3：多媒体消息测试

**目的**: 验证不同消息类型的处理

**步骤**:
```bash
# 1. 启动SSE客户端
python sse_client.py --verbose

# 2. 依次发送:
#    - 纯文本消息
#    - 图片消息
#    - 视频消息
#    - 文件消息
#    - 混合消息（文本+图片）
```

**验证**:
- [ ] 文本消息: text字段非空
- [ ] 图片消息: media_path存在，media_image_base64非空
- [ ] 视频消息: type="video"，media_path存在
- [ ] 混合消息: text和media_path都存在

---

### 场景4：并发连接测试

**目的**: 验证多客户端并发接收

**步骤**:
```bash
# 1. 启动5个并发SSE客户端
for i in {1..5}; do
    python sse_client.py --client-id client_$i --save-json &
done

# 2. 发送10条消息
# 3. 检查每个客户端保存的JSON文件
```

**验证**:
- [ ] 每个客户端都接收到所有消息
- [ ] 消息数一致（都是10条）
- [ ] 消息内容一致
- [ ] 无连接中断

---

### 场景5：网络异常恢复测试

**目的**: 验证异常情况下的稳定性

**步骤**:
```bash
# 1. 启动SSE客户端
python sse_client.py

# 2. 发送3条消息

# 3. 模拟网络中断:
#    - 方法1: 拔网线
#    - 方法2: 断开WiFi
#    - 方法3: 防火墙阻断

# 4. 等待10秒

# 5. 恢复网络

# 6. 发送新消息
```

**验证**:
- [ ] 网络恢复后客户端自动重连
- [ ] 恢复后能接收新消息
- [ ] 无内存泄漏
- [ ] 重连次数正确记录

---

### 场景6：队列分析测试

**目的**: 深入分析队列数据

**步骤**:
```bash
# 1. 发送各类消息（文本、图片、视频等）

# 2. 分析原始队列
python queue_monitor.py --analyze

# 3. 分析精确队列
python queue_monitor.py --analyze

# 4. 导出队列数据
python queue_monitor.py --export --output test_results/queue_data.json
```

**验证**:
- [ ] 原始队列和精确队列长度一致
- [ ] 消息类型分布合理
- [ ] 导出的JSON文件格式正确
- [ ] 消息时间戳递增

---

### 场景7：压力测试

**目的**: 验证系统在高负载下的表现

**步骤**:
```bash
# 1. 启动性能测试
python sse_performance_test.py --duration 120 --benchmark

# 2. 快速连续发送100条消息（使用自动化脚本）
```

**验证**:
- [ ] 无消息丢失
- [ ] 延迟增长<50%
- [ ] 无内存溢出
- [ ] CPU使用率<80%

---

## 工具详细说明

### sse_client.py - SSE客户端工具

**功能**:
- 实时监听SSE流
- 显示消息内容
- 保存消息到JSON文件
- 支持详细输出模式

**用法**:
```bash
# 基础监听
python sse_client.py

# 详细输出（显示位置、元数据）
python sse_client.py --verbose

# 保存消息到JSON
python sse_client.py --save-json

# 指定客户端ID
python sse_client.py --client-id test_client_1

# 自定义保存目录
python sse_client.py --save-json --save-dir ./my_results
```

**输出示例**:
```
============================================================
客户端ID: default
连接URL: http://localhost:8000/api/stream/messages
============================================================

开始监听SSE流...
按 Ctrl+C 停止监听

✅ 连接成功 (Status: 200)
────────────────────────────────────────────────────────────

📨 [消息 #1] 14:30:22
────────────────────────────────────────────────────────────
ID:         msg_20250112_143022_abc123
类型:       text
时间戳:     2025-01-12T14:30:22.123456
文本内容:   测试消息1
────────────────────────────────────────────────────────────
```

---

### queue_monitor.py - 队列监控工具

**功能**:
- 实时监控Redis队列长度
- 显示最新消息内容
- 分析队列数据
- 导出队列数据到JSON

**用法**:
```bash
# 实时监控（每2秒刷新）
python queue_monitor.py

# 自定义刷新间隔
python queue_monitor.py --interval 5

# 分析模式
python queue_monitor.py --analyze

# 导出队列数据
python queue_monitor.py --export --output queue_data.json

# 连接远程Redis
python queue_monitor.py --host 192.168.1.100 --port 6379
```

**输出示例**:
```
╚════════════════════════════════════════════════════════════╝
║         微信沙盒队列监控 - 2025-01-12 14:30:22          ║
╚════════════════════════════════════════════════════════════╝

📥 原始队列 (Raw):               5 条消息
📤 精确队列 (Precise):           5 条消息
📊 处理进度:                [████████████████████████████████] 100%

────────────────────────────────────────────────────────────

📌 最新精确消息:
────────────────────────────────────────────────────────────
时间:     2025-01-12T14:30:22.123456
类型:     text
生产者:   producer2_content_fetcher
内容:     测试消息1
────────────────────────────────────────────────────────────

🔒 当前锁定消息:              0 条
💾 Redis内存使用:            2.5M (峰值: 3.1M)
╚════════════════════════════════════════════════════════════╝
```

---

### sse_performance_test.py - 性能测试工具

**功能**:
- 测试SSE延迟
- 测试吞吐量
- 测试稳定性（错误、重连）
- 生成性能报告

**用法**:
```bash
# 基础性能测试（无限时长，按Ctrl+C停止）
python sse_performance_test.py

# 测试60秒
python sse_performance_test.py --duration 60

# 基准测试模式（显示详细报告）
python sse_performance_test.py --duration 60 --benchmark

# 自定义SSE URL
python sse_performance_test.py --url http://192.168.1.100:8000/api/stream/messages
```

**性能指标说明**:

| 指标 | 说明 | 优秀阈值 |
|------|------|---------|
| 平均延迟 | 从发送到接收的平均时间 | <500ms |
| 吞吐量 | 每秒处理的消息数 | >5条/秒 |
| 错误次数 | 连接错误、解析错误 | 0 |
| 重连次数 | 连接中断后重连次数 | 0 |
| 延迟标准差 | 延迟波动程度 | <300ms |

**性能评级**:
- **A+ (优秀)**: 平均延迟<100ms
- **A (良好)**: 平均延迟<500ms
- **B (一般)**: 平均延迟<1s
- **C (较慢)**: 平均延迟<2s
- **D (慢)**: 平均延迟>2s

---

## 故障排查指南

### 问题1: SSE客户端无法连接

**症状**:
```
❌ 连接失败: HTTP 502
```

**排查步骤**:
1. 检查服务是否启动
```bash
curl http://localhost:8000/api/stream/messages
```

2. 检查端口是否被占用
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

3. 检查防火墙设置

---

### 问题2: 队列监控显示"无法连接到Redis"

**症状**:
```
❌ 无法连接到Redis: Error 111 connecting to localhost:6379
```

**排查步骤**:
1. 检查Redis是否启动
```bash
redis-cli ping
```

2. 检查Redis配置
```bash
# 检查端口
redis-cli -p 6379 ping

# 检查主机
redis-cli -h 127.0.0.1 ping
```

3. 检查Redis日志
```bash
tail -f /var/log/redis/redis-server.log
```

---

### 问题3: 接收不到消息

**症状**: SSE客户端已连接，但发送消息后无输出

**可能原因**:
1. **ROI配置错误**: 检查监控区域是否正确
```bash
# 查看配置
cat services/wechat_sandbox/config/settings.yaml | grep -A 5 roi
```

2. **微信群名不匹配**: 检查目标群聊名称
```bash
cat services/wechat_sandbox/config/settings.yaml | grep target_group_name
```

3. **微信窗口最小化**: 确保微信窗口在前台

4. **消息被过滤**: 检查是否触发过滤规则

**排查步骤**:
```bash
# 1. 检查原始队列
redis-cli XLEN wechat:messages:raw

# 2. 如果原始队列为0，说明Observer未检测到消息
#    - 检查ROI配置
#    - 检查微信窗口位置

# 3. 如果原始队列有数据但精确队列为空
#    - 说明ContentFetcher未处理
#    - 检查ContentFetcher日志

# 4. 如果精确队列有数据但SSE未推送
#    - 说明SSE流有问题
#    - 检查FastAPI日志
```

---

### 问题4: 消息延迟过高

**症状**: 发送消息后3秒以上才收到

**可能原因**:
1. **截图频率太低**: 增加capture_interval_ms
2. **ContentFetcher处理慢**: 检查CPU使用率
3. **网络延迟**: 检查本地网络

**优化方案**:
```yaml
# services/wechat_sandbox/config/settings.yaml
system:
  capture_interval_ms: 100  # 从200ms降到100ms

# 或者调整队列大小
redis:
  stream_maxlen: 10000  # 增加队列容量
```

---

### 问题5: 内存泄漏

**症状**: 长时间运行后内存持续增长

**排查步骤**:
1. 监控内存使用
```bash
# Linux/Mac
top -p $(pgrep -f wechat_sandbox)

# Windows
tasklist | findstr python
```

2. 检查Redis内存
```bash
redis-cli INFO memory | grep used_memory
```

3. 清空旧消息
```bash
# 保留最近1000条
redis-cli XTRIM wechat:messages:raw MAXLEN ~ 1000
redis-cli XTRIM wechat:messages:precise MAXLEN ~ 1000
```

---

## 测试报告模板

完成测试后，请填写以下报告：

### 测试环境

- **操作系统**: Windows 10 / Ubuntu 22.04
- **Python版本**: 3.10.12
- **Redis版本**: 7.2.3
- **微信版本**: 3.9.x
- **测试日期**: 2025-01-12

### 测试结果

| 测试项 | 状态 | 通过率 | 备注 |
|--------|------|--------|------|
| 端到端数据流 | ✅/❌ | XX% | |
| 单用户单消息 | ✅/❌ | XX% | |
| 连续发送测试 | ✅/❌ | XX% | |
| 多媒体消息 | ✅/❌ | XX% | |
| 并发连接 | ✅/❌ | XX% | |
| 异常恢复 | ✅/❌ | XX% | |
| 压力测试 | ✅/❌ | XX% | |

### 性能指标

- **平均延迟**: XX ms
- **吞吐量**: XX 条/秒
- **CPU使用率**: XX%
- **内存使用**: XX MB
- **错误次数**: XX
- **重连次数**: XX

### 发现的问题

1. **问题描述**
   - 严重程度: 高/中/低
   - 复现步骤: ...
   - 期望结果: ...
   - 实际结果: ...

### 改进建议

1. ...
2. ...

---

## 附录

### A. 快速测试命令

```bash
# 一键启动所有监控
alias monitor-all='python queue_monitor.py & python sse_client.py --verbose &'

# 清空所有队列
alias clear-queues='redis-cli DEL wechat:messages:raw wechat:messages:precise'

# 查看Redis状态
alias redis-status='redis-cli INFO | grep -E "connected_clients|used_memory|total_commands"'
```

### B. 测试数据生成

使用以下Python脚本快速生成测试消息：

```python
# generate_test_messages.py
import time
import random

test_messages = [
    "测试消息1: 纯文本",
    "测试消息2: 包含数字123",
    "测试消息3: 包含英文Hello World",
    "作业w1作业前",
    "作业w1作业中",
    "作业w1作业后",
    "工作汇报: 今天完成了XX任务",
    "状态更新: 进度80%",
]

# 需要配合微信自动化工具（如wxauto）
for msg in test_messages:
    print(f"发送: {msg}")
    # send_wechat_message("测试群", msg)
    time.sleep(random.uniform(1, 2))
```

### C. 自动化测试脚本

```bash
#!/bin/bash
# run_all_tests.sh - 运行所有测试

echo "开始微信沙盒完整测试..."
echo "========================================"

# 1. 清空队列
echo "[1/5] 清空队列..."
redis-cli DEL wechat:messages:raw wechat:messages:precise

# 2. 启动监控
echo "[2/5] 启动监控..."
python queue_monitor.py &
MONITOR_PID=$!

# 3. 启动SSE客户端
echo "[3/5] 启动SSE客户端..."
python sse_client.py --save-json --client-id auto_test &
SSE_PID=$!

# 4. 等待测试
echo "[4/5] 请在微信群中发送测试消息..."
echo "按Enter继续..."
read

# 5. 清理
echo "[5/5] 清理进程..."
kill $MONITOR_PID $SSE_PID

echo "测试完成！"
```

---

**文档版本**: v1.0
**创建日期**: 2025-01-12
**维护者**: 开发团队
