# Docker 目录说明

本目录统一管理项目所有 Docker 相关文件和容器编排配置。

## 目录结构

```
docker/
├── sandbox/                 # 微信沙盒镜像
│   ├── Dockerfile           # 基础镜像（生产环境，不带 AT-SPI）
│   └── Dockerfile.test      # 测试镜像（带 AT-SPI 支持）
├── orchestrator/            # 编排器镜像
│   └── Dockerfile           # 后端编排服务镜像
├── frontend/                # 前端镜像
│   ├── Dockerfile           # 前端 Web UI 镜像
│   └── nginx.conf           # Nginx 配置
├── scripts/                 # 容器运行脚本
│   ├── common/              # 通用脚本（不需要 AT-SPI）
│   │   ├── start_all.sh     # 启动所有服务
│   │   ├── start_sandbox.sh # 启动沙盒容器
│   │   ├── start_wechat.sh  # 启动微信应用
│   │   └── start_wechat_sandbox.bat  # Windows 启动脚本
│   └── atspi/               # AT-SPI 相关脚本（需要 AT-SPI 支持）
│       ├── restart_wechat_with_dbus.sh  # 重启微信（DBus 会话）
│       ├── run_atspi_observer.sh       # 运行 AT-SPI 观察者
│       ├── test_atspi_simple.py        # AT-SPI 简单测试
│       └── test_atspi_solution.sh      # AT-SPI 完整测试
├── compose/                 # Docker Compose 编排文件目录
│   ├── docker-compose.yml           # 默认环境（完整服务栈）
│   ├── docker-compose.dev.yml       # 开发环境（调试支持）
│   ├── docker-compose.prod.yml      # 生产环境（安全加固）
│   ├── docker-compose.multi.yml     # 多实例环境（3个沙盒实例）
│   ├── docker-compose.sandbox.test.yml  # 沙盒测试环境（AT-SPI，从根目录）
│   └── nginx/               # Nginx 配置
│       └── nginx.conf       # Nginx 反向代理配置
└── README.md                # 本文档
```

## 镜像架构

### 镜像分层策略

项目采用两层镜像策略：

#### 1. 基础镜像（Dockerfile）
- **生成镜像**: `wechat_sandbox:latest`
- **基础镜像**: `ubuntu:22.04`
- **功能特性**:
  - VNC 服务器（端口 5900）
  - noVNC Web 访问（端口 6080）
  - 微信 Linux 版本（4.1.13）
  - Python 3.10 + FastAPI
  - 双生产者架构（视觉方案）
- **分层构建**（优化缓存和构建速度）:
  - Layer 1: 基础系统工具（几乎不变）
  - Layer 2: 桌面环境（VNC + noVNC + X11 + Fluxbox）
  - Layer 3: WeChat 基础依赖
  - Layer 4: 中文字体
  - Layer 5: WeChat 应用安装
  - Layer 6: 依赖补丁（高频变动）
  - Layer 7: Python 环境和依赖
  - Layer 8: 应用代码和配置
- **使用场景**: 生产环境、默认环境、多实例部署
- **不包含**: AT-SPI 辅助功能支持

#### 2. 测试镜像（Dockerfile.test）
- **生成镜像**: `wechat_sandbox-test:latest`
- **基础镜像**: `wechat_sandbox:latest`
- **额外功能**:
  - AT-SPI 辅助功能框架支持
  - pyatspi Python 库
  - Accerciser UI 调试工具
  - Qt6 AT-SPI 桥接
  - D-Bus 会话支持
  - xdotool 和 xclip（自动化工具）
- **环境变量**:
  - `QT_ACCESSIBILITY=1`（启用 Qt 辅助功能）
  - `GNOME_ACCESSIBILITY=1`（启用 GNOME 辅助功能）
  - `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`（Qt 持续启用）
  - `TZ=Asia/Shanghai`（中国时区）
- **使用场景**: AT-SPI 测试、UI 调试、双生产者验证

### 本地镜像策略

所有编排文件优先使用本地镜像：
- `redis:7-alpine`
- `wechat_sandbox:latest`
- `wechat_sandbox-test:latest`

如果本地镜像不存在，Docker Compose 会自动构建。

## 服务说明

### 核心服务

