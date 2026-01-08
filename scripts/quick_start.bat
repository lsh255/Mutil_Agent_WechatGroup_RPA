@echo off
REM 快速启动脚本 - Windows版本

echo ========================================
echo 多模态Agent微信群自动化项目
echo 快速启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.12+
    pause
    exit /b 1
)

echo [1/6] 检查Docker是否运行...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)
echo [完成] Docker运行正常
echo.

echo [2/6] 安装Python依赖...
pip install -e . -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [完成] 依赖安装成功
echo.

echo [3/6] 启动基础设施服务（Redis和Ollama）...
docker-compose up -d redis ollama
if %errorlevel% neq 0 (
    echo [错误] 基础设施启动失败
    pause
    exit /b 1
)
echo [完成] 基础设施启动成功
echo.

echo [4/6] 创建必要的目录和模板...
if not exist "data" mkdir data
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\wechat_profile" mkdir data\wechat_profile
if not exist "output" mkdir output
if not exist "templates" mkdir templates

python scripts\create_excel_template.py
echo [完成] 目录和模板创建成功
echo.

echo [5/6] 初始化知识库...
python scripts\init_knowledge_base.py
if %errorlevel% neq 0 (
    echo [警告] 知识库初始化失败，但可以继续
)
echo [完成] 知识库初始化完成
echo.

echo [6/6] 启动协调中心服务...
echo 提示：协调中心将在 http://localhost:8000 启动
echo 按 Ctrl+C 可以停止服务
echo.
uvicorn services.orchestrator.main:app --host 0.0.0.0 --port 8000 --reload

pause
