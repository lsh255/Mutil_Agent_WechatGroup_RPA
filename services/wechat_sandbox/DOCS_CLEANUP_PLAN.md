# Wechat Sandbox 文档清理计划

## 📋 文档清单分析

### ✅ 保留的文档

#### 核心文档（根目录）
| 文档 | 状态 | 说明 |
|------|------|------|
| `README.md` | ✅ 保留并更新 | 项目说明，需要更新路径引用 |
| `QUICKSTART.md` | ✅ 保留并更新 | 快速开始指南，需要更新路径和命令 |
| `CHANGELOG_v2.0.md` | ✅ 保留 | 变更日志（最新） |
| `DIRECTORY_STRUCTURE_V2.md` | ✅ 保留 | 新目录结构说明（最新） |

#### docs/目录
| 文档 | 状态 | 说明 |
|------|------|------|
| `docs/ARCHITECTURE.md` | ✅ 保留 | 架构文档 |
| `docs/AT_SPI_GUIDE.md` | ✅ 保留 | AT-SPI使用指南（整合） |
| `docs/MESSAGE_TYPES.md` | ✅ 保留 | 消息类型说明（v2.0） |

#### 测试文档
| 文档 | 状态 | 说明 |
|------|------|------|
| `tests/README.md` | ✅ 保留并更新 | 测试说明，需要更新测试路径 |
| `archive/README.md` | ✅ 保留 | 归档说明 |

### ❌ 删除的文档

#### 过时的文档
| 文档 | 原因 |
|------|------|
| `RESTRUCTURE_PLAN_V2.md` | 重整已完成，不需要保留计划文档 |
| `docs/DIRECTORY_STRUCTURE.md` | 已有V2版本，旧版过时 |
| `BUSINESS_LOGIC_TEST.md` | 业务逻辑测试，过时，可以归档或删除 |
| `tests/.pytest_cache/README.md` | pytest缓存目录，不应有README |

### 📝 需要更新的文档

#### 1. README.md
**需要更新的内容**：
- 目录结构描述
- 导入路径示例
- 文档引用链接
- 快速开始命令

#### 2. QUICKSTART.md
**需要更新的内容**：
- 配置路径
- 导入示例
- 测试命令
- 文档链接

#### 3. tests/README.md
**需要更新的内容**：
- 测试路径引用
- 测试命令

## 🎯 清理操作

### 步骤1：删除过时文档
```bash
cd services/wechat_sandbox
rm RESTRUCTURE_PLAN_V2.md
rm docs/DIRECTORY_STRUCTURE.md
rm BUSINESS_LOGIC_TEST.md
rm tests/.pytest_cache/README.md
```

### 步骤2：更新核心文档
- 更新 `README.md`
- 更新 `QUICKSTART.md`
- 更新 `tests/README.md`

### 步骤3：创建文档索引
在 `docs/` 目录创建 `INDEX.md` 作为文档导航

## 📚 最终文档结构

```
services/wechat_sandbox/
├── README.md                   # 项目说明（入口）
├── QUICKSTART.md              # 快速开始
├── CHANGELOG_v2.0.md          # 变更日志
├── DIRECTORY_STRUCTURE_V2.md  # 目录结构
│
├── docs/                      # 详细文档
│   ├── INDEX.md               # 文档索引 ⭐ 新建
│   ├── ARCHITECTURE.md        # 架构设计
│   ├── AT_SPI_GUIDE.md        # AT-SPI指南
│   └── MESSAGE_TYPES.md       # 消息类型
│
├── tests/
│   └── README.md              # 测试说明
│
└── archive/
    └── README.md              # 归档说明
```

## 🔄 文档关系图

```
README.md (入口)
  ├─► QUICKSTART.md (快速上手)
  ├─► DIRECTORY_STRUCTURE_V2.md (了解结构)
  ├─► CHANGELOG_v2.0.md (版本历史)
  └─► docs/INDEX.md (详细文档)
       ├─► docs/ARCHITECTURE.md (架构)
       ├─► docs/AT_SPI_GUIDE.md (AT-SPI)
       └─► docs/MESSAGE_TYPES.md (消息类型)
```

---

**创建时间**：2025-01-14
**维护者**：Claude Code
