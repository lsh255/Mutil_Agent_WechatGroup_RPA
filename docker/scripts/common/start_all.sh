#!/bin/bash

set -e

export DISPLAY=:99

echo "========================================="
echo "Starting WeChat Sandbox with Accerciser..."
echo "========================================="

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null || true
echo "Cleaned up Xvfb lock files"

Xvfb :99 -screen 0 1920x1080x24 &
echo "[1/7] Xvfb started on DISPLAY :99"

sleep 3

fluxbox -display :99 &
echo "[2/7] Fluxbox window manager started"

sleep 2

if [ ! -f /root/.vnc/passwd ]; then
    echo "Setting VNC password..."
    echo "wechat123" | vncpasswd -f > /root/.vnc/passwd
    chmod 600 /root/.vnc/passwd
fi

x11vnc -display :99 -rfbport 5900 -forever -shared -rfbauth /root/.vnc/passwd &
echo "[3/7] x11vnc started on port 5900 (password: wechat123)"

sleep 2

cd /usr/share/novnc
websockify --web=/usr/share/novnc 6080 localhost:5900 &
echo "[4/7] noVNC started on port 6080"

sleep 2

cd /app

echo "Setting up AT-SPI environment..."

export GNOME_ACCESSIBILITY=1
export QT_ACCESSIBILITY=1
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export AT_SPI_BUS_ADDRESS=""

echo "Starting DBus session..."
# 启动 D-Bus 会话并导出地址，所有AT-SPI应用都需要使用同一个会话
eval $(dbus-launch --sh-syntax)
export DBUS_SESSION_BUS_ADDRESS
echo "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"

# 将 D-Bus 地址保存到文件，供后续进程使用
echo "$DBUS_SESSION_BUS_ADDRESS" > /tmp/dbus_session_address

sleep 2

echo "[5/7] Starting AT-SPI service..."
# 确保使用统一的 D-Bus 会话
if [ -f /tmp/dbus_session_address ]; then
    export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/dbus_session_address)
    echo "Using D-Bus session: $DBUS_SESSION_BUS_ADDRESS"
fi

/usr/libexec/at-spi-bus-launcher --launch-immediately > /tmp/atspi.log 2>&1 &
ATSPI_PID=$!
sleep 3

if ! ps -p $ATSPI_PID > /dev/null; then
    echo "Failed to start AT-SPI bus launcher"
    echo "AT-SPI log:"
    cat /tmp/atspi.log
    exit 1
fi

echo "AT-SPI started with PID: $ATSPI_PID"

sleep 2

echo "[6/7] Starting FastAPI service..."
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &
FASTAPI_PID=$!
sleep 3

if ! ps -p $FASTAPI_PID > /dev/null; then
    echo "Failed to start FastAPI"
    echo "FastAPI log:"
    cat /tmp/fastapi.log
    exit 1
fi
echo "FastAPI started with PID: $FASTAPI_PID"

sleep 2

echo "[7/7] Starting WeChat application with AT-SPI enabled..."
# 确保微信使用统一的 D-Bus 会话
if [ -f /tmp/dbus_session_address ]; then
    export DBUS_SESSION_BUS_ADDRESS=$(cat /tmp/dbus_session_address)
fi

QT_ACCESSIBILITY=1 QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 /opt/wechat/wechat > /tmp/wechat.log 2>&1 &
WECHAT_PID=$!
sleep 5

if ! ps -p $WECHAT_PID > /dev/null; then
    echo "Failed to start WeChat"
    echo "WeChat log:"
    cat /tmp/wechat.log
    exit 1
fi
echo "WeChat started with PID: $WECHAT_PID"

sleep 2

echo "========================================="
echo "重要提示：微信需要扫码登录"
echo "========================================="
echo "请在浏览器中访问 noVNC 界面查看二维码："
echo "http://localhost:6080/vnc.html"
echo "或直接在 noVNC 界面中扫描二维码登录"
echo "========================================="
echo ""

echo "Waiting for WeChat to fully initialize..."
sleep 5

echo "Starting Accerciser..."
accerciser > /tmp/accerciser.log 2>&1 &
ACERCISER_PID=$!
sleep 2

if ! ps -p $ACERCISER_PID > /dev/null; then
    echo "Failed to start Accerciser"
    echo "Accerciser log:"
    cat /tmp/accerciser.log
    exit 1
fi

echo "Accerciser started with PID: $ACERCISER_PID"

echo "========================================="
echo "All services started successfully!"
echo "========================================="
echo "AT-SPI Environment:"
echo "  GNOME_ACCESSIBILITY=$GNOME_ACCESSIBILITY"
echo "  QT_ACCESSIBILITY=$QT_ACCESSIBILITY"
echo "  QT_LINUX_ACCESSIBILITY_ALWAYS_ON=$QT_LINUX_ACCESSIBILITY_ALWAYS_ON"
echo "========================================="
echo "Access WeChat/Accerciser via browser:"
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
