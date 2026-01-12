# AT-SPI 部署配置说明

## 概述

本文档说明AT-SPI方案在容器编排中的配置要求，包括时区设置和D-Bus总线配置。

## 配置目标

1. **时区统一**：所有容器使用中国标准时间（CST, UTC+8）
2. **D-Bus会话统一**：AT-SPI服务、微信应用和其他辅助功能工具使用同一个D-Bus会话
3. **环境变量配置**：确保AT-SPI功能正常工作

---

## 1. Dockerfile 配置

### 文件位置
- `docker/sandbox/Dockerfile.test` (测试环境)
- `docker/sandbox/Dockerfile` (生产环境)

### 关键配置

#### 时区设置
```dockerfile
# 设置时区为中国标准时间
ENV TZ=Asia/Shanghai

# 安装时区数据包并设置时区链接
RUN apt-get update && apt-get install -y --fix-missing \
    ... \
    tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -rf /var/lib/apt/lists/*
```

#### AT-SPI 环境变量
```dockerfile
# 开启 Qt6 AT-SPI 桥接功能
ENV QT_ACCESSIBILITY=1

# 设置辅助功能环境变量
ENV GNOME_ACCESSIBILITY=1
ENV QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
```

---

## 2. Docker Compose 配置

### 环境变量配置

所有微信沙盒服务都需要添加以下环境变量：

```yaml
environment:
  - DISPLAY=:99
  - REDIS_HOST=redis
  - REDIS_PORT=6379
  - REDIS_DB=0
  - VNC_PASSWORD=vnc123
  # 时区设置（关键）
  - TZ=Asia/Shanghai
  # AT-SPI辅助功能环境变量（关键）
  - GNOME_ACCESSIBILITY=1
  - QT_ACCESSIBILITY=1
  - QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
```

### 已更新的文件

✅ `docker/compose/docker-compose.yml`
✅ `docker/compose/docker-compose.dev.yml`
✅ `docker/compose/docker-compose.prod.yml`
✅ `docker/compose/docker-compose.multi.yml`
✅ `docker/compose/docker-compose.sandbox.test.yml`

---

## 3. 启动脚本配置

### 文件位置
`docker/scripts/start_all.sh`

### D-Bus 会话管理

#### 启动 D-Bus 会话
```bash
echo "Starting DBus session..."
# 启动 D-Bus 会话并导出地址，所有AT-SPI应用都需要使用同一个会话
eval $(dbus-launch --sh-syntax)
export DBUS_SESSION_BUS_ADDRESS
echo "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"

# 将 D-Bus 地址保存到文件，供后续进程使用
echo "$DBUS_SESSION_BUS_ADDRESS" > /tmp/dbus_session_address
```

#### 确保 AT-SPI 服务使用统一会话
```bash
echo "[5/7] Starting AT-SPI service..."
# 确保使用统一的 D-Bus 会话
if [ -f /tmp/dbus_session_address ]; then
    export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/dbus_session_address)
    echo "Using D-Bus session: $DBUS_SESSION_BUS_ADDRESS"
fi

/usr/libexec/at-spi-bus-launcher --launch-immediately > /tmp/atspi.log 2>&1 &
```

#### 确保微信使用统一会话
```bash
echo "[7/7] Starting WeChat application with AT-SPI enabled..."
# 确保微信使用统一的 D-Bus 会话
if [ -f /tmp/dbus_session_address ]; then
    export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/dbus_session_address)
fi

QT_ACCESSIBILITY=1 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 /opt/wechat/wechat > /tmp/wechat.log 2>&1 &
```

---

## 4. 配置验证

### 验证时区

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 查看时区
date
# 应显示类似: Mon Jan 12 20:29:27 CST 2026

# 查看时区文件
ls -la /etc/localtime
# 应显示: /etc/localtime -> /usr/share/zoneinfo/Asia/Shanghai
```

### 验证 D-Bus 会话

```bash
# 进入容器
docker exec -it wechat_sandbox_test bash

# 查看 D-Bus 地址
echo $DBUS_SESSION_BUS_ADDRESS
# 应显示类似: unix:path=/run/user/0/bus

# 查看保存的地址
cat /tmp/dbus_session_address
# 应与上面一致
```

### 验证 AT-SPI 注册

```bash
# 使用 pyatspi 测试
python3 -c "
import pyatspi
desktop = pyatspi.Registry.getDesktop(0)
print(f'找到 {desktop.childCount} 个应用')
for i in range(desktop.childCount):
    app = desktop.getChildAtIndex(i)
    print(f'  [{i}] {app.name}')
"

