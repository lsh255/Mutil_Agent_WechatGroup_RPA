# 归档文件说明

此目录包含已过时或不再使用的配置文件。

## 文件说明

### Dockerfile
- **用途**: 早期开发版本，基于 python:3.12-slim
- **状态**: 过时
- **原因**: 已被新的分层 Dockerfile 替代

### Dockerfile.single
- **用途**: 分层设计的 WeChat 沙箱 Dockerfile
- **状态**: 已迁移
- **原因**: 已移动到主目录并重命名为 `Dockerfile`

### Dockerfile.wechat
- **用途**: 简化版 WeChat 沙箱
- **状态**: 过时
- **原因**: 功能已合并到新的 Dockerfile 中

### docker-compose.wechat.yml
- **用途**: WeChat 沙箱单独部署配置
- **状态**: 过时
- **原因**: 已被新的 docker-compose.test.yml 替代
