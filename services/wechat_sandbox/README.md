# WeChat 沙箱项目

## 概述

这是一个基于 Linux 微信的沙盒容器，用于本地测试和开发微信自动化功能。项目采用 Docker 容器化部署，支持多实例部署，并内置双生产者架构实时提取和转发群聊消息。

## 前置要求

1. Docker 已安装并运行
2. Linux 微信安装包已放置在项目 build 目录：`build/WeChatLinux_x86_64.deb`

## 目录结构说明

### 核心 Dockerfile

| 文件 | 用途 | 基础镜像 |
|------|------|----------|
| [docker/sandbox/Dockerfile](../../docker/sandbox/Dockerfile) | 生产环境基础镜像 | ubuntu:22.04 |
| [docker/sandbox/Dockerfile.test](../../docker/sandbox/Dockerfile.test) | 测试环境镜像（添加 FastAPI） | wechat_sandbox:latest |

### Docker Compose 编排文件

| 文件 | 用途 | 环境 |
|------|------|------|
| [docker/compose/docker-compose.sandbox.test.yml](../../docker/compose/docker-compose.sandbox.test.yml) | 测试单实例部署（含 FastAPI） | 测试 |

### 应用代码

| 目录/文件 | 用途 |
|-----------|------|
| [main.py](./main.py) | 主启动脚本 |
| [backup_start.py](./backup_start.py) | 备用启动脚本 |
| [api/](./api/) | API 模块（FastAPI 应用、路由、配置管理） |
| [core/](./core/) | 核心业务逻辑模块（消息监控、提取、分类、队列管理） |
| [core/detector/](./core/detector/) | 变化检测模块（dHash、气泡检测、屏幕变化） |
| [core/extractor/](./core/extractor/) | 内容提取模块（文本提取、媒体截图） |
| [core/producer/](./core/producer/) | 生产者模块（Observer、ContentFetcher、AgentConsumer） |
| [core/queue/](./core/queue/) | Redis Stream 队列管理 |
| [core/classifier/](./core/classifier/) | 消息类型分类器（文本/图片/视频/链接） |
| [core/platform/](./core/platform/) | 平台适配模块（跨平台支持） |
| [utils/](./utils/) | 工具类（配置、日志） |
| [tests/](./tests/) | 测试代码 |
| [services/](./services/) | 服务模块 |

### 启动脚本

| 文件 | 用途 |
|------|------|
| [docker/scripts/start_sandbox.sh](../../docker/scripts/start_sandbox.sh) | 通用启动脚本 |
| [docker/scripts/start_wechat.sh](../../docker/scripts/start_wechat.sh) | WeChat 沙箱启动脚本（Xvfb、Fluxbox、noVNC、WeChat） |
| [docker/scripts/start_wechat_sandbox.bat](../../docker/scripts/start_wechat_sandbox.bat) | Windows 启动脚本 |

### 配置文件

| 文件 | 用途 |
|------|------|
| [config.yaml](./config.yaml) | 配置文件（微信、监控、ROI、Redis） |
| [config.production.yaml](./config.production.yaml) | 生产环境配置文件 |
| [requirements.txt](./requirements.txt) | Python 依赖 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构文档 |
| [BUSINESS_LOGIC_TEST.md](./BUSINESS_LOGIC_TEST.md) | 业务逻辑测试指南 |
| [QUICKSTART.md](./QUICKSTART.md) | 快速开始 |

### 数据目录

| 目录 | 用途 |
|------|------|
| [docker/sandbox/media/](../../docker/sandbox/media/) | 媒体文件目录（自动创建） |
| [docker/sandbox/logs/](../../docker/sandbox/logs/) | 日志文件目录（自动创建） |

### 归档目录

[archive/](./archive/) - 包含过时的配置文件

## 快速开始

### 构建生产环境镜像
```bash
docker build -f docker/sandbox/Dockerfile -t wechat_sandbox:latest .
```

### 启动生产环境（单实例）
```bash
docker run -d --name wechat_sandbox \
    --privileged \
    -p 6080:6080 \
    -p 5900:5900 \
    -v docker/sandbox/media:/app/media \
    -v docker/sandbox/logs:/app/logs \
    -e DISPLAY=:99 \
    wechat_sandbox:latest
```

### 测试环境（使用 Docker Compose）
```bash
cd docker/compose
docker-compose -f docker-compose.sandbox.test.yml up -d
```

## 访问地址

- **noVNC Web 界面**: http://localhost:6080/vnc.html
- **VNC**: localhost:5900
- **FastAPI 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **服务状态**: http://localhost:8000/api/status
- **SSE 消息流**: http://localhost:8000/api/stream
- **配置管理**: http://localhost:8000/api/config
- **实例管理**: http://localhost:8000/api/instance/start, http://localhost:8000/api/instance/stop
- **Redis**: localhost:6379

## 端口映射

| 端口 | 服务 | 说明 |
|------|------|------|
| 6080 | noVNC | Web 界面 |
| 5900 | VNC | VNC 客户端 |
| 8000 | FastAPI | API 服务 |
| 6379 | Redis | 数据库 |

## 访问微信界面

### 方式一：通过浏览器访问（推荐）

1. 打开浏览器访问：`http://localhost:6080/vnc.html`
2. 在连接对话框中输入密码：`wechat123`
3. 等待微信界面加载完成

### 方式二：通过 VNC 客户端访问

1. 使用 VNC 客户端（如 RealVNC、TightVNC）连接：
   - 主机：`localhost`
   - 端口：`5900`
   - 密码：`wechat123`

