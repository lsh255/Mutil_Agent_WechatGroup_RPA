@echo off
REM 微信沙盒容器启动脚本

echo ========================================
echo 微信沙盒容器启动脚本
echo ========================================

REM 设置工作目录
cd /d "%~dp0"

REM 检查微信安装包是否存在
if not exist "..\..\WeChatLinux_x86_64.deb" (
    echo [错误] 未找到微信安装包！
    echo 请确保 WeChatLinux_x86_64.deb 文件位于项目根目录：
    echo d:\AI\Trae\Mutil_Agent_WechatGroup_RPA\Mutil_Agent_WechatGroup_RPA\WeChatLinux_x86_64.deb
    pause
    exit /b 1
)

REM 复制微信安装包到当前目录
echo [1/3] 复制微信安装包到构建目录...
copy "..\..\WeChatLinux_x86_64.deb" ".\WeChatLinux_x86_64.deb" /Y
if errorlevel 1 (
    echo [错误] 复制微信安装包失败！
    pause
    exit /b 1
)

REM 创建必要的目录
echo [2/3] 创建媒体和日志目录...
if not exist "media" mkdir media
if not exist "logs" mkdir logs

REM 构建并启动容器
echo [3/3] 构建并启动微信沙盒容器...
docker-compose -f docker-compose.wechat.yml up -d --build

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
echo   docker-compose -f docker-compose.wechat.yml logs -f
echo.
echo 停止容器：
echo   docker-compose -f docker-compose.wechat.yml down
echo.
echo ========================================

pause
