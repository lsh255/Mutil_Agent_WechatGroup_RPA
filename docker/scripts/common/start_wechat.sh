#!/bin/bash

set -e

echo "========================================="
echo "Starting WeChat Sandbox with VNC..."
echo "========================================="

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true
echo "Cleaned up Xvfb lock files"

Xvfb :99 -screen 0 1920x1080x24 &
echo "[1/5] Xvfb started on DISPLAY :99"

sleep 3

fluxbox -display :99 &
echo "[2/5] Fluxbox window manager started"

sleep 2

if [ ! -f /root/.vnc/passwd ]; then
    echo "Setting VNC password..."
    echo "wechat123" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
fi

x11vnc -display :99 -rfbport 5900 -forever -shared -rfbauth /root/.vnc/passwd &
echo "[3/5] x11vnc started on port 5900 (password: wechat123)"

sleep 2

cd /usr/share/novnc
websockify --web=/usr/share/novnc 6080 localhost:5900 &
echo "[4/5] noVNC started on port 6080"

sleep 2

cd /app

echo "[5/5] Starting WeChat application..."
QT_ACCESSIBILITY=1 /opt/wechat/wechat &
echo "WeChat application launched (QT_ACCESSIBILITY enabled)"

sleep 2

echo "[6/6] Starting FastAPI server..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 &
echo "FastAPI server started on port 8000"

echo "========================================="
echo "WeChat Sandbox is ready!"
echo "========================================="
echo "Access WeChat via browser:"
echo "  URL: http://localhost:6080/vnc.html"
echo "  VNC Password: wechat123"
echo "========================================="
echo "Access FastAPI API:"
echo "  URL: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "========================================="
echo "To access via VNC client:"
echo "  Host: localhost"
echo "  Port: 5900"
echo "  Password: wechat123"
echo "========================================="
echo "Press Ctrl+C to stop the container"
echo "========================================="

tail -f /dev/null
