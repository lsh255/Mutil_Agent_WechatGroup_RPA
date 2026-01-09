# 环境配置说明

## 概述

本项目提供了完整的环境配置方案，支持 Conda 虚拟环境和直接安装两种方式。详细的环境初始化步骤请参考 [环境初始化指南](ENVIRONMENT_INIT.md)。

## 配置文件说明

### 1. `.env` 文件

环境变量配置文件，用于覆盖 `config/settings.yaml` 中的默认配置。

**主要配置项：**

- `PROJECT__NAME`: 项目名称
- `PROJECT__ENV`: 运行环境（development/production）
- `AI__OLLAMA__BASE_URL`: Ollama服务地址
- `AI__OLLAMA__VISION_MODEL`: 视觉模型名称
- `AI__OLLAMA__EMBEDDING_MODEL`: 嵌入模型名称
- `REDIS__HOST`: Redis主机地址
- `REDIS__PORT`: Redis端口
- `LOGGING__LEVEL`: 日志级别

**使用方式：**
```bash
# 复制示例文件
# Windows: copy .env.example .env
# Linux/Mac: cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# Linux/Mac: vim .env

# 配置会自动加载，无需额外操作
```

### 2. `requirements.txt` 文件

Python 依赖清单文件，包含所有必需的 Python 包。

**主要依赖：**

- Python 3.12+
- FastAPI、Uvicorn（Web框架）
- LangGraph、LangChain（AI框架）
- Redis（缓存）
- openpyxl、python-docx（文档处理）
- Docker（容器管理）
- Pillow、OpenCV（图像处理）
- Structlog（日志）
- PyYAML（配置管理）

**安装方式：**
```bash
# 安装所有依赖
pip install -r requirements.txt

# 或安装项目（开发模式）
pip install -e .
```

### 3. `environment.yml` 文件

Conda 环境配置文件，定义了项目的所有 Python 依赖。

**主要依赖：**

- Python 3.12
- FastAPI、Uvicorn（Web框架）
- LangGraph、LangChain（AI框架）
- Ollama（AI模型服务）
- Chroma（向量数据库）
- Redis（缓存）
- openpyxl、python-docx（文档处理）
- 开发工具（pytest、black、ruff、mypy）

**使用方式：**
```bash
# 创建 Conda 环境
conda env create -f environment.yml

# 激活环境
conda activate wechat-workflow-agent

# 更新环境
conda env update -f environment.yml --prune
```

### 4. `.env.example` 文件

环境变量配置示例文件，用于创建实际的 `.env` 文件。

**使用方式：**
```bash
# 复制示例文件
# Windows: copy .env.example .env
# Linux/Mac: cp .env.example .env

# 根据实际情况修改配置
# Windows: notepad .env
# Linux/Mac: vim .env
```

## 快速开始

详细的快速开始步骤请参考 [环境初始化指南](ENVIRONMENT_INIT.md)。

### Windows 用户

#### 使用 Conda 环境（推荐）

```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建必要的目录
mkdir data
mkdir data\chroma_db
mkdir data\wechat_profile
mkdir output
mkdir templates
mkdir logs

# 6. 复制环境变量配置
copy .env.example .env

# 7. 启动服务
docker-compose up -d redis ollama
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
python -m services.orchestrator.main
```

#### 直接安装依赖

```bash
# 1. 进入项目目录
cd d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建必要的目录
mkdir data
mkdir data\chroma_db
mkdir data\wechat_profile
mkdir output
mkdir templates
mkdir logs

# 4. 复制环境变量配置
copy .env.example .env

# 5. 启动服务
docker-compose up -d redis ollama
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
python -m services.orchestrator.main
```

### Linux/Mac 用户

#### 使用 Conda 环境（推荐）

```bash
# 1. 创建 Conda 环境
conda create -n wechat-workflow-agent python=3.12

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 进入项目目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 4. 安装依赖
pip install -r requirements.txt

# 5. 创建必要的目录
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates
mkdir -p logs

# 6. 复制环境变量配置
cp .env.example .env

# 7. 启动服务
docker-compose up -d redis ollama
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
python -m services.orchestrator.main
```

#### 直接安装依赖

```bash
# 1. 进入项目目录
cd /path/to/Mutil_Agent_WechatGroup_RPA

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建必要的目录
mkdir -p data/chroma_db
mkdir -p data/wechat_profile
mkdir -p output
mkdir -p templates
mkdir -p logs

# 4. 复制环境变量配置
cp .env.example .env

# 5. 启动服务
docker-compose up -d redis ollama
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
python -m services.orchestrator.main
```

