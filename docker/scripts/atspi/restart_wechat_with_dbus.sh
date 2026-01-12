#!/bin/bash
# 重新启动微信，确保在正确的DBus会话中

killall -9 wechat wxocr wxplayer wxutility 2>/dev/null
sleep 2

export DISPLAY=:99
export QT_ACCESSIBILITY=1
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export GNOME_ACCESSIBILITY=1
export DBUS_SESSION_BUS_ADDRESS=unix:path=/root/.cache/at-spi/bus_99

echo "重新启动微信（使用DBus会话）..."
echo "DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"

# 在同一shell中启动微信，确保继承所有环境变量
DBUS_SESSION_BUS_ADDRESS=unix:path=/root/.cache/at-spi/bus_99 \
QT_ACCESSIBILITY=1 \
QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 \
/opt/wechat/wechat > /tmp/wechat_new.log 2>&1 &

WECHAT_PID=$!
sleep 3

echo "微信PID: $WECHAT_PID"

# 检查微信是否运行
if ps -p $WECHAT_PID > /dev/null 2>&1; then
    echo "✅ 微信正在运行"

    # 验证环境变量
    echo "检查微信的DBus环境变量:"
    cat /proc/$WECHAT_PID/environ 2>/dev/null | tr '\0' '\n' | grep DBUS_SESSION_BUS_ADDRESS

    if [ $? -eq 0 ]; then
        echo "✅ 微信已连接到DBus会话"
    else
        echo "❌ 微信没有DBus会话环境变量"
    fi
else
    echo "❌ 微信启动失败"
    exit 1
fi
