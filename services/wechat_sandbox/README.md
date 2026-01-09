# WeChat 沙箱项目

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
| [QUICKSTART.md](./QUICKSTART.md) | 快速开始指南 |
| [WECHAT_SANDBOX.md](./WECHAT_SANDBOX.md) | WeChat 沙箱文档 |

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
