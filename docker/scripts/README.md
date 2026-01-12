# Docker Scripts 目录说明

本目录包含容器运行脚本，按功能分为两类。

## 目录结构

```
scripts/
├── common/              # 通用脚本（不需要 AT-SPI 支持）
└── atspi/               # AT-SPI 相关脚本（需要 AT-SPI 支持）
```

## 通用脚本 (common/)

不需要 AT-SPI 辅助功能支持的基础脚本，适用于所有微信沙盒环境。

| 脚本 | 说明 | 使用场景 |
|------|------|----------|
| `start_all.sh` | 启动所有服务（VNC、noVNC、微信） | 完整环境启动 |
| `start_sandbox.sh` | 启动沙盒容器环境 | 容器初始化 |
| `start_wechat.sh` | 启动微信应用 | 微信启动 |
| `start_wechat_sandbox.bat` | Windows 批处理启动脚本 | Windows 环境 |

### 使用示例

```bash
# 完整启动
docker exec -it wechat-sandbox bash /app/docker/scripts/common/start_all.sh

# 仅启动微信
docker exec -it wechat-sandbox bash /app/docker/scripts/common/start_wechat.sh
```

## AT-SPI 脚本 (atspi/)

需要 AT-SPI 辅助功能框架支持的脚本，仅适用于测试环境（`wechat_sandbox-test:latest` 镜像）。

| 脚本 | 说明 | 依赖 |
|------|------|------|
| `restart_wechat_with_dbus.sh` | 重启微信并连接 DBus 会话 | DBus 会话 |
| `run_atspi_observer.sh` | 运行 AT-SPI 观察者（监听 UI 事件） | pyatspi |
| `test_atspi_simple.py` | AT-SPI 简单功能测试 | pyatspi |
| `test_atspi_solution.sh` | AT-SPI 完整测试方案 | pyatspi, Redis |

### 使用示例

```bash
# 运行 AT-SPI 完整测试
docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh

# 运行 AT-SPI 简单测试
docker exec -it wechat_sandbox_test python3 /app/test_atspi_simple.py

# 启动 AT-SPI 观察者
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/run_atspi_observer.sh

# 重启微信（使用 DBus 会话）
docker exec -it wechat_sandbox_test bash /app/docker/scripts/atspi/restart_wechat_with_dbus.sh
```

## 脚本路径说明

### 在容器内

- **通用脚本**: `/app/docker/scripts/common/`
- **AT-SPI 脚本**: `/app/docker/scripts/atspi/`
- **AT-SPI 测试脚本**: `/app/test_atspi_*` (直接复制到 `/app/`)

### 在宿主机

- **通用脚本**: `docker/scripts/common/`
- **AT-SPI 脚本**: `docker/scripts/atspi/`

## 注意事项

1. **镜像差异**:
   - `wechat_sandbox:latest` (基础镜像) - 只包含通用脚本
   - `wechat_sandbox-test:latest` (测试镜像) - 包含通用脚本 + AT-SPI 脚本

2. **权限**:
   - 所有 `.sh` 脚本都需要可执行权限
   - Dockerfile 会自动设置权限：`RUN chmod +x /app/script.sh`

3. **环境变量**:
   - AT-SPI 脚本需要以下环境变量：
     - `QT_ACCESSIBILITY=1`
     - `GNOME_ACCESSIBILITY=1`
     - `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`
     - `TZ=Asia/Shanghai`

4. **DBus 会话**:
   - AT-SPI 脚本依赖正确的 DBus 会话
   - 测试镜像会自动配置 DBus 会话

## 相关文档

- [AT-SPI 混合方案说明](../../docs/atspi_hybrid_solution.md)
- [AT-SPI 部署配置说明](../../docs/atspi_deployment_config.md)
- [Docker 主文档](../README.md)
