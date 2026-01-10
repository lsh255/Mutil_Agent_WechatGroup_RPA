# 微信沙箱快速启动指南

## 目录结构说明

| 文件/目录 | 用途 |
|-----------|------|
| [docker/sandbox/Dockerfile](../../docker/sandbox/Dockerfile) | 生产环境基础镜像（分层设计） |
| [docker/sandbox/Dockerfile.test](../../docker/sandbox/Dockerfile.test) | 测试环境镜像（添加 FastAPI） |
| [docker/compose/docker-compose.yml](../../docker/compose/docker-compose.yml) | 生产单实例部署 |
| [docker/compose/docker-compose.multi.yml](../../docker/compose/docker-compose.multi.yml) | 生产多实例部署（3 个实例） |
| [docker/compose/docker-compose.sandbox.test.yml](../../docker/compose/docker-compose.sandbox.test.yml) | 测试单实例部署（含 FastAPI） |
| [main.py](./main.py) | 主启动脚本 |
| [backup_start.py](./backup_start.py) | 备用启动脚本 |
| [docker/scripts/start_wechat.sh](../../docker/scripts/start_wechat.sh) | 微信沙箱启动脚本（Xvfb、Fluxbox、noVNC、WeChat） |
| [docker/scripts/start_wechat_sandbox.bat](../../docker/scripts/start_wechat_sandbox.bat) | Windows 启动脚本 |
| [requirements.txt](./requirements.txt) | Python 依赖列表 |
| [api/](./api/) | API 模块（FastAPI 应用、路由、配置管理） |
| [core/](./core/) | 核心业务逻辑模块（消息监控、提取、分类、队列管理） |
| [core/detector/](./core/detector/) | 变化检测模块（dHash、气泡检测、屏幕变化） |
| [core/extractor/](./core/extractor/) | 内容提取模块（文本提取、媒体截图） |
| [core/producer/](./core/producer/) | 生产者模块（Observer、ContentFetcher、AgentConsumer） |
| [core/queue/](./core/queue/) | Redis Stream 队列管理 |
| [core/classifier/](./core/classifier/) | 消息类型分类器（文本/图片/视频/链接） |
| [core/platform/](./core/platform/) | 平台适配模块（跨平台支持） |
| [utils/](./utils/) | 工具模块（配置、日志） |
| [tests/](./tests/) | 单元测试和集成测试 |
| [services/](./services/) | 服务模块 |
| [archive/](./archive/) | 归档文件 |

## 准备工作

### 1. 确保以下文件存在

在 `services/wechat_sandbox/build` 目录下：
- `WeChatLinux_x86_64.deb` - 微信 Linux 版安装包
- `fonts-noto-cjk_20240730+repack1-1_all.deb` - 中文字体包

### 2. 检查文件位置

```bash
cd services/wechat_sandbox
ls WeChatLinux_x86_64.deb
ls fonts-noto-cjk_20240730+repack1-1_all.deb
```

## 构建镜像

### 构建生产环境基础镜像

```bash
docker build -f docker/sandbox/Dockerfile -t wechat_sandbox:latest .
```

### 构建说明

- **分层设计**：Dockerfile 采用分层结构，便于缓存和增量构建
- **依赖补丁层**：第 7 层专门用于添加缺失依赖，后续发现新依赖可在此添加
- **本地开发优化**：保留 apt lists，加快构建速度

## 测试环境部署

### 1. 构建测试镜像

```bash
# Dockerfile.test 继承自 wechat_sandbox:latest，添加 FastAPI 支持
docker build -f docker/sandbox/Dockerfile.test -t wechat_sandbox-test:latest .
```

### 2. 启动测试环境

```bash
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d
```

### 3. 访问服务

- **noVNC Web 界面**: http://localhost:6080
- **VNC 客户端**: localhost:5900（密码: wechat123）
- **FastAPI 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **服务状态**: http://localhost:8000/api/status
- **SSE 消息流**: http://localhost:8000/api/stream
- **Redis**: localhost:6379

### 4. 停止测试环境

```bash
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down
```

## 生产环境部署

### 单实例部署

```bash
docker-compose -f docker/compose/docker-compose.yml up -d
```

**访问地址**:
- noVNC: http://localhost:6080
- VNC: localhost:5900（密码: vnc123）
- FastAPI: http://localhost:8000

### 多实例部署

```bash
docker-compose -f docker/compose/docker-compose.multi.yml up -d
```

**访问地址**:

| 实例 | noVNC | VNC | FastAPI |
|------|-------|-----|---------|
| 1 | http://localhost:6081 | localhost:5901 | http://localhost:8001 |
| 2 | http://localhost:6082 | localhost:5902 | http://localhost:8002 |
| 3 | http://localhost:6083 | localhost:5903 | http://localhost:8003 |

