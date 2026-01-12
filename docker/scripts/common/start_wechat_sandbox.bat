@echo off
REM 微信沙盒容器启动脚本

echo ========================================
echo 微信沙盒容器启动脚本
echo ========================================

REM 设置工作目录
cd /d "%~dp0"
cd ..\..

REM 检查微信安装包是否存在
if not exist "build\WeChatLinux_x86_64.deb" (
    echo [错误] 未找到微信安装包！
    echo 请确保 WeChatLinux_x86_64.deb 文件位于项目 build 目录：
    echo d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\build\WeChatLinux_x86_64.deb
    pause
    exit /b 1
)

REM 创建必要的目录
echo [1/3] 创建媒体和日志目录...
if not exist "services\wechat_sandbox\media" mkdir services\wechat_sandbox\media
if not exist "services\wechat_sandbox\logs" mkdir services\wechat_sandbox\logs

REM 构建并启动容器
echo [2/3] 构建并启动微信沙盒容器...
docker build -f docker\sandbox\Dockerfile -t wechat_sandbox:latest .

if errorlevel 1 (
    echo [错误] 容器构建失败！
    pause
    exit /b 1
)

echo [3/3] 启动容器...
docker run -d --name wechat_sandbox ^
    --privileged ^
    -p 6080:6080 ^
    -p 5900:5900 ^
    -v services\wechat_sandbox\media:/app/media ^
    -v services\wechat_sandbox\logs:/app/logs ^
    -e DISPLAY=:99 ^
    wechat_sandbox:latest

if errorlevel 1 (
    echo [错误] 容器启动失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 微信沙盒容器启动成功！
echo ========================================
echo.
echo 访问方式：
echo   浏览器访问：http://localhost:6080/vnc.html
echo   VNC 密码：wechat123
echo.
echo 查看日志：
echo   docker logs -f wechat_sandbox
echo.
echo 停止容器：
echo   docker stop wechat_sandbox
echo   docker rm wechat_sandbox
echo.
echo ========================================

pause
