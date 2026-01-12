@echo off
REM 微信沙盒快速测试脚本
REM 用法: quick_test.bat [test_type]
REM   test_type: basic | full | performance

setlocal enabledelayedexpansion

REM 设置Python路径（如果需要）
set PYTHON_CMD=python

REM 解析参数
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=basic

echo ╔════════════════════════════════════════════════════════════╗
echo ║          微信沙盒快速测试工具                              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 检查Redis连接
echo [1/5] 检查Redis连接...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis未运行，请先启动Redis
    pause
    exit /b 1
)
echo ✅ Redis已运行
echo.

REM 检查服务是否启动
echo [2/5] 检查微信沙盒服务...
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  微信沙盒服务未启动
    echo    请先运行: cd services/wechat_sandbox && python main.py
    echo.
    choice /C YN /M "是否继续测试"
    if errorlevel 2 exit /b 0
)
echo ✅ 服务检查完成
echo.

REM 根据测试类型执行不同测试
if /i "%TEST_TYPE%"=="basic" goto :basic_test
if /i "%TEST_TYPE%"=="full" goto :full_test
if /i "%TEST_TYPE%"=="performance" goto :performance_test
if /i "%TEST_TYPE%"=="monitor" goto :monitor_only

:basic_test
echo ════════════════════════════════════════════════════════════
echo  运行基础测试
echo ════════════════════════════════════════════════════════════
echo.
echo 启动SSE客户端...
echo 请在微信群中发送测试消息
echo.
echo 提示:
echo   - 发送几条文本消息
echo   - 发送一张图片
echo   - 发送一个视频
echo   - 按Ctrl+C停止测试
echo.
pause

%PYTHON_CMD% "%~dp0sse_client.py" --verbose --save-json
goto :end

:full_test
echo ════════════════════════════════════════════════════════════
echo  运行完整测试套件
echo ════════════════════════════════════════════════════════════
echo.

echo [测试1/5] 队列状态检查...
%PYTHON_CMD% "%~dp0queue_monitor.py" --host localhost --port 6379
echo.
pause

echo [测试2/5] SSE基础连接测试...
echo 请发送5条测试消息...
%PYTHON_CMD% "%~dp0sse_client.py" --client-id full_test_1
echo.
pause

echo [测试3/5] 并发连接测试...
echo 启动3个并发客户端，请发送10条消息...
start "SSE Client 1" %PYTHON_CMD% "%~dp0sse_client.py" --client-id concurrent_1 --save-json
start "SSE Client 2" %PYTHON_CMD% "%~dp0sse_client.py" --client-id concurrent_2 --save-json
start "SSE Client 3" %PYTHON_CMD% "%~dp0sse_client.py" --client-id concurrent_3 --save-json
echo 等待30秒...
timeout /t 30
taskkill /FI "WINDOWTITLE eq SSE Client*" /F >nul 2>&1
echo.
pause

echo [测试4/5] 性能测试...
echo 请连续发送至少20条消息，测试将运行60秒...
%PYTHON_CMD% "%~dp0sse_performance_test.py" --duration 60 --benchmark
echo.
pause

echo [测试5/5] 数据导出和分析...
%PYTHON_CMD% "%~dp0queue_monitor.py" --analyze
%PYTHON_CMD% "%~dp0queue_monitor.py" --export --output "%~dp0test_results\queue_export_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.json"
echo.

echo ════════════════════════════════════════════════════════════
echo  完整测试结束！
echo ════════════════════════════════════════════════════════════
goto :end

:performance_test
echo ════════════════════════════════════════════════════════════
echo  运行性能测试
echo ════════════════════════════════════════════════════════════
echo.
echo 性能测试将运行2分钟
echo 请在此期间持续发送消息（建议至少50条）
echo.
pause

%PYTHON_CMD% "%~dp0sse_performance_test.py" --duration 120 --benchmark
goto :end

:monitor_only
echo ════════════════════════════════════════════════════════════
echo  启动队列监控
echo ════════════════════════════════════════════════════════════
echo.
echo 按 Ctrl+C 停止监控
echo.

%PYTHON_CMD% "%~dp0queue_monitor.py"
goto :end

:end
echo.
echo ════════════════════════════════════════════════════════════
echo  测试完成
echo ════════════════════════════════════════════════════════════
echo.
echo 测试结果保存在: %~dp0test_results\
echo.
pause