VNC 密码: vnc123

## 端口说明

### 测试环境
| 端口 | 服务 |
|------|------|
| 8000 | FastAPI |
| 6080 | noVNC |
| 5900 | VNC |
| 6379 | Redis |

### 生产单实例
| 端口 | 服务 |
|------|------|
| 8000 | FastAPI |
| 6080 | noVNC |
| 5900 | VNC |
| 6379 | Redis |

### 生产多实例
| 端口范围 | 服务 |
|----------|------|
| 8001-8003 | FastAPI |
| 6081-6083 | noVNC |
| 5901-5903 | VNC |
| 6379 | Redis |

## 常用命令

### 查看容器状态
```bash
# 测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml ps

# 生产单实例
docker-compose -f docker/compose/docker-compose.yml ps

# 生产多实例
docker-compose -f docker/compose/docker-compose.multi.yml ps
```

### 查看日志
```bash
# 测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml logs -f

# 生产单实例
docker-compose -f docker/compose/docker-compose.yml logs -f

# 生产多实例
docker-compose -f docker/compose/docker-compose.multi.yml logs -f
```

### 重启服务
```bash
# 测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml restart

# 生产单实例
docker-compose -f docker/compose/docker-compose.yml restart

# 生产多实例
docker-compose -f docker/compose/docker-compose.multi.yml restart
```

### 停止服务
```bash
# 测试环境
docker-compose -f docker/compose/docker-compose.sandbox.test.yml down

# 生产单实例
docker-compose -f docker/compose/docker-compose.yml down

# 生产多实例
docker-compose -f docker/compose/docker-compose.multi.yml down
```

### 进入容器
```bash
# 测试环境
docker exec -it wechat_sandbox_test bash

# 生产单实例
docker exec -it wechat_producer_service bash

# 生产多实例
docker exec -it wechat_producer_service_1 bash
docker exec -it wechat_producer_service_2 bash
docker exec -it wechat_producer_service_3 bash
```

## 常见问题

### VNC 无法连接
1. 检查容器是否启动：`docker ps`
2. 查看容器日志：`docker logs <container_name>`
3. 确认端口是否被占用：`netstat -ano | findstr :5900`

### WeChat 无法启动
1. 检查依赖是否完整：`docker logs <container_name>`
2. 进入容器手动启动：`docker exec -it <container_name> bash`，然后执行 `/opt/wechat/wechat`
3. 如有缺失依赖，在 Dockerfile 第 7 层（依赖补丁层）添加

### FastAPI 无法访问
1. 检查端口映射是否正确
2. 查看容器日志确认服务是否启动
3. 检查 Redis 连接是否正常
4. 确认 API 路由前缀是否正确（/api/）

### Redis 连接失败
1. 确认 Redis 容器已启动：`docker ps | grep redis`
2. 检查健康状态：`docker exec <redis_container> redis-cli ping`
3. 确认网络配置正确

### 构建镜像失败
1. 确认 deb 文件在正确位置
2. 检查网络连接（下载依赖）
3. 查看详细错误信息：`docker build -f Dockerfile --progress=plain .`

## 数据持久化

### 测试环境
- **微信数据**: `wechat_data` volume
- **媒体文件**: `./media` 目录
- **日志文件**: `./logs` 目录
- **Redis 数据**: `redis_data` volume

### 生产环境
- **微信数据**: `wechat_data` volume
- **媒体文件**: `./media` 目录
- **Redis 数据**: `redis_data` volume

### 备份数据
```bash
# 备份 volume
docker run --rm -v wechat_data:/data -v $(pwd):/backup ubuntu tar czf /backup/wechat_data.tar.gz /data

# 备份媒体文件
tar czf media_backup.tar.gz ./media
```

## 性能优化

### 降低资源占用
1. 调整 `xvfb` 分辨率：修改 `start_wechat.sh` 中的分辨率参数
2. 限制容器资源：在 docker-compose.yml 中添加 `mem_limit` 和 `cpus`

### 提升构建速度
1. 利用 Docker 层缓存：不频繁修改的层放在前面
2. 使用 BuildKit：`DOCKER_BUILDKIT=1 docker build ...`

### 生产环境优化
1. 使用多实例并行处理
2. Redis 集群部署提升并发
3. 增加实例数量实现水平扩展

## 安全建议

1. **修改默认密码**: 更改 VNC 密码
2. **端口映射限制**: 仅开放必要端口
3. **网络隔离**: 使用自定义网络
4. **定期更新**: 及时更新系统和依赖
5. **日志监控**: 设置日志告警

## 相关文档

- [README.md](./README.md) - 项目总览
- [WECHAT_SANDBOX.md](./WECHAT_SANDBOX.md) - WeChat 沙箱详细说明
- [archive/README.md](./archive/README.md) - 归档文件说明
