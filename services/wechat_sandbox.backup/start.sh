#!/bin/bash

set -e  # 遇到错误立即退出

echo "Starting WeChat Producer Service with VNC..."  # 输出启动信息

# 启动Xvfb虚拟显示器
Xvfb :99 -screen 0 1920x1080x24 &  # 启动Xvfb虚拟显示器，分辨率为1920x1080，色深24位
echo "Xvfb started on DISPLAY :99"  # 输出Xvfb启动信息

# 等待Xvfb启动
sleep 2  # 等待2秒确保Xvfb启动完成

# 启动Fluxbox窗口管理器
fluxbox -display :99 &  # 启动Fluxbox窗口管理器
echo "Fluxbox started"  # 输出Fluxbox启动信息

# 等待窗口管理器启动
sleep 2  # 等待2秒确保窗口管理器启动完成

# 启动VNC服务器（设置密码）
if [ ! -f /root/.vnc/passwd ]; then  # 检查VNC密码文件是否存在
    echo "Setting VNC password..."  # 输出设置密码提示
    echo "vnc123" | vncpasswd -f > /root/.vnc/passwd  # 设置VNC密码为vnc123
    chmod 600 /root/.vnc/passwd  # 设置密码文件权限为仅所有者可读写
fi

# 启动x11vnc
x11vnc -display :99 -rfbport 5900 -forever -shared -nopwfb -rfbauth /root/.vnc/passwd &  # 启动x11vnc服务器
echo "x11vnc started on port 5900"  # 输出x11vnc启动信息

# 启动noVNC
cd /usr/share/novnc  # 切换到noVNC目录
websockify --web=/usr/share/novnc 6080 localhost:5900 &  # 启动websockify代理VNC连接
echo "noVNC started on port 6080"  # 输出noVNC启动信息

# 返回工作目录
cd /app  # 切换到应用目录

echo "Starting FastAPI and Producer services..."  # 输出启动服务提示
python start_service.py  # 启动FastAPI和Producer服务