# 应该能看到 wechat 应用
```

---

## 5. 关键技术点

### 为什么需要统一的 D-Bus 会话？

AT-SPI (Assistive Technology Service Provider Interface) 基于 D-Bus 通信：

1. **AT-SPI Registry** 运行在一个 D-Bus 会话中
2. **辅助功能应用**（如微信）必须注册到**同一个** D-Bus 会话
3. **AT-SPI 客户端**（如 Accerciser、pyatspi）也必须连接到**同一个** D-Bus 会话

如果不在同一个会话：
- ❌ 微信无法注册到 AT-SPI
- ❌ pyatspi 无法发现微信
- ❌ 消息监听失败

### 为什么需要设置时区？

1. **消息时间戳准确性**：消息提取的时间戳需要使用本地时区
2. **日志时间戳**：调试和监控需要准确的时间
3. **数据一致性**：确保所有组件使用相同的时区

### 环境变量说明

| 变量 | 作用 | 必需 |
|------|------|------|
| `TZ=Asia/Shanghai` | 设置容器时区为中国标准时间 | ✅ |
| `GNOME_ACCESSIBILITY=1` | 启用 GNOME 辅助功能框架 | ✅ |
| `QT_ACCESSIBILITY=1` | 启用 Qt 应用辅助功能支持 | ✅ |
| `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1` | 强制 Qt 应用始终开启辅助功能 | ✅ |
| `DBUS_SESSION_BUS_ADDRESS` | D-Bus 会话地址（自动生成） | ✅ |

---

## 6. 启动顺序

正确的启动顺序至关重要：

```
1. Xvfb (虚拟显示)
2. Fluxbox (窗口管理器)
3. x11vnc (VNC服务器)
4. noVNC (Web VNC客户端)
5. dbus-launch (启动 D-Bus 会话) ← 关键步骤
6. AT-SPI service (辅助功能服务) ← 必须在应用之前
7. FastAPI (等待 Redis 就绪)
8. WeChat (使用同一 D-Bus 会话) ← 必须注册到 AT-SPI
9. Accerciser (调试工具，可选)
```

**关键点**：
- D-Bus 会话必须最先启动
- AT-SPI 服务必须在微信之前启动
- 所有应用必须使用同一个 D-Bus 会话地址

---

## 7. 故障排查

### 问题1：时间戳不正确

**症状**：消息时间戳比实际时间少8小时

**解决方案**：
```bash
# 检查时区设置
docker exec wechat_sandbox_test date
docker exec wechat_sandbox_test ls -la /etc/localtime

# 手动修复
docker exec wechat_sandbox_test ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
```

### 问题2：pyatspi 找不到微信

**症状**：`未找到微信应用` 或 `未找到微信窗口`

**解决方案**：
```bash
# 检查 D-Bus 会话
docker exec wechat_sandbox_test sh -c 'echo $DBUS_SESSION_BUS_ADDRESS'

# 检查 AT-SPI 服务
docker exec wechat_sandbox_test ps aux | grep at-spi-bus-launcher

# 检查微信进程环境变量
docker exec wechat_sandbox_test cat /proc/$(pgrep wechat)/environ | tr '\0' '\n' | grep DBUS
```

### 问题3：Accerciser 看不到微信

**症状**：Accerciser 中没有微信节点

**解决方案**：
1. 确保使用 `start_all.sh` 启动（不是手动启动）
2. 确保 D-Bus 会话统一
3. 重启容器：
   ```bash
   docker-compose -f docker/compose/docker-compose.sandbox.test.yml down
   docker-compose -f docker/compose/docker-compose.sandbox.test.yml up --build
   ```

---

## 8. 生产部署建议

### 1. 使用 Docker Compose

推荐使用 docker-compose 而不是手动启动：

```bash
cd docker/compose
docker-compose -f docker-compose.sandbox.test.yml up --build
```

### 2. 健康检查

确保 Redis 健康检查正常：

```yaml
redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5

wechat_sandbox:
  depends_on:
    redis:
      condition: service_healthy
```

### 3. 日志监控

监控关键日志：

```bash
# AT-SPI 日志
docker exec wechat_sandbox_test tail -f /tmp/atspi.log

# 微信日志
docker exec wechat_sandbox_test tail -f /tmp/wechat.log

# FastAPI 日志
docker exec wechat_sandbox_test tail -f /tmp/fastapi.log
```

---

## 9. 配置文件清单

### 必需的配置文件

✅ `docker/sandbox/Dockerfile.test` - 包含时区和AT-SPI环境变量
✅ `docker/sandbox/Dockerfile` - 生产环境Dockerfile
✅ `docker/scripts/start_all.sh` - D-Bus会话管理
✅ `docker/compose/docker-compose.sandbox.test.yml` - 测试环境编排
✅ `docker/compose/docker-compose.yml` - 默认编排
✅ `docker/compose/docker-compose.dev.yml` - 开发环境
✅ `docker/compose/docker-compose.prod.yml` - 生产环境
✅ `docker/compose/docker-compose.multi.yml` - 多实例环境

---

## 10. 总结

### 关键配置点

1. ✅ **时区设置**：`TZ=Asia/Shanghai` + `/etc/localtime` 链接
2. ✅ **D-Bus 会话**：统一使用 `dbus-launch` 生成的会话
3. ✅ **环境变量**：`GNOME_ACCESSIBILITY` + `QT_ACCESSIBILITY`
4. ✅ **启动顺序**：D-Bus → AT-SPI → WeChat

### 验证清单

- [ ] 容器时区显示 CST
- [ ] D-Bus 会话地址一致
- [ ] AT-SPI 服务运行正常
- [ ] 微信注册到 AT-SPI
- [ ] Accerciser 可以看到微信
- [ ] pyatspi 可以检测微信
- [ ] 消息监听正常工作

---

**配置完成时间**：2025-01-12
**配置状态**：✅ 完成并验证
**维护者**：Claude Code
