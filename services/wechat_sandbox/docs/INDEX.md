# Wechat Sandbox 文档索引

欢迎使用微信沙盒服务文档！本文档将帮助您快速找到所需信息。

## 🚀 快速开始

### 新手入门
1. [项目说明](../README.md) - 了解项目概况和功能
2. [快速开始](../QUICKSTART.md) - 快速上手指南
3. [目录结构](../DIRECTORY_STRUCTURE_V2.md) - 了解项目结构

### 核心概念
- [消息类型说明](MESSAGE_TYPES.md) - 了解3种消息类型的处理方式
- [AT-SPI使用指南](AT_SPI_GUIDE.md) - 深入了解AT-SPI方案
- [架构设计文档](ARCHITECTURE.md) - 了解系统架构

## 📚 文档分类

### 按主题分类

#### 1. 快速上手
| 文档 | 说明 | 适用人群 |
|------|------|---------|
| [README](../README.md) | 项目说明 | 所有用户 |
| [QUICKSTART](../QUICKSTART.md) | 快速开始 | 新用户 |
| [CHANGELOG_v2.0](../CHANGELOG_v2.0.md) | 变更日志 | 了解更新 |

#### 2. 核心功能
| 文档 | 说明 | 相关模块 |
|------|------|---------|
| [MESSAGE_TYPES](MESSAGE_TYPES.md) | 消息类型说明 | core/extractor/ |
| [AT_SPI_GUIDE](AT_SPI_GUIDE.md) | AT-SPI指南 | core/atspi/ |
| [ARCHITECTURE](ARCHITECTURE.md) | 架构设计 | 全局 |

#### 3. 开发指南
| 文档 | 说明 | 适用场景 |
|------|------|---------|
| [DIRECTORY_STRUCTURE_V2](../DIRECTORY_STRUCTURE_V2.md) | 目录结构 | 开发者 |
| [测试说明](../tests/README.md) | 测试指南 | 测试人员 |

### 按用户角色分类

#### 👨‍💻 开发者
**必读文档**：
1. [README](../README.md) - 了解项目
2. [DIRECTORY_STRUCTURE_V2](../DIRECTORY_STRUCTURE_V2.md) - 了解结构
3. [MESSAGE_TYPES](MESSAGE_TYPES.md) - 消息类型
4. [AT_SPI_GUIDE](AT_SPI_GUIDE.md) - AT-SPI方案

**常用代码**：
```python
# 导入配置
from config.config import config

# 使用AT-SPI观察者
from core.atspi.observer import ATSPIObserver

# 使用消息提取器
from core.extractor import UniversalMessageExtractor, MessageType

# 使用混合生产者
from core.producer.hybrid_producer import HybridProducer, ProductionMode
```

#### 👨‍🔧 运维人员
**必读文档**：
1. [README](../README.md) - 快速了解
2. [QUICKSTART](../QUICKSTART.md) - 部署指南
3. [CHANGELOG_v2.0](../CHANGELOG_v2.0.md) - 版本变更

**常用命令**：
```bash
# 构建镜像
docker build -f docker/sandbox/Dockerfile -t wechat_sandbox:latest ../..

# 启动服务
docker-compose -f docker/compose/docker-compose.sandbox.test.yml up -d

# 查看日志
docker logs -f wechat_sandbox_test

# 健康检查
curl http://localhost:8000/health
```

#### 🧪 测试人员
**必读文档**：
1. [README](../README.md) - 了解功能
2. [tests/README.md](../tests/README.md) - 测试指南
3. [MESSAGE_TYPES](MESSAGE_TYPES.md) - 测试场景

**测试命令**：
```bash
# 运行所有测试
pytest services/wechat_sandbox/tests/

# 运行特定测试
pytest services/wechat_sandbox/tests/test_producer_service.py -v

# 查看覆盖率
pytest --cov=services.wechat_sandbox services/wechat_sandbox/tests/
```

## 🔍 文档导航

### 我要...

**了解项目**
→ 📖 [项目说明](../README.md)

**快速开始**
→ 🚀 [快速开始](../QUICKSTART.md)

**了解消息类型**
→ 📨 [消息类型说明](MESSAGE_TYPES.md)

**使用AT-SPI**
→ 🔧 [AT-SPI使用指南](AT_SPI_GUIDE.md)

**了解架构**
→ 🏗️ [架构设计文档](ARCHITECTURE.md)

**查看目录结构**
→ 📂 [目录结构说明](../DIRECTORY_STRUCTURE_V2.md)

**查看变更记录**
→ 📝 [变更日志](../CHANGELOG_v2.0.md)

**运行测试**
→ 🧪 [测试指南](../tests/README.md)

## 📖 文档阅读顺序

### 第一次使用建议阅读顺序

1. **开始** (5分钟)
   - [README](../README.md) - 项目概述

2. **上手** (15分钟)
   - [QUICKSTART](../QUICKSTART.md) - 快速开始
   - [DIRECTORY_STRUCTURE_V2](../DIRECTORY_STRUCTURE_V2.md) - 目录结构

3. **深入** (30分钟)
   - [MESSAGE_TYPES](MESSAGE_TYPES.md) - 消息类型
   - [AT_SPI_GUIDE](AT_SPI_GUIDE.md) - AT-SPI方案
   - [ARCHITECTURE](ARCHITECTURE.md) - 架构设计

### 开发者建议阅读顺序

1. **基础** → [README](../README.md) → [DIRECTORY_STRUCTURE_V2](../DIRECTORY_STRUCTURE_V2.md)
2. **核心** → [MESSAGE_TYPES](MESSAGE_TYPES.md) → [AT_SPI_GUIDE](AT_SPI_GUIDE.md)
3. **架构** → [ARCHITECTURE](ARCHITECTURE.md)
4. **测试** → [tests/README.md](../tests/README.md)

### 运维人员建议阅读顺序

1. **了解** → [README](../README.md)
2. **部署** → [QUICKSTART](../QUICKSTART.md)
3. **维护** → [CHANGELOG_v2.0](../CHANGELOG_v2.0.md)

## 🔗 外部资源

### 项目文档
- [项目主文档](../../../README.md)
- [Docker文档](../../../docker/README.md)
- [Docker脚本说明](../../../docker/scripts/README.md)

### 技术文档
- [AT-SPI 官方文档](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Redis 文档](https://redis.io/docs/)

## 📝 文档更新记录

### v2.0 (2025-01-14)
- ✅ 整合文档到docs/目录
- ✅ 更新所有路径引用
- ✅ 简化消息类型说明
- ✅ 添加文档索引

### v1.0 (2025-01-12)
- 初始版本
- 分散在各个目录

## 💡 文档贡献

### 文档规范
- 使用 Markdown 格式
- 添加清晰的标题和目录
- 提供代码示例
- 保持简洁明了

### 更新文档
当您修改代码时，请同步更新相关文档：
1. 修改目录结构 → 更新 DIRECTORY_STRUCTURE_V2.md
2. 修改消息类型 → 更新 MESSAGE_TYPES.md
3. 修改API → 更新 README.md 和 ARCHITECTURE.md
4. 重大变更 → 更新 CHANGELOG_v2.0.md

## 🆘 获取帮助

### 常见问题
- 查看 [README](../README.md) 的故障排查部分
- 查看 [CHANGELOG_v2.0](../CHANGELOG_v2.0.md) 的常见问题部分

### 报告问题
- 提交 Issue
- 联系维护者

---

**最后更新**：2025-01-14
**维护者**：Claude Code
