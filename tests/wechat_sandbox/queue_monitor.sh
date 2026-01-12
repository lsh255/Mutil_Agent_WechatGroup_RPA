#!/bin/bash
# Redis队列监控脚本
# 实时监控微信沙盒的Redis队列状态

echo "=== 微信沙盒队列监控 ==="
echo "每2秒刷新一次，按Ctrl+C退出"
echo ""

# Redis配置
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
RAW_STREAM="wechat:messages:raw"
PRECISE_STREAM="wechat:messages:precise"
LOCK_PREFIX="wechat:lock:"

# Redis命令
REDIS_CLI="redis-cli -h $REDIS_HOST -p $REDIS_PORT"

# 测试连接
if ! $REDIS_CLI ping > /dev/null 2>&1; then
    echo "❌ 无法连接到Redis服务器 ($REDIS_HOST:$REDIS_PORT)"
    exit 1
fi

echo "✅ 已连接到Redis ($REDIS_HOST:$REDIS_PORT)"
echo ""

while true; do
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         微信沙盒队列监控 - $(date '+%Y-%m-%d %H:%M:%S')          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # 原始队列
    RAW_COUNT=$($REDIS_CLI XLEN $RAW_STREAM 2>/dev/null || echo "0")
    echo "📥 原始队列 (Raw):          $RAW_COUNT 条消息"

    # 精确队列
    PRECISE_COUNT=$($REDIS_CLI XLEN $PRECISE_STREAM 2>/dev/null || echo "0")
    echo "📤 精确队列 (Precise):      $PRECISE_COUNT 条消息"

    # 计算处理进度
    if [ "$RAW_COUNT" -gt 0 ] || [ "$PRECISE_COUNT" -gt 0 ]; then
        TOTAL=$((RAW_COUNT + PRECISE_COUNT))
        if [ "$TOTAL" -gt 0 ]; then
            PERCENT=$((PRECISE_COUNT * 100 / TOTAL))
            echo "📊 处理进度:                $PERCENT% ($PRECISE_COUNT/$TOTAL)"
        fi
    fi

    echo ""
    echo "────────────────────────────────────────────────────────────"

    # 最新原始消息
    if [ "$RAW_COUNT" -gt 0 ]; then
        echo ""
        echo "📌 最新原始消息:"
        echo "────────────────────────────────────────────────────────────"
        $REDIS_CLI XREVRANGE $RAW_STREAM + - COUNT 1 | while read -r line; do
            # 美化JSON输出（如果安装了jq）
            if command -v jq &> /dev/null; then
                echo "$line" | jq -r 'select(.id != null) | "\(.timestamp // "N/A") | \(.type // "N/A") | Producer: \(.metadata.producer // "N/A")"' 2>/dev/null || echo "$line"
            else
                # 简单格式化
                echo "$line" | grep -o '"timestamp":"[^"]*"' | head -1
                echo "$line" | grep -o '"type":"[^"]*"' | head -1
            fi
        done
    else
        echo ""
        echo "📭 原始队列为空"
    fi

    echo ""
    echo "────────────────────────────────────────────────────────────"

    # 最新精确消息
    if [ "$PRECISE_COUNT" -gt 0 ]; then
        echo ""
        echo "📌 最新精确消息:"
        echo "────────────────────────────────────────────────────────────"
        $REDIS_CLI XREVRANGE $PRECISE_STREAM + - COUNT 1 | while read -r line; do
            if command -v jq &> /dev/null; then
                echo "$line" | jq -r 'select(.id != null) | "\(.timestamp // "N/A") | \(.type // "N/A") | Content: \(.precise_content.text // .precise_content.type // "N/A")"' 2>/dev/null || echo "$line"
            else
                echo "$line" | grep -o '"timestamp":"[^"]*"' | head -1
                echo "$line" | grep -o '"type":"[^"]*"' | head -1
            fi
        done
    else
        echo ""
        echo "📭 精确队列为空"
    fi

    echo ""
    echo "────────────────────────────────────────────────────────────"

    # 消息锁
    LOCK_COUNT=$($REDIS_CLI KEYS "${LOCK_PREFIX}*" 2>/dev/null | wc -l)
    echo ""
    echo "🔒 当前锁定消息:            $LOCK_COUNT 条"

    # Redis内存使用
    INFO=$($REDIS_CLI INFO memory 2>/dev/null)
    if [ -n "$INFO" ]; then
        USED=$(echo "$INFO" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
        PEAK=$(echo "$INFO" | grep "used_memory_peak_human:" | cut -d: -f2 | tr -d '\r')
        echo "💾 Redis内存使用:           $USED (峰值: $PEAK)"
    fi

    echo ""
    echo "╚════════════════════════════════════════════════════════════╝"
    echo "按 Ctrl+C 退出监控"

    sleep 2
done
