# Wechat Sandbox 重整变更日志

## 版本信息
- **版本**：v2.0
- **日期**：2025-01-14
- **备份文件**：`wechat_sandbox_backup_20260114_142514.tar.gz` (257MB)

## 📋 变更概览

本次重整主要目标是：
1. ✅ 整合重复模块
2. ✅ 简化目录结构
3. ✅ 统一文档管理
4. ✅ 保持沙盒独立性

## 🔄 模块路径变更

### 核心变更

| 旧路径 | 新路径 | 说明 |
|-------|--------|------|
| `core/message/extractor.py` | `core/extractor/message_extractor.py` | 整合提取器模块 |
| `core/message/models.py` | `core/extractor/models.py` | 整合数据模型 |
| `core/message/__init__.py` | `core/extractor/__init__.py` | 更新模块导出 |
| `utils/config.py` | `config/config.py` | 独立配置管理 |
| `core/producer/agent_consumer.py` | `core/producer/consumer.py` | 简化命名 |
| `config.yaml` | `config/config.yaml` | 配置文件统一管理 |
| `config.production.yaml` | `config/config.production.yaml` | 生产配置统一管理 |

### 导入语句变更

#### Python代码更新

**旧导入方式**：
```python
# 消息提取器
from core.extractor import UniversalMessageExtractor, MessageType, ExtractedMessage

# 配置
from config.config import config

# 消费者
from core.producer.consumer import AgentConsumer
```

**新导入方式**：
```python
# 消息提取器（统一）
from core.extractor import UniversalMessageExtractor, MessageType, ExtractedMessage

# 配置（独立）
from config.config import config
# 或
from config import config

# 消费者（简化命名）
from core.producer.consumer import AgentConsumer
```

#### 外部项目引用更新

**测试文件更新**：
```python
# 旧路径
from services.wechat_sandbox.core.producer.atspi_observer import ATSPIObserver

# 新路径
from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
```

## 📂 目录结构变更

### 新增目录
- `config/` - 沙盒配置管理（独立）
- `docs/` - 沙盒文档（独立）
- `core/extractor/` - 统一的消息提取器模块

### 删除目录
- `core/message/` - 已合并到 `core/extractor/`
- `core/classifier/` - 未使用，已删除
- `core/extractor/`（旧版）- 与message重复，已删除
- `core/platform/` - 功能简单，移到 `utils/`
- `core/queue/` - 未使用，已删除
- `core/window/` - 空目录，已删除

### 删除文件
- `core/producer/observer.py` - 旧的视觉观察者
- `core/producer/monitor.py` - 旧的监控器
- `core/producer/content_fetcher.py` - 旧的内容提取器
- `core/producer/photo_extractor.py` - 旧图片提取器，已合并
- `core/producer/README.md` - 旧文档
- `core/producer/README_PHOTO_EXTRACTOR.md` - 旧文档
- `core/producer/SSE_MESSAGE_MODEL.md` - 旧文档
- `core/producer/UNIVERSAL_MESSAGE_EXTRACTION.md` - 旧文档
- `core/producer/sse_message_model.jsonl` - 示例文件

### 文档迁移
| 旧文档 | 新位置 |
|-------|--------|
| `AT_SPI_VS_VISUAL_COMPARISON.md` | `docs/AT_SPI_GUIDE.md` |
| `MESSAGE_TYPES_V2.md` | `docs/MESSAGE_TYPES.md` |
| `DIRECTORY_STRUCTURE.md` | `docs/DIRECTORY_STRUCTURE.md` |
| `ARCHITECTURE.md` | `docs/ARCHITECTURE.md` |

## 🔧 代码更新清单

### 已更新的文件
- ✅ `core/__init__.py` - 更新模块导出
- ✅ `core/producer/__init__.py` - 更新导出列表
- ✅ `core/extractor/__init__.py` - 新建模块导出
- ✅ `core/atspi/observer.py` - 更新导入路径
- ✅ `config/__init__.py` - 新建配置模块
- ✅ `tests/atspi/test_atspi_observer.py` - 更新导入路径

### 需要外部项目配合更新的文件
- ⚠️ `tests/atspi/test_atspi_observer.py` - 已更新导入路径
- ⚠️ 任何引用 `core.message` 的文件 - 需更新为 `core.extractor`
- ⚠️ 任何引用 `utils.config` 的文件 - 需更新为 `config.config`

## 📝 配置变更

### 配置文件路径变更
项目根目录的配置文件移至 `config/` 目录：

**旧结构**：
```
services/wechat_sandbox/
├── config.yaml
├── config.production.yaml
└── utils/
    └── config.py
```

**新结构**：
```
services/wechat_sandbox/
└── config/
    ├── config.yaml
    ├── config.production.yaml
    └── config.py
```

### 环境变量
配置的环境变量保持不变，仍可通过 `utils/config.py` 的方式访问，但现在推荐使用新路径：
```python
# 推荐
from config.config import config

# 兼容旧代码（仍可用）
from utils.config import config
```

## 🚀 迁移指南

### 对于项目开发者

#### 1. 更新导入语句
搜索并替换以下模式：
```bash
# Python文件
from core.message -> from core.extractor
from utils.config import config -> from config.config import config

# 外部引用
from services.wechat_sandbox.core.message -> from services.wechat_sandbox.core.extractor
from services.wechat_sandbox.core.producer.atspi_observer -> from services.wechat_sandbox.core.atspi.observer
```

#### 2. 更新配置引用
```python
# 旧方式
from utils.config import config

# 新方式
from config.config import config
# 或
from config import config
```

#### 3. 测试验证
运行测试确保所有功能正常：
```bash
cd services/wechat_sandbox
python -m pytest tests/
```

### 对于文档维护者

#### 更新路径引用
在文档中更新以下路径：
- `core/message/` → `core/extractor/`
- `core/producer/observer.py` → `core/atspi/observer.py`
- `utils/config.py` → `config/config.py`

## ✅ 验证检查清单

- [x] 备份完成
- [x] 目录结构调整
- [x] 文件移动完成
- [x] 旧文件删除
- [x] 导入路径更新
- [x] 测试文件更新
- [x] 模块导入验证
- [ ] 文档完全更新
- [ ] 完整测试通过

## 📚 相关文档

- [新目录结构说明](DIRECTORY_STRUCTURE_V2.md)
- [重整计划v2.0](RESTRUCTURE_PLAN_V2.md)
- [消息类型说明](docs/MESSAGE_TYPES.md)
- [AT-SPI使用指南](docs/AT_SPI_GUIDE.md)

## 🆘 常见问题

### Q1: 导入错误 "No module named 'core.message'"
**A**: 使用新的导入路径：
```python
# 旧
from core.message.extractor import UniversalMessageExtractor

# 新
from core.extractor import UniversalMessageExtractor
```

### Q2: 配置导入错误
**A**: 使用新的配置路径：
```python
# 旧
from utils.config import config

# 新
from config.config import config
```

### Q3: 找不到某个模块
**A**: 参考本文档的"模块路径变更"部分，确认新路径。大多数模块保持不变，只有以下模块路径变更：
- `message` → `extractor`
- `producer.atspi_observer` → `atspi.observer`

## 📞 联系方式

如有问题或疑问，请查阅：
- 项目README
- 相关文档
- 或提交Issue

---

**维护者**：Claude Code
**最后更新**：2025-01-14
