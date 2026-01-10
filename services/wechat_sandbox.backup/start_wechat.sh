#!/bin/bash

set -e  # 遇到错误立即退出

echo "========================================="
echo "Starting WeChat Sandbox with VNC..."
echo "========================================="

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true  # 清理Xvfb残留的锁文件
echo "Cleaned up Xvfb lock files"  # 输出清理锁文件信息

Xvfb :99 -screen 0 1920x1080x24 &  # 启动Xvfb虚拟显示器，分辨率为1920x1080，色深24位
echo "[1/5] Xvfb started on DISPLAY :99"  # 输出Xvfb启动信息

sleep 3  # 等待3秒确保Xvfb启动完成

fluxbox -display :99 &  # 启动Fluxbox窗口管理器
echo "[2/5] Fluxbox window manager started"  # 输出Fluxbox启动信息

sleep 2  # 等待2秒确保窗口管理器启动完成

if [ ! -f /root/.vnc/passwd ]; then  # 检查VNC密码文件是否存在
    echo "Setting VNC password..."  # 输出设置密码提示
    echo "wechat123" | vncpasswd -f > /root/.vnc/passwd  # 设置VNC密码为wechat123
    chmod 600 /root/.vnc/passwd  # 设置密码文件权限为仅所有者可读写
fi

x11vnc -display :99 -rfbport 5900 -forever -shared -rfbauth /root/.vnc/passwd &  # 启动x11vnc服务器
echo "[3/5] x11vnc started on port 5900 (password: wechat123)"  # 输出x11vnc启动信息

sleep 2  # 等待2秒确保x11vnc启动完成

cd /usr/share/novnc  # 切换到noVNC目录
websockify --web=/usr/share/novnc 6080 localhost:5900 &  # 启动websockify代理VNC连接
echo "[4/5] noVNC started on port 6080"  # 输出noVNC启动信息

sleep 2  # 等待2秒确保noVNC启动完成

cd /app  # 切换到应用目录

echo "[5/5] Starting WeChat application..."  # 输出启动微信提示
/opt/wechat/wechat &  # 启动微信应用
echo "WeChat application launched"  # 输出微信启动信息

sleep 2  # 等待2秒确保微信启动完成

echo "[6/6] Starting FastAPI server..."  # 输出启动FastAPI提示
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &  # 启动FastAPI服务器
echo "FastAPI server started on port 8000"  # 输出FastAPI启动信息

echo "========================================="
echo "WeChat Sandbox is ready!"  # 输出服务就绪信息
echo "========================================="
echo "Access WeChat via browser:"  # 输出浏览器访问说明
echo "  URL: http://localhost:6080/vnc.html"  # noVNC访问地址
echo "  VNC Password: wechat123"  # VNC密码
echo "========================================="
echo "Access FastAPI API:"  # 输出API访问说明
echo "  URL: http://localhost:8000"  # FastAPI地址
echo "  Docs: http://localhost:8000/docs"  # API文档地址
echo "========================================="
echo "To access via VNC client:"  # 输出VNC客户端访问说明
echo "  Host: localhost"  # VNC主机
echo "  Port: 5900"  # VNC端口
echo "  Password: wechat123"  # VNC密码
echo "========================================="
echo "Press Ctrl+C to stop the container"  # 输出停止说明
echo "========================================="

tail -f /dev/null  # 保持容器运行
