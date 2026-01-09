# 微信沙盒容器使用说明

## 概述

这是一个基于 Linux 微信的沙盒容器，用于本地测试和开发微信自动化功能。

## 前置要求

1. Docker 已安装并运行
2. Linux 微信安装包已放置在项目根目录：`WeChatLinux_x86_64.deb`

## 文件结构

```
services/wechat_sandbox/
├── Dockerfile.wechat           # 微信沙盒容器定义
├── docker-compose.wechat.yml    # 微信沙盒容器编排
├── start_wechat.sh             # 微信启动脚本
├── media/                      # 媒体文件目录（自动创建）
└── logs/                       # 日志文件目录（自动创建）
```

## 快速开始

### 1. 构建并启动容器

```bash
cd d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\services\wechat_sandbox
docker-compose -f docker-compose.wechat.yml up -d --build
```

### 2. 查看容器日志

```bash
docker-compose -f docker-compose.wechat.yml logs -f
```

### 3. 访问微信界面

#### 方式一：通过浏览器访问（推荐）

1. 打开浏览器访问：`http://localhost:6080/vnc.html`
2. 在连接对话框中输入密码：`wechat123`
3. 等待微信界面加载完成

#### 方式二：通过 VNC 客户端访问

1. 使用 VNC 客户端（如 RealVNC、TightVNC）连接：
   - 主机：`localhost`
   - 端口：`5900`
   - 密码：`wechat123`

## 常用命令

### 停止容器

```bash
docker-compose -f docker-compose.wechat.yml down
```

### 重启容器

```bash
docker-compose -f docker-compose.wechat.yml restart
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

### 3. 数据持久化
- 微信用户数据存储在 Docker volume 中
- 媒体文件映射到本地 `media/` 目录
- 日志文件映射到本地 `logs/` 目录

## 故障排查

### 问题 1：容器无法启动

检查 Docker 日志：
```bash
docker-compose -f docker-compose.wechat.yml logs
```

### 问题 2：无法通过浏览器访问

1. 确认容器正在运行：`docker ps`
2. 确认端口未被占用：`netstat -ano | findstr "6080"`
3. 等待 30-60 秒让服务完全启动

### 问题 3：微信界面显示异常

重新启动容器：
```bash
docker-compose -f docker-compose.wechat.yml restart
```

### 问题 4：构建失败

确保 `WeChatLinux_x86_64.deb` 文件存在于项目根目录：
```bash
ls d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\WeChatLinux_x86_64.deb
```

## 安全说明

- VNC 密码默认为 `wechat123`，生产环境请修改
- 容器以特权模式运行，仅用于开发测试
- 不要将此容器暴露到公网

## 端口说明

| 端口 | 用途 | 说明 |
|------|------|------|
| 6080 | noVNC Web 界面 | 通过浏览器访问微信 |
| 5900 | VNC 服务 | 通过 VNC 客户端访问微信 |

## 开发说明

### 自定义分辨率

修改 `Dockerfile.wechat` 中的 Xvfb 启动参数：
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

在 `Dockerfile.wechat` 中添加中文字体：
```dockerfile
RUN apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei
```

## 技术栈

- **基础镜像**：Ubuntu 22.04
- **显示服务**：Xvfb + Fluxbox
- **远程访问**：noVNC + x11vnc
- **应用**：Linux 微信 (WeChatLinux_x86_64.deb)

## 相关文档

- [QUICKSTART.md](./QUICKSTART.md) - 微信沙盒快速开始指南
- [agent.md](../../agent.md) - 项目整体架构说明
- [claude.md](../../claude.md) - 开发规范和约定