| 服务名 | 说明 | 端口 |
|--------|------|------|
| redis | Redis 消息队列和数据缓存 | 6379 |
| ollama | LLM 模型服务（需要 GPU） | 11434 |
| orchestrator | LangGraph 工作流编排中心 | 8000 |
| frontend | React 前端 Web UI | 3000 |
| wechat-sandbox | 微信沙盒实例 | 8000/6080/5900 |
| nginx | 反向代理（生产环境） | 80/443 |

### 多实例沙箱

多实例编排文件包含 3 个微信沙盒实例，支持并发处理多个微信群：

| 实例 | FastAPI 端口 | noVNC 端口 | VNC 端口 |
|------|--------------|------------|----------|
| wechat-sandbox-1 | 8001 | 6081 | 5901 |
| wechat-sandbox-2 | 8002 | 6082 | 5902 |
| wechat-sandbox-3 | 8003 | 6083 | 5903 |

## 使用方法

### 1. 构建镜像

**构建基础镜像（必须先执行）：**
```bash
docker build -f docker/sandbox/Dockerfile -t wechat_sandbox:latest ../..
```

**构建测试镜像（可选）：**
```bash
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest ../..
```

或使用 Docker Compose 自动构建：
```bash
docker-compose -f docker/compose/docker-compose.sandbox.test.yml build
```

### 2. 启动服务

**默认环境（推荐新手）：**
```bash
docker-compose -f docker/compose/docker-compose.yml up -d
```

**开发环境（支持调试和热重载）：**
```bash
docker-compose -f docker/compose/docker-compose.yml \
               -f docker/compose/docker-compose.dev.yml up -d
```

**生产环境（安全加固）：**
```bash
export REDIS_PASSWORD=your_secure_password
export VNC_PASSWORD=your_vnc_password
docker-compose -f docker/compose/docker-compose.prod.yml up -d
```

**多实例环境（3个沙盒并行）：**
```bash
docker-compose -f docker/compose/docker-compose.multi.yml up -d
```

**沙盒测试环境（AT-SPI 测试）：**
```bash
# 方式1: 从项目根目录（推荐）
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 方式2: 从 sandbox 目录
cd docker/sandbox
docker-compose -f docker-compose.test.yml up -d
```

### 3. 访问服务

| 服务 | 访问地址 | 说明 |
|------|----------|------|
| 前端 UI | http://localhost:3000 | React Web 管理界面 |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |
| WeChat 界面 | http://localhost:6080/vnc.html | noVNC Web 界面 |
| Redis | localhost:6379 | Redis 服务 |
| Ollama | http://localhost:11434 | LLM 模型服务 |

### 4. AT-SPI 测试

**运行 AT-SPI 完整测试：**
```bash
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh
```

**运行 AT-SPI 简单测试：**
```bash
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py
```

**启动 Accerciser（UI 调试工具）：**
```bash
docker exec -it wechat_sandbox_test bash -c "accerciser &"
```

### 5. 停止服务

```bash
# 停止但保留数据
docker-compose -f docker/compose/docker-compose.yml down

# 停止并删除数据卷
docker-compose -f docker/compose/docker-compose.yml down -v
```

### 6. 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker/compose/docker-compose.yml logs -f

# 查看特定服务日志
docker-compose -f docker/compose/docker-compose.yml logs -f wechat-sandbox

# 查看最近 100 行日志
docker-compose -f docker/compose/docker-compose.yml logs --tail=100 wechat-sandbox
```

## 容器依赖关系

```
┌─────────────┐
│   nginx     │ (仅生产环境)
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
┌──────▼──────┐  ┌──────▼──────┐
│  frontend   │  │orchestrator │
└─────────────┘  └──────┬──────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐   ┌─────▼─────┐   ┌───▼────┐
    │ redis   │   │  ollama   │   │sandbox │
    └─────────┘   └───────────┘   └────────┘