## 常用命令

### 停止容器

```bash
docker stop wechat_sandbox
docker rm wechat_sandbox
```

### 重启容器

```bash
docker restart wechat_sandbox
```

### 查看容器日志

```bash
docker logs -f wechat_sandbox
```

### 进入容器终端

```bash
docker exec -it wechat_sandbox bash
```

### 查看容器状态

```bash
docker ps | grep wechat_sandbox
```

## 功能特性

### 1. 虚拟显示环境
- 使用 Xvfb 提供 1920x1080 分辨率的虚拟显示器
- 配置 Fluxbox 窗口管理器

### 2. 远程访问
- **noVNC**：通过浏览器访问（端口 6080）
- **x11vnc**：通过 VNC 客户端访问（端口 5900）

### 3. 双生产者架构
- **Producer1 Observer**：监控微信群聊消息气泡
- **Producer2 ContentFetcher**：提取消息精确内容（文本、图片、视频）
- **AgentConsumer**：消费者代理，消费精确消息队列
- **Redis Stream**：消息队列管理（原始消息队列、精确消息队列）
- **SSE 推送**：实时推送消息到外部系统
- **跨平台支持**：PlatformAdapter 抽象基类，支持 Linux 和 Windows

### 4. 统一 API 服务
- **FastAPI 应用**：统一的 API 入口点
- **健康检查端点**：服务健康状态监控
- **配置管理端点**：动态配置管理
- **实例管理端点**：启动/停止服务实例
- **SSE 流端点**：实时消息流推送

### 5. 数据持久化
- 微信用户数据存储在 Docker volume 中
- 媒体文件映射到本地 `docker/sandbox/media/` 目录
- 日志文件映射到本地 `docker/sandbox/logs/` 目录

### 6. 启动脚本
- **main.py**：主启动脚本，完整功能启动
- **backup_start.py**：备用启动脚本，仅启动 FastAPI 服务
- **docker/scripts/start_sandbox.sh**：Shell 启动脚本，Linux 环境使用
- **docker/scripts/start_wechat.sh**：微信沙箱启动脚本，启动 Xvfb、Fluxbox、noVNC、WeChat
- **docker/scripts/start_wechat_sandbox.bat**：Windows 启动脚本，Windows 环境使用

## 故障排查

### 问题 1：容器无法启动

检查 Docker 日志：
```bash
docker logs wechat_sandbox
```

### 问题 2：无法通过浏览器访问

1. 确认容器正在运行：`docker ps`
2. 确认端口未被占用：`netstat -ano | findstr "6080"`
3. 等待 30-60 秒让服务完全启动

### 问题 3：微信界面显示异常

重新启动容器：
```bash
docker restart wechat_sandbox
```

### 问题 4：构建失败

确保 `WeChatLinux_x86_64.deb` 文件存在于项目 build 目录：
```bash
ls build/WeChatLinux_x86_64.deb
```

### 问题 5：无法连接到服务器

1. 检查容器是否正在运行
2. 检查端口映射是否正确
3. 查看 [docker/scripts/start_wechat.sh](../../docker/scripts/start_wechat.sh) 脚本日志

### 问题 6：API 无法访问

1. 确认 FastAPI 服务是否启动：`docker logs -f wechat_sandbox`
2. 检查 API 路由前缀是否正确（/api/）
3. 尝试使用备用启动脚本：`docker exec -it wechat_sandbox python backup_start.py`

### 问题 7：Redis 连接失败

1. 确认 Redis 容器已启动：`docker ps | grep redis`
2. 检查健康状态：`docker exec <redis_container> redis-cli ping`
3. 确认网络配置正确

## 安全说明

- VNC 密码默认为 `wechat123`，生产环境请修改
- 容器以特权模式运行，仅用于开发测试
- 不要将此容器暴露到公网

## 开发说明

### 自定义分辨率

修改 [docker/scripts/start_wechat.sh](../../docker/scripts/start_wechat.sh) 中的 Xvfb 启动参数：
```bash
Xvfb :99 -screen 0 1920x1080x24 &
```
改为：
```bash
Xvfb :99 -screen 0 2560x1440x24 &
```

### 修改 VNC 密码

修改 [docker/scripts/start_wechat.sh](../../docker/scripts/start_wechat.sh) 中的密码：
```bash
echo "wechat123" | vncpasswd -f > /root/.vnc/passwd
```

### 自定义字体

在 [docker/sandbox/Dockerfile](../../docker/sandbox/Dockerfile) 中添加中文字体：
```dockerfile
RUN apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei
```

## 技术栈

- **基础镜像**：Ubuntu 22.04
- **显示服务**：Xvfb + Fluxbox
- **远程访问**：noVNC + x11vnc
- **应用**：Linux 微信 (WeChatLinux_x86_64.deb)
- **API 框架**：FastAPI + uvicorn
- **消息队列**：Redis Stream
- **屏幕截图**：mss（兼容 Docker Xvfb）
- **图像处理**：OpenCV + PIL
- **跨平台支持**：PlatformAdapter 抽象基类
- **异步通信**：httpx.AsyncClient (SSE 消费)

## 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构详细说明
- [BUSINESS_LOGIC_TEST.md](./BUSINESS_LOGIC_TEST.md) - 业务逻辑测试指南
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始
- [agent.md](../../agent.md) - 项目整体架构说明
- [claude.md](../../claude.md) - 开发规范和约定