## 环境变量优先级

配置加载优先级（从高到低）：

1. 系统环境变量
2. `.env` 文件
3. `config/settings.yaml` 文件
4. 代码中的默认值

**示例：**
```bash
# 系统环境变量优先级最高
# Windows: set REDIS__HOST=192.168.1.100
# Linux/Mac: export REDIS__HOST=192.168.1.100

# 即使 .env 中配置了 localhost，也会使用 192.168.1.100
```

## 配置项详解

### 项目配置

```bash
PROJECT__NAME=wechat-workflow-agent
PROJECT__ENV=development  # development/production
```

### AI 模型配置

```bash
AI__OLLAMA__BASE_URL=http://localhost:11434
AI__OLLAMA__VISION_MODEL=qwen3-vl-8b:latest
AI__OLLAMA__EMBEDDING_MODEL=qwen3-embedding-4b
AI__OLLAMA__CHAT_MODEL=qwen3-72b:latest
```

### Redis 配置

```bash
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__LOCK_DB=1
REDIS__CACHE_DB=0
```

### Chroma 配置

```bash
CHROMA__PERSIST_DIRECTORY=data/chroma_db
CHROMA__COLLECTION_NAME=wechat_messages
```

### 日志配置

```bash
LOGGING__LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR/CRITICAL
LOGGING__FORMAT=json  # json/text
```

### FastAPI 配置

```bash
API__HOST=0.0.0.0
API__PORT=8000
API__RELOAD=true
```

## 常见问题

详细的常见问题解决方案请参考 [环境初始化指南 - 常见问题](ENVIRONMENT_INIT.md#常见问题)。

### 1. Conda 环境创建失败

**问题：** 执行 `conda env create` 时报错

**解决方案：**
```bash
# 更新 conda
conda update conda

# 清理缓存
conda clean --all

# 重新创建环境
conda env create -f environment.yml
```

### 2. 依赖安装失败

**问题：** pip install 时出现依赖冲突

**解决方案：**
```bash
# 使用国内镜像源（如果在中国）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 分步安装
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 3. Docker 服务启动失败

**问题：** docker-compose up 时报错

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
```

### 4. 环境变量不生效

**问题：** 修改 .env 文件后配置未生效

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

## 生产环境配置

### 1. 创建生产环境配置

```bash
# 复制示例文件
# Windows: copy .env.example .env.production
# Linux/Mac: cp .env.example .env.production

# 修改配置
# Windows: notepad .env.production
# Linux/Mac: vim .env.production
```

### 2. 关键配置项

```bash
# 运行环境
PROJECT__ENV=production

# 日志级别
LOGGING__LEVEL=WARNING

# Redis 地址（生产环境）
REDIS__HOST=redis.production.example.com
REDIS__PORT=6379

# Ollama 地址（生产环境）
AI__OLLAMA__BASE_URL=http://ollama.production.example.com:11434
```

### 3. 启动生产服务

```bash
# 加载生产环境配置
# Linux/Mac:
export $(cat .env.production | xargs)

# Windows PowerShell:
Get-Content .env.production | ForEach-Object { $var = $_.Split('='); [System.Environment]::SetEnvironmentVariable($var[0], $var[1]) }

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
uvicorn services.orchestrator.main:app --host 0.0.0.0 --port 8000
```

## 开发工具

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

# 运行特定测试
pytest tests/test_workflow.py

# 生成覆盖率报告
pytest --cov=core --cov-report=html
```

## 安全注意事项

1. **不要提交敏感信息**
   - `.env` 文件已在 `.gitignore` 中
   - 使用 `.env.example` 作为模板
   - 生产环境配置单独管理

2. **使用环境变量管理密钥**
   ```python
   # 错误：硬编码密钥
   API_KEY = "sk-xxxxxxxxxxxxxxxxxxxx"

   # 正确：使用环境变量
   import os
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       api_key: str = os.getenv("API_KEY")

   settings = Settings()
   ```

3. **定期更新依赖**
   ```bash
   # 检查过时的依赖
   pip list --outdated

   # 更新依赖
   pip install --upgrade -r requirements.txt
   ```

## 参考资源

- [环境初始化指南](ENVIRONMENT_INIT.md) - 详细的环境初始化步骤
- [Agent 系统架构](agent.md) - 系统架构和组件说明
- [环境配置总结](ENVIRONMENT_INIT_SUMMARY.md) - 环境配置完成总结
- [Conda 文档](https://docs.conda.io/)
- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
