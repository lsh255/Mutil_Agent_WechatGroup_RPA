# 环境初始化指南

## 概述

本文档提供多模态Agent微信群自动化项目的完整环境初始化步骤，适用于Windows、Linux和Mac系统。

## 前置要求

### 必需软件

1. **Python 3.12 或更高版本**
   - Windows: 从 [python.org](https://www.python.org/downloads/) 下载安装
   - Linux: `sudo apt install python3.12`
   - Mac: `brew install python@3.12`

2. **Conda**（可选但推荐）
   - Anaconda: 从 [anaconda.com](https://www.anaconda.com/) 下载安装
   - Miniconda: 从 [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html) 下载安装

3. **Docker 和 Docker Compose**
   - Windows: 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: `curl -fsSL https://get.docker.com | sh`
   - Mac: 安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

4. **Git**
   - Windows: 从 [git-scm.com](https://git-scm.com/) 下载安装
   - Linux: `sudo apt install git`
   - Mac: `brew install git`

## 快速开始

### 方式一：使用 Conda 环境（推荐）

#### Windows 用户

```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装项目（开发模式）
pip install -e .

# 6. 创建必要的目录
mkdir data
mkdir data\chroma_db
mkdir data\wechat_profile
mkdir output
mkdir templates
mkdir logs

# 7. 复制环境变量配置
copy .env.example .env

# 8. 启动 Docker 服务
docker-compose up -d redis ollama

# 9. 等待 Ollama 服务启动（约30秒），然后拉取模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 10. 初始化知识库
python scripts/init_knowledge_base.py

# 11. 启动协调中心
python -m services.orchestrator.main
```

#### Linux/Mac 用户

```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装项目（开发模式）
pip install -e .

# 6. 创建必要的目录
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates
mkdir -p logs

# 7. 复制环境变量配置
cp .env.example .env

# 8. 启动 Docker 服务
docker-compose up -d redis ollama

# 9. 等待 Ollama 服务启动（约30秒），然后拉取模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 10. 初始化知识库
python scripts/init_knowledge_base.py

# 11. 启动协调中心
python -m services.orchestrator.main
```

### 方式二：直接安装依赖（不使用 Conda）

#### Windows 用户

```bash
# 1. 进入项目目录
cd d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装项目（开发模式）
pip install -e .

# 4. 创建必要的目录
mkdir data
mkdir data\chroma_db
mkdir data\wechat_profile
mkdir output
mkdir templates
mkdir logs

# 5. 复制环境变量配置
copy .env.example .env

# 6. 启动 Docker 服务
docker-compose up -d redis ollama

# 7. 拉取 AI 模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 8. 初始化知识库
python scripts/init_knowledge_base.py

# 9. 启动协调中心
python -m services.orchestrator.main
```

#### Linux/Mac 用户

```bash
# 1. 进入项目目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装项目（开发模式）
pip install -e .

# 4. 创建必要的目录
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates
mkdir -p logs

# 5. 复制环境变量配置
cp .env.example .env

# 6. 启动 Docker 服务
docker-compose up -d redis ollama

# 7. 拉取 AI 模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 8. 初始化知识库
python scripts/init_knowledge_base.py

# 9. 启动协调中心
python -m services.orchestrator.main
```

## 环境验证

### 1. 验证 Python 版本

```bash
python --version
# 应该显示: Python 3.12.x
```

### 2. 验证 Conda 环境（如果使用）

```bash
conda env list
# 应该看到 wechat-workflow-agent 环境
```

### 3. 验证依赖安装

```bash
pip list
# 应该看到所有项目依赖
```

### 4. 验证 Docker 服务

```bash
docker ps
# 应该看到 redis 和 ollama 容器在运行

docker-compose ps
# 应该显示所有服务的状态
```

### 5. 验证 Ollama 服务

```bash
curl http://localhost:11434/api/tags
# 应该返回已安装的模型列表

docker exec -it ollama ollama list
# 应该显示 qwen3-vl-8b 和 qwen3-embedding-4b
```

### 6. 验证 Redis 服务

```bash
docker exec -it redis redis-cli ping
# 应该返回 PONG
```

### 7. 验证协调中心 API

```bash
curl http://localhost:8000/
# 应该返回: {"message":"微信工作流Agent协调中心","version":"0.1.0","status":"running"}

curl http://localhost:8000/health
# 应该返回: {"status":"healthy","workflow_loaded":true}
```

## 配置说明

### 环境变量配置

项目使用 `.env` 文件管理环境变量，该文件位于项目根目录。

#### 配置优先级

1. 系统环境变量（最高优先级）
2. `.env` 文件
3. `config/settings.yaml` 文件
4. 代码中的默认值（最低优先级）

#### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PROJECT__NAME` | 项目名称 | wechat-workflow-agent |
| `PROJECT__ENV` | 运行环境 | development |
| `AI__OLLAMA__BASE_URL` | Ollama服务地址 | http://localhost:11434 |
| `AI__OLLAMA__VISION_MODEL` | 视觉模型 | qwen3-vl-8b:latest |
| `AI__OLLAMA__EMBEDDING_MODEL` | 嵌入模型 | qwen3-embedding-4b |
| `REDIS__HOST` | Redis主机地址 | localhost |
| `REDIS__PORT` | Redis端口 | 6379 |
| `REDIS__LOCK_DB` | Redis锁数据库 | 1 |
| `LOGGING__LEVEL` | 日志级别 | INFO |

#### 修改配置

```bash
# Windows
notepad .env

# Linux/Mac
vim .env
```

## 常见问题

### 1. Conda 环境创建失败

**问题：** 执行 `conda create` 时报错

**可能原因：**
- Conda 版本过旧
- 网络连接问题
- 磁盘空间不足

**解决方案：**
```bash
# 更新 conda
conda update conda

# 清理缓存
conda clean --all

# 检查磁盘空间
# Windows: dir
# Linux: df -h

# 重新创建环境
conda create -n wechat-workflow-agent python=3.12
```

### 2. 依赖安装失败

**问题：** `pip install` 时出现依赖冲突或下载失败

**可能原因：**
- 网络问题
- Python 版本不兼容
- pip 版本过旧

**解决方案：**
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源（如果在中国）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 分步安装
pip install -r requirements.txt --no-cache-dir

# 如果仍然失败，尝试逐个安装
pip install fastapi uvicorn pydantic
pip install langgraph langchain
# ... 依次安装其他依赖
```

### 3. Docker 服务启动失败

**问题：** `docker-compose up` 时报错

**可能原因：**
- Docker 未启动
- 端口被占用
- 内存不足

**解决方案：**
```bash
# 检查 Docker 是否运行
docker ps

# 检查端口占用
# Windows: netstat -ano | findstr "6379" | findstr "11434"
# Linux/Mac: lsof -i :6379 -i :11434

# 查看容器日志
docker-compose logs redis
docker-compose logs ollama

# 重启 Docker 服务
# Windows: 在 Docker Desktop 中重启
# Linux: sudo systemctl restart docker
# Mac: 重启 Docker Desktop
```

### 4. Ollama 模型拉取失败

**问题：** `ollama pull` 时下载失败

**可能原因：**
- 网络问题
- Ollama 服务未启动
- 模型名称错误

**解决方案：**
```bash
# 检查 Ollama 服务状态
curl http://localhost:11434/api/tags

# 查看容器日志
docker-compose logs ollama

# 重新拉取模型
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# 如果网络问题，可以尝试使用代理
# 设置 HTTP_PROXY 和 HTTPS_PROXY 环境变量
```

### 5. 环境变量不生效

**问题：** 修改 `.env` 文件后配置未生效

**可能原因：**
- `.env` 文件位置错误
- 配置项名称错误
- 服务未重启

**解决方案：**
```bash
# 确保 .env 文件在项目根目录
# Windows: dir .env
# Linux/Mac: ls -la .env

# 检查配置项名称（注意使用双下划线分隔嵌套配置）
# 正确: AI__OLLAMA__BASE_URL
# 错误: AI_OLLAMA_BASE_URL

# 重启服务
# 停止当前服务（Ctrl+C）并重新启动
```

### 6. 知识库初始化失败

**问题：** `python scripts/init_knowledge_base.py` 报错

**可能原因：**
- 依赖未安装
- Redis 服务未启动
- 配置错误

**解决方案：**
```bash
# 检查依赖安装
pip list | grep chroma

# 检查 Redis 服务
docker exec -it redis redis-cli ping

# 检查配置
cat .env | grep REDIS
cat .env | grep CHROMA

# 重新初始化
python scripts/init_knowledge_base.py
```

### 7. 协调中心启动失败

**问题：** `python -m services.orchestrator.main` 报错

**可能原因：**
- 端口被占用
- 依赖未安装
- 配置错误

**解决方案：**
```bash
# 检查端口占用
# Windows: netstat -ano | findstr "8000"
# Linux/Mac: lsof -i :8000

# 更改端口（修改 .env 文件）
API__PORT=8001

# 检查依赖
pip list | grep fastapi
pip list | grep langgraph

# 查看详细错误信息
python -m services.orchestrator.main
```

## 开发工具使用

### 代码格式化

```bash
# 使用 Black 格式化代码
black .

# 检查格式
black --check .
```

### 代码检查

```bash
# 使用 Ruff 检查代码
ruff check .

# 自动修复
ruff check --fix .
```

### 类型检查

```bash
# 使用 MyPy 进行类型检查
mypy core/
mypy services/
mypy agents/
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_workflow.py

# 运行并显示覆盖率
pytest --cov=core --cov-report=html

# 详细输出
pytest -v
```

## 下一步

环境初始化完成后，你可以：

1. **查看系统架构文档**: 阅读 [docs/agent.md](file:///d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\docs\agent.md) 了解系统架构

2. **测试工作流**: 运行 `python scripts/test_workflow.py` 测试工作流功能

3. **创建文档模板**: 运行 `python scripts/create_excel_template.py` 创建文档模板

4. **启动监控 Agent**: 运行 `python -m agents.monitor_agent` 启动监控 Agent

5. **访问 API**: 打开浏览器访问 http://localhost:8000 查看 API 文档

## 参考文档

- [项目 README](file:///d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\README.md)
- [Agent 系统架构](file:///d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\docs\agent.md)
- [环境配置总结](file:///d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\docs\ENVIRONMENT_INIT_SUMMARY.md)
- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Ollama 文档](https://ollama.ai/docs)
