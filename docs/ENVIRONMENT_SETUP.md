# 环境配置说明

## 概述

本项目提供了完整的环境配置方案，支持Conda虚拟环境和直接安装两种方式。

## 配置文件说明

### 1. `.env` 文件

环境变量配置文件，用于覆盖 `config/settings.yaml` 中的默认配置。

**主要配置项：**

- `PROJECT__NAME`: 项目名称
- `PROJECT__ENV`: 运行环境（development/production）
- `AI__OLLAMA__BASE_URL`: Ollama服务地址
- `REDIS__HOST`: Redis主机地址
- `REDIS__PORT`: Redis端口

**使用方式：**
```bash
# 直接使用.env文件（自动加载）
python scripts/start_all.py

# 或手动设置环境变量
export PROJECT__ENV=production
python scripts/start_all.py
```

### 2. `environment.yml` 文件

Conda环境配置文件，定义了项目的所有Python依赖。

**主要依赖：**
- Python 3.12
- FastAPI、Uvicorn（Web框架）
- LangGraph、LangChain（AI框架）
- Ollama（AI模型服务）
- Chroma（向量数据库）
- Redis（缓存）
- openpyxl、python-docx（文档处理）

### 3. `.env.example` 文件

环境变量配置示例文件，用于创建实际的 `.env` 文件。

## 快速开始

### Windows用户

#### 使用Conda环境（推荐）

```bash
# 1. 运行环境设置脚本
scripts\setup_conda_env.bat

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 启动服务
docker-compose up -d redis ollama
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

#### 直接安装依赖

```bash
# 1. 安装依赖
pip install -e .

# 2. 启动服务
docker-compose up -d redis ollama
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

### Linux/Mac用户

#### 使用Conda环境（推荐）

```bash
# 1. 运行环境设置脚本
chmod +x scripts/setup_conda_env.sh
./scripts/setup_conda_env.sh

# 2. 激活环境
conda activate wechat-workflow-agent

# 3. 启动服务
docker-compose up -d redis ollama
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

#### 直接安装依赖

```bash
# 1. 安装依赖
pip install -e .

# 2. 启动服务
docker-compose up -d redis ollama
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
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
export REDIS__HOST=192.168.1.100

# 即使.env中配置了localhost，也会使用192.168.1.100
```

## 常见问题

### 1. Conda环境创建失败

**问题：** 执行 `conda env create` 时报错

**解决方案：**
```bash
# 更新conda
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
# 使用conda安装系统依赖
conda install -c conda-forge python=3.12

# 使用pip安装Python包
pip install -e . --no-deps
pip install -r requirements.txt
```

### 3. Docker服务启动失败

**问题：** docker-compose up 时报错

**解决方案：**
```bash
# 检查Docker是否运行
docker ps

# 检查端口是否被占用
netstat -ano | findstr "6379"
netstat -ano | findstr "11434"

# 修改.env文件中的端口配置
REDIS__PORT=6380
```

### 4. 环境变量不生效

**问题：** 修改.env文件后配置未生效

**解决方案：**
```bash
# 确保.env文件在项目根目录
ls -la .env

# 检查文件格式（Windows下可能是CRLF）
file .env

# 重启服务
# 环境变量只在服务启动时加载
```

## 生产环境配置

### 1. 创建生产环境配置

```bash
# 复制示例文件
cp .env.example .env.production

# 修改配置
vim .env.production
```

### 2. 关键配置项

```bash
# 运行环境
PROJECT__ENV=production

# 日志级别
LOGGING__LEVEL=WARNING

# Redis地址（生产环境）
REDIS__HOST=redis.production.example.com
REDIS__PORT=6379

# Ollama地址（生产环境）
AI__OLLAMA__BASE_URL=http://ollama.production.example.com:11434
```

### 3. 启动生产服务

```bash
# 加载生产环境配置
export $(cat .env.production | xargs)

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
uvicorn services.orchestrator.main:app --host 0.0.0.0 --port 8000
```

## 开发工具

### 代码格式化

```bash
# 使用black格式化代码
black .

# 使用ruff检查代码
ruff check .
```

### 类型检查

```bash
# 使用mypy进行类型检查
mypy core/
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
   ```bash
   # 不要在代码中硬编码
   API_KEY="sk-xxx"  # 错误
   
   # 使用环境变量
   API_KEY=os.getenv("API_KEY")  # 正确
   ```

3. **定期更新依赖**
   ```bash
   # 检查过时的依赖
   pip list --outdated
   
   # 更新依赖
   pip install --upgrade -r requirements.txt
   ```

## 参考资源

- [Conda文档](https://docs.conda.io/)
- [Pydantic Settings文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [LangGraph文档](https://langchain-ai.github.io/langgraph/)
