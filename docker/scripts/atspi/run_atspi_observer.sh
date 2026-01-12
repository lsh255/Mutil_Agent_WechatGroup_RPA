#!/bin/bash
# =====================================================
# AT-SPI观察者启动脚本
# =====================================================
# 功能：在正确的DBus会话中运行AT-SPI观察者
# 关键：获取并使用正确的DBUS_SESSION_BUS_ADDRESS
# =====================================================

set -e

export DISPLAY=:99

echo "========================================="
echo "Starting AT-SPI Observer..."
echo "========================================="

# 方法1：从环境变量获取（如果在start_all.sh的会话中）
if [ -n "$DBUS_SESSION_BUS_ADDRESS" ]; then
    echo "✅ 使用环境变量中的DBUS_SESSION_BUS_ADDRESS"
    echo "   $DBUS_SESSION_BUS_ADDRESS"
else
    # 方法2：从at-spi2-registryd进程获取DBus地址
    echo "🔍 查找AT-SPI的DBus会话地址..."

    # 查找at-spi2-registryd进程
    ATSPI_PID=$(pgrep -f at-spi2-registryd | head -1)

    if [ -z "$ATSPI_PID" ]; then
        echo "❌ AT-SPI registry未运行"
        echo "   请先使用start_all.sh启动所有服务"
        exit 1
    fi

    echo "✅ 找到AT-SPI Registry PID: $ATSPI_PID"

    # 读取进程的环境变量
    DBUS_ADDRESS=$(cat /proc/$ATSPI_PID/environ 2>/dev/null | tr '\0' '\n' | grep DBUS_SESSION_BUS_ADDRESS | cut -d= -f2)

    if [ -z "$DBUS_ADDRESS" ]; then
        # 方法3：从文件系统获取
        echo "🔍 从文件系统查找DBus地址..."

        # 检查常见的DBus地址文件
        if [ -f "/root/.cache/at-spi/bus_99" ]; then
            echo "✅ 找到AT-SPI bus文件"
            DBUS_ADDRESS="unix:path=/root/.cache/at-spi/bus_99"
        else
            echo "❌ 无法确定DBUS_SESSION_BUS_ADDRESS"
            echo "   请确保在start_all.sh启动的会话中运行此脚本"
            exit 1
        fi
    fi

    export DBUS_SESSION_BUS_ADDRESS=$DBUS_ADDRESS
    echo "✅ 使用DBUS_SESSION_BUS_ADDRESS: $DBUS_ADDRESS"
fi

# 设置AT-SPI相关环境变量
export GNOME_ACCESSIBILITY=1
export QT_ACCESSIBILITY=1
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1

echo ""
echo "========================================="
echo "环境变量："
echo "  DISPLAY=$DISPLAY"
echo "  DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS"
echo "  QT_ACCESSIBILITY=$QT_ACCESSIBILITY"
echo "========================================="
echo ""

# 等待AT-SPI完全初始化
echo "等待AT-SPI初始化..."
sleep 2

# 运行AT-SPI观察者
echo "启动AT-SPI观察者..."
echo ""

cd /app
python3 -m core.producer.atspi_observer

echo ""
echo "========================================="
echo "AT-SPI观察者已退出"
echo "========================================="
