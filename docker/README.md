# Docker 目录说明

本目录统一管理项目所有 Docker 相关文件和容器编排配置。

## 目录结构

```
docker/
├── base/                    # 基础镜像层
│   └── Dockerfile           # 分层基础镜像（9层策略）
├── sandbox/                 # 微信沙箱镜像
│   └── Dockerfile           # 沙箱服务镜像（基于 base 镜像）
├── orchestrator/            # 编排器镜像
│   └── Dockerfile           # 后端编排服务镜像
├── frontend/                # 前端镜像
│   ├── Dockerfile           # 前端 Web UI 镜像
│   └── nginx.conf           # Nginx 配置
├── scripts/                 # 启动脚本
│   └── start_wechat.sh      # 微信启动脚本
├── compose/                 # 编排文件目录
│   ├── docker-compose.yml           # 完整编排（单实例）
│   ├── docker-compose.dev.yml       # 开发环境编排
│   ├── docker-compose.prod.yml      # 生产环境编排
│   ├── docker-compose.multi.yml     # 多实例沙箱编排（3个实例）
│   ├── nginx/              # Nginx 配置
│   │   └── nginx.conf      # Nginx 反向代理配置
│   └── sandbox/            # 沙箱数据卷挂载目录
│       ├── instance1/      # 实例1媒体文件
│       ├── instance2/      # 实例2媒体文件
│       ├── instance3/      # 实例3媒体文件
│       └── logs/           # 日志目录
│           ├── instance1/
│           ├── instance2/
│           └── instance3/
└── README.md                # 本文档
```

## 分层 Dockerfile 策略

基础镜像采用 9 层分层策略，优化构建效率和缓存利用率：

1. **基础系统层**（几乎不变）：wget, curl, ca-certificates
2. **桌面环境层**（低频变动）：VNC + noVNC + X11 + Fluxbox
3. **WeChat 基础依赖层**（偶尔变动）：GUI 库 + 多媒体库
4. **字体层**（低频变动）：中文字体支持
5. **WeChat 应用层**（偶尔变动）：WeChat Linux 安装
6. **依赖补丁层**（高频变动）：方便添加缺失依赖
7. **Python 环境层**（可选）：Python 3 + pip
8. **配置层**（经常变动）：启动脚本和配置文件

## 服务说明

### 核心服务

| 服务名 | 说明 | 端口 |
|--------|------|------|
| redis | Redis 消息队列和数据缓存 | 6379 |
| ollama | LLM 模型服务 | 11434 |
| orchestrator | 工作流编排中心 | 8000 |
| frontend | 前端 Web UI | 3000 |
| wechat-sandbox | 微信沙箱实例 | 8000/6080/5900 |
| nginx | 反向代理 | 80/443 |

### 多实例沙箱

多实例编排文件包含 3 个微信沙箱实例，支持并发处理多个微信群：

| 实例 | FastAPI 端口 | noVNC 端口 | VNC 端口 |
|------|--------------|------------|----------|
| wechat-sandbox-1 | 8001 | 6081 | 5901 |
| wechat-sandbox-2 | 8002 | 6082 | 5902 |
| wechat-sandbox-3 | 8003 | 6083 | 5903 |

## 使用方法

### 1. 构建基础镜像

```bash
cd docker/base
docker build -t wechat-base:latest .
```

### 2. 启动完整服务栈

**单实例部署（推荐测试环境）：**
```bash
cd docker/compose
docker-compose -f docker-compose.yml up -d
```

**多实例部署（生产环境）：**
```bash
cd docker/compose
docker-compose -f docker-compose.multi.yml up -d
```

**开发环境（支持调试）：**
```bash
cd docker/compose
docker-compose -f docker-compose.dev.yml up -d
```

**生产环境（带安全配置）：**
```bash
cd docker/compose
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 访问服务

| 服务 | 访问地址 | 说明 |
|------|----------|------|
| 前端 UI | http://localhost:3000 | Web 管理界面 |
| API 文档 | http://localhost:8000/docs | Swagger API 文档 |
| WeChat 界面 | http://localhost:6080/vnc.html | noVNC Web 界面 |
| Redis | localhost:6379 | Redis 服务 |
| Ollama | http://localhost:11434 | LLM 模型服务 |

### 4. 停止服务

```bash
cd docker/compose
docker-compose -f docker-compose.yml down
```

### 5. 查看日志

```bash
docker-compose -f docker-compose.yml logs -f [service_name]
```

## 容器依赖关系

```
┌─────────────┐
│   nginx     │
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
| REDIS_PASSWORD | default_password | Redis 密码 |
| VNC_PASSWORD | vnc123 | VNC 访问密码 |
| API_URL | http://localhost:8000 | API 地址 |
| WS_URL | ws://localhost:8000/ws | WebSocket 地址 |

### 网络配置

默认使用 `172.20.0.0/16` 子网，避免与本地网络冲突。

## 故障排查

### WeChat 沙箱无法启动

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

## 注意事项

1. **GPU 支持**：Ollama 需要支持 GPU 的主机和 NVIDIA Container Toolkit
2. **特权模式**：微信沙箱需要特权模式和 SYS_ADMIN 能力
3. **端口冲突**：多实例部署时注意端口映射，避免冲突
4. **数据持久化**：使用 Docker Volume 持久化 Redis 和 Ollama 数据
5. **安全性**：生产环境请修改默认密码并启用 SSL

## 清理命令

删除所有容器和网络：
```bash
docker-compose -f docker-compose.yml down -v
```

删除未使用的镜像：
```bash
docker image prune -a
```

## 相关文档

- [项目架构文档](../../多模态Agent微信群自动化项目：架构设计文档V2.md)
- [技术栈文档](../../多模态Agent微信群自动化项目：技术栈文档.md)
- [微信沙箱架构文档](../../services/wechat_sandbox/ARCHITECTURE.md)
