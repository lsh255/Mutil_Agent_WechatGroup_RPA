#!/bin/bash

set -e

echo "Starting WeChat Producer Service with VNC..."

# 启动Xvfb虚拟显示器
Xvfb :99 -screen 0 1920x1080x24 &
echo "Xvfb started on DISPLAY :99"

# 等待Xvfb启动
sleep 2

# 启动Fluxbox窗口管理器
fluxbox -display :99 &
echo "Fluxbox started"

# 等待窗口管理器启动
sleep 2

# 启动VNC服务器（设置密码）
if [ ! -f /root/.vnc/passwd ]; then
    echo "Setting VNC password..."
    echo "vnc123" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
fi

# 启动x11vnc
x11vnc -display :99 -rfbport 5900 -forever -shared -nopwfb -rfbauth /root/.vnc/passwd &
echo "x11vnc started on port 5900"

# 启动noVNC
cd /usr/share/novnc
websockify --web=/usr/share/novnc 6080 localhost:5900 &
echo "noVNC started on port 6080"

# 返回工作目录
cd /app

echo "Starting FastAPI and Producer services..."
python start_service.py