```

## 配置说明

### 环境变量

生产环境支持通过环境变量配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `REDIS_PASSWORD` | default_password | Redis 密码 |
| `VNC_PASSWORD` | vnc123 | VNC 访问密码 |
| `API_URL` | http://localhost:8000 | API 地址 |
| `WS_URL` | ws://localhost:8000/ws | WebSocket 地址 |

### AT-SPI 环境变量

测试环境自动配置以下 AT-SPI 相关环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `TZ` | Asia/Shanghai | 中国标准时间 |
| `GNOME_ACCESSIBILITY` | 1 | 启用 GNOME 辅助功能 |
| `QT_ACCESSIBILITY` | 1 | 启用 Qt 辅助功能 |
| `QT_LINUX_ACCESSIBILITY_ALWAYS_ON` | 1 | Qt 持续启用辅助功能 |

### 网络配置

默认使用 `172.20.0.0/16` 子网，避免与本地网络冲突。

### 数据持久化

**默认环境和生产环境：**
- Redis 数据: Docker Volume `redis_data`
- Ollama 数据: Docker Volume `ollama_data`
- 微信沙盒媒体: `services/wechat_sandbox/media`
- 微信沙盒日志: `services/wechat_sandbox/logs`

**测试环境：**
- Redis 数据: Docker Volume `redis_data`
- 微信数据: Docker Volume `wechat_data`
- 媒体文件: `docker/sandbox/media`（或 `services/wechat_sandbox/media`）
- 日志文件: `docker/sandbox/logs`（或 `services/wechat_sandbox/logs`）

**多实例环境：**
- 每个实例有独立的媒体和日志目录：
  - `services/wechat_sandbox/media/instance{1,2,3}`
  - `services/wechat_sandbox/logs/instance{1,2,3}`

## 故障排查

### WeChat 沙盒无法启动

检查 VNC 和 Xvfb 服务状态：
```bash
docker exec -it wechat-sandbox ps aux | grep -E "Xvfb|x11vnc|fluxbox"
```

### Redis 连接失败

检查 Redis 容器状态：
```bash
docker ps | grep redis
docker logs wechat-redis
```

### Ollama GPU 不工作

检查 GPU 支持配置：
```bash
docker exec -it wechat-ollama nvidia-smi
```

### AT-SPI 功能不工作

1. 检查环境变量：
```bash
docker exec -it wechat_sandbox_test env | grep -E "QT_ACCESSIBILITY|GNOME_ACCESSIBILITY|DBUS"
```

2. 检查 AT-SPI 服务：
```bash
docker exec -it wechat_sandbox_test ps aux | grep at-spi
```

3. 运行测试脚本：
```bash
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py
```

## 注意事项

1. **GPU 支持**: Ollama 需要支持 GPU 的主机和 NVIDIA Container Toolkit
2. **特权模式**: 微信沙盒需要特权模式和 `SYS_ADMIN` 能力
3. **端口冲突**: 多实例部署时注意端口映射，避免冲突
4. **镜像构建顺序**: 必须先构建 `wechat_sandbox:latest`，再构建 `wechat_sandbox-test:latest`
5. **安全性**: 生产环境请修改默认密码并启用 SSL
6. **AT-SPI 功能**: 仅在测试镜像（`wechat_sandbox-test:latest`）中可用
7. **数据备份**: 定期备份 Redis 和 Ollama 数据卷

## 清理命令

**停止并删除容器、网络、数据卷：**
```bash
docker-compose -f docker/compose/docker-compose.yml down -v
```

**删除未使用的镜像：**
```bash
docker image prune -a
```

**删除所有未使用的资源：**
```bash
docker system prune -a --volumes
```

## 相关文档

### 技术文档
- [AT-SPI 混合方案说明](../docs/atspi_hybrid_solution.md)
- [AT-SPI 部署配置说明](../docs/atspi_deployment_config.md)
- [微信沙盒测试方案](../docs/wechat_sandbox_test_plan.md)
- [环境初始化指南](../docs/ENVIRONMENT_INIT.md)
- [环境配置说明](../docs/ENVIRONMENT_SETUP.md)

### 项目文档
- [项目架构设计文档](../多模态Agent微信群自动化项目：架构设计文档V2.md)
- [技术栈文档](../多模态Agent微信群自动化项目：技术栈文档.md)
- [微信沙盒架构文档](../services/wechat_sandbox/ARCHITECTURE.md)

### 容器监控
- 前端管理员监控界面: `http://localhost:3000/admin/sandbox`（需要管理员权限）

## 版本历史

- **2025-01-12**:
  - 删除 `Dockerfile.old`（废弃版本）
  - 删除 `docker/base/` 目录（旧的基础镜像方式，已被 `docker/sandbox/Dockerfile` 替代）
  - 添加 Dockerfile.test（AT-SPI 测试镜像）
  - 更新所有编排文件添加中文说明
  - 统一镜像策略（优先使用本地镜像）
  - 更新 Redis 版本为 `redis:7-alpine`
  - 添加容器运行脚本到 `docker/scripts/`
