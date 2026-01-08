@echo off
REM ========================================
REM 创建并激活Conda虚拟环境
REM ========================================

echo ========================================
echo 多模态Agent微信群自动化项目
echo Conda环境设置脚本
echo ========================================
echo.

REM 检查conda是否安装
conda --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Conda，请先安装Anaconda或Miniconda
    pause
    exit /b 1
)

echo [1/4] 检查现有环境...
conda env list | findstr /C:"wechat-workflow-agent" >nul
if %errorlevel% equ 0 (
    echo [信息] 环境已存在，将更新依赖
    conda env update -f environment.yml
) else (
    echo [信息] 创建新环境...
    conda env create -f environment.yml
)

if %errorlevel% neq 0 (
    echo [错误] 环境创建失败
    pause
    exit /b 1
)

echo [完成] Conda环境创建成功
echo.

echo [2/4] 激活环境...
call conda activate wechat-workflow-agent

if %errorlevel% neq 0 (
    echo [错误] 环境激活失败
    pause
    exit /b 1
)

echo [完成] 环境已激活
echo.

echo [3/4] 创建必要的目录...
if not exist "data" mkdir data
if not exist "data\chroma_db" mkdir data\chroma_db
if not exist "data\wechat_profile" mkdir data\wechat_profile
if not exist "output" mkdir output
if not exist "templates" mkdir templates
if not exist "logs" mkdir logs

echo [完成] 目录创建成功
echo.

echo [4/4] 安装项目依赖...
pip install -e . -q

if %errorlevel% neq 0 (
    echo [警告] 依赖安装可能有问题，但可以继续
) else (
    echo [完成] 依赖安装成功
)

echo.
echo ========================================
echo 环境设置完成！
echo ========================================
echo.
echo 使用以下命令激活环境：
echo   conda activate wechat-workflow-agent
echo.
echo 使用以下命令启动服务：
echo   python scripts\quick_start.bat
echo.
pause
