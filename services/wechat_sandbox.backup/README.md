# WeChat 沙箱项目

## 概述

这是一个基于 Linux 微信的沙盒容器，用于本地测试和开发微信自动化功能。项目采用 Docker 容器化部署，支持多实例部署，并内置双生产者架构实时提取和转发群聊消息。

## 前置要求

1. Docker 已安装并运行
2. Linux 微信安装包已放置在项目根目录：`WeChatLinux_x86_64.deb`

## 目录结构说明

### 核心 Dockerfile

| 文件 | 用途 | 基础镜像 |
|------|------|----------|
| [Dockerfile](./Dockerfile) | 生产环境基础镜像 | ubuntu:22.04 |
| [Dockerfile.test](./Dockerfile.test) | 测试环境镜像（添加 FastAPI） | wechat_sandbox:latest |

### Docker Compose 编排文件

| 文件 | 用途 | 环境 |
|------|------|------|
| [docker-compose.yml](./docker-compose.yml) | 生产单实例部署 | 生产 |
| [docker-compose.multi.yml](./docker-compose.multi.yml) | 生产多实例部署（3 个实例） | 生产 |
| [docker-compose.test.yml](./docker-compose.test.yml) | 测试单实例部署（含 FastAPI） | 测试 |

### 应用代码

| 目录/文件 | 用途 |
|-----------|------|
| [app/](./app/) | FastAPI 应用代码 |
| [producer_service/](./producer_service/) | 生产者服务代码 |
| [utils/](./utils/) | 工具类 |
| [tests/](./tests/) | 测试代码 |

### 启动脚本

| 文件 | 用途 |
|------|------|
| [start_wechat.sh](./start_wechat.sh) | WeChat 沙箱启动脚本 |
| [start.sh](./start.sh) | 服务启动脚本 |

### 配置文件

| 文件 | 用途 |
|------|------|
| [requirements.txt](./requirements.txt) | Python 依赖 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 架构文档 |
| [BUSINESS_LOGIC_TEST.md](./BUSINESS_LOGIC_TEST.md) | 业务逻辑测试指南 |
| [QUICKSTART_TEST.md](./QUICKSTART_TEST.md) | 测试环境快速开始 |

### 数据目录

| 目录 | 用途 |
|------|------|
| [media/](./media/) | 媒体文件目录（自动创建） |
| [logs/](./logs/) | 日志文件目录（自动创建） |

### 归档目录

[archive/](./archive/) - 包含过时的配置文件

## 快速开始

### 生产环境（单实例）
```bash
docker-compose up -d
```

### 生产环境（多实例）
```bash
docker-compose -f docker-compose.multi.yml up -d
```

### 测试环境
```bash
docker-compose -f docker-compose.test.yml up -d
```

## 访问地址

- **noVNC Web 界面**: http://localhost:6080
- **VNC**: localhost:5900
- **FastAPI 文档**: http://localhost:8000/docs
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
docker-compose down
```

### 重启容器

```bash
docker-compose restart
```

### 查看容器日志

```bash
docker-compose logs -f
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
- **Redis Stream**：消息队列管理
- **SSE 推送**：实时推送消息到外部系统

### 4. 数据持久化
- 微信用户数据存储在 Docker volume 中
- 媒体文件映射到本地 `media/` 目录
- 日志文件映射到本地 `logs/` 目录

## 故障排查

### 问题 1：容器无法启动

检查 Docker 日志：
```bash
docker-compose logs
```

### 问题 2：无法通过浏览器访问

1. 确认容器正在运行：`docker ps`
2. 确认端口未被占用：`netstat -ano | findstr "6080"`
3. 等待 30-60 秒让服务完全启动

### 问题 3：微信界面显示异常

重新启动容器：
```bash
docker-compose restart
```

### 问题 4：构建失败

确保 `WeChatLinux_x86_64.deb` 文件存在于项目根目录：
```bash
ls d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\WeChatLinux_x86_64.deb
```

### 问题 5：无法连接到服务器

1. 检查容器是否正在运行
2. 检查端口映射是否正确
3. 查看 [start_wechat.sh](./start_wechat.sh) 脚本日志

## 安全说明

- VNC 密码默认为 `wechat123`，生产环境请修改
- 容器以特权模式运行，仅用于开发测试
- 不要将此容器暴露到公网

## 开发说明

### 自定义分辨率

修改 `Dockerfile` 中的 Xvfb 启动参数：
```bash
Xvfb :99 -screen 0 1920x1080x24 &
```
改为：
```bash
Xvfb :99 -screen 0 2560x1440x24 &
```

### 修改 VNC 密码

修改 `start_wechat.sh` 中的密码：
```bash
echo "wechat123" | vncpasswd -f > /root/.vnc/passwd
```

### 自定义字体

在 `Dockerfile` 中添加中文字体：
```dockerfile
RUN apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei
```

## 技术栈

- **基础镜像**：Ubuntu 22.04
- **显示服务**：Xvfb + Fluxbox
- **远程访问**：noVNC + x11vnc
- **应用**：Linux 微信 (WeChatLinux_x86_64.deb)
- **生产者服务**：FastAPI + Redis Stream
- **屏幕截图**：mss（兼容 Docker Xvfb）

## 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构详细说明
- [BUSINESS_LOGIC_TEST.md](./BUSINESS_LOGIC_TEST.md) - 业务逻辑测试指南
- [QUICKSTART.md](./QUICKSTART.md) - 快速开始
- [agent.md](../../agent.md) - 项目整体架构说明
- [claude.md](../../claude.md) - 开发规范和约定
