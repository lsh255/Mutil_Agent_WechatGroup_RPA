# 微信沙盒测试快速指南

## 一、测试前准备（5分钟）

### 1. 启动Redis
```bash
# Windows
redis-server

# Linux/Mac
redis-server
```

验证连接：
```bash
redis-cli ping
# 应返回: PONG
```

### 2. 启动微信沙盒服务
```bash
cd services/wechat_sandbox
python main.py
```

### 3. 准备测试环境
- ✅ 微信PC客户端已登录
- ✅ 测试群聊已打开（至少3个成员）
- ✅ 配置文件中的目标群名正确

检查配置：
```bash
cat services/wechat_sandbox/config/settings.yaml | grep target_group_name
```

---

## 二、快速测试（3种方式）

### 方式1️⃣：一键测试脚本（推荐）

**Windows**:
```bash
cd tests/wechat_sandbox
quick_test.bat basic
```

**Linux/Mac**:
```bash
cd tests/wechat_sandbox
./quick_test.sh basic
```

这个脚本会自动：
- ✅ 检查Redis连接
- ✅ 检查服务状态
- ✅ 启动SSE客户端
- ✅ 保存测试结果

---

### 方式2️⃣：手动基础测试

**步骤1**: 启动SSE客户端（新终端）
```bash
cd tests/wechat_sandbox
python sse_client.py --verbose --save-json
```

**步骤2**: 在微信群发送测试消息
- 文本: "测试消息1"
- 图片: 发送一张截图
- 视频: 发送一个小视频

**步骤3**: 观察客户端输出
```
✅ 连接成功
📨 [消息 #1] 14:30:22
ID:         msg_xxx
类型:       text
文本内容:   测试消息1
```

---

### 方式3️⃣：监控队列状态

**启动监控**:
```bash
cd tests/wechat_sandbox
python queue_monitor.py
```

**实时显示**:
```
📥 原始队列:            5 条消息
📤 精确队列:            5 条消息
📊 处理进度:        100% (5/5)
```

---

## 三、测试场景说明

### 场景A: 端到端测试（5分钟）

**目标**: 验证完整数据流

**命令**:
```bash
# 终端1: 队列监控
python queue_monitor.py

# 终端2: SSE客户端
python sse_client.py --verbose
```

**操作**:
1. 发送3条文本消息
2. 发送1张图片
3. 发送1个视频

**验证**:
- ✅ 原始队列消息数 ≥ 5
- ✅ 精确队列消息数 = 5
- ✅ SSE收到所有5条消息
- ✅ 延迟 < 3秒

---

### 场景B: 性能测试（10分钟）

**目标**: 测试延迟和吞吐量

**命令**:
```bash
python sse_performance_test.py --duration 60 --benchmark
```

**操作**:
在60秒内连续发送50条消息

**预期结果**:
```
平均延迟:   <1000ms
吞吐量:     >1条/秒
错误次数:   0
重连次数:   0
```

---

### 场景C: 并发测试（5分钟）

**目标**: 测试多客户端连接

**命令**:
```bash
# 启动3个并发客户端
python sse_client.py --client-id client1 --save-json &
python sse_client.py --client-id client2 --save-json &
python sse_client.py --client-id client3 --save-json &
```

**操作**:
发送10条消息

**验证**:
- ✅ 每个客户端都收到10条消息
- ✅ 消息内容一致
- ✅ 无连接中断

---

## 四、故障快速排查

### ❌ 问题1: SSE无法连接

**症状**: `❌ 连接失败: HTTP 502`

**解决**:
```bash
# 检查服务是否启动
curl http://localhost:8000/api/stream/messages

# 查看服务日志
cd services/wechat_sandbox
tail -f logs/wechat_sandbox.log
```

---

### ❌ 问题2: 接收不到消息

**症状**: SSE已连接，但发送消息后无输出

**解决**:
```bash
# 1. 检查原始队列
redis-cli XLEN wechat:messages:raw

# 2. 如果为0，说明Observer未检测到
#    - 检查微信窗口是否在前台
#    - 检查ROI配置是否正确
#    - 查看Observer日志

# 3. 如果有数据，检查精确队列
redis-cli XLEN wechat:messages:precise

# 4. 如果精确队列为0，说明ContentFetcher未处理
#    - 查看ContentFetcher日志
#    - 检查Redis锁
redis-cli KEYS "wechat:lock:*"
```

---

### ❌ 问题3: 延迟过高

**症状**: 发送消息后3秒以上才收到

**解决**:
```yaml
# 编辑配置文件
vim services/wechat_sandbox/config/settings.yaml

# 调整截图频率
system:
  capture_interval_ms: 100  # 从200降到100

# 重启服务
cd services/wechat_sandbox
python main.py
```

---

## 五、测试结果检查

### 查看保存的消息

```bash
cd tests/wechat_sandbox/test_results
ls messages_*.json
```

使用jq查看（可选）:
```bash
jq '.[] | {id, type, content: .precise_content}' messages_default_*.json
```

### 导出队列数据

```bash
python queue_monitor.py --export --output my_test.json
```

### 查看性能报告

性能测试后会自动生成报告，包含：
- 平均延迟
- 吞吐量
- 延迟分布
- 性能评级

---

## 六、完整测试流程（推荐新用户）

### 第1步：环境检查（2分钟）
```bash
# 1. 检查Redis
redis-cli ping

# 2. 检查服务
curl http://localhost:8000/api/health

# 3. 运行快速测试
./quick_test.sh basic
```

### 第2步：基础功能测试（5分钟）
```bash
# 启动SSE客户端
python sse_client.py --verbose

# 发送测试消息:
# - 文本: "Hello"
# - 图片: 一张截图
# - 视频: 一个小视频
```

### 第3步：队列验证（3分钟）
```bash
# 启动监控
python queue_monitor.py

# 发送5条消息，观察队列变化
```

### 第4步：性能测试（10分钟）
```bash
# 运行性能测试
python sse_performance_test.py --duration 60 --benchmark

# 在测试期间持续发送消息
```

### 第5步：查看结果（2分钟）
```bash
# 查看保存的消息
ls test_results/messages_*.json

# 分析队列数据
python queue_monitor.py --analyze
```

---

## 七、常用命令速查

```bash
# 启动测试
./quick_test.sh basic              # 基础测试
./quick_test.sh full               # 完整测试
./quick_test.sh performance        # 性能测试

# 监控工具
python queue_monitor.py            # 实时监控
python queue_monitor.py --analyze  # 分析模式
python queue_monitor.py --export   # 导出数据

# SSE客户端
python sse_client.py               # 基础监听
python sse_client.py -v            # 详细输出
python sse_client.py --save-json   # 保存消息

# 性能测试
python sse_performance_test.py                     # 基础测试
python sse_performance_test.py --duration 60       # 测试60秒
python sse_performance_test.py --benchmark         # 基准测试

# Redis操作
redis-cli XLEN wechat:messages:raw                 # 原始队列长度
redis-cli XLEN wechat:messages:precise             # 精确队列长度
redis-cli DEL wechat:messages:raw                  # 清空原始队列
redis-cli KEYS "wechat:lock:*"                     # 查看所有锁
```

---

## 八、测试检查清单

完成测试后，请确认：

- [ ] ✅ SSE客户端成功连接
- [ ] ✅ 发送文本消息能接收
- [ ] ✅ 发送图片能接收
- [ ] ✅ 发送视频能接收
- [ ] ✅ 原始队列和精确队列长度一致
- [ ] ✅ 消息延迟 < 3秒
- [ ] ✅ 无消息丢失
- [ ] ✅ 无重复消息
- [ ] ✅ 性能评级 ≥ B

全部通过？🎉 恭喜，系统运行正常！

有问题？查看 [README.md](README.md) 获取详细文档

---

**需要帮助？**
- 详细测试方案: [wechat_sandbox_test_plan.md](../../docs/wechat_sandbox_test_plan.md)
- 完整使用文档: [README.md](README.md)
- 问题反馈: 提交Issue到项目仓库

---

**最后更新**: 2025-01-12
**文档版本**: v1.0
