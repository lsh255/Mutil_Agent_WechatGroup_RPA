#!/bin/bash
# 微信沙盒快速测试脚本
# 用法: ./quick_test.sh [test_type]
#   test_type: basic | full | performance | monitor

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Python命令
PYTHON_CMD=${PYTHON_CMD:-python3}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 解析参数
TEST_TYPE=${1:-basic}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          微信沙盒快速测试工具                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查Redis连接
echo -e "[1/5] ${YELLOW}检查Redis连接...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis未运行，请先启动Redis${NC}"
    echo "   启动命令: redis-server"
    exit 1
fi
echo -e "${GREEN}✅ Redis已运行${NC}"
echo ""

# 检查服务是否启动
echo -e "[2/5] ${YELLOW}检查微信沙盒服务...${NC}"
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  微信沙盒服务未启动${NC}"
    echo "   请先运行: cd services/wechat_sandbox && python main.py"
    echo ""
    read -p "是否继续测试? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi
echo -e "${GREEN}✅ 服务检查完成${NC}"
echo ""

# 根据测试类型执行不同测试
case "$TEST_TYPE" in
    basic)
        basic_test
        ;;
    full)
        full_test
        ;;
    performance)
        performance_test
        ;;
    monitor)
        monitor_only
        ;;
    *)
        echo -e "${RED}❌ 未知的测试类型: $TEST_TYPE${NC}"
        echo "   支持的测试类型: basic, full, performance, monitor"
        exit 1
        ;;
esac

# 基础测试
basic_test() {
    echo "═══════════════════════════════════════════════════════════"
    echo " 运行基础测试"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "启动SSE客户端..."
    echo "请在微信群中发送测试消息"
    echo ""
    echo "提示:"
    echo "  - 发送几条文本消息"
    echo "  - 发送一张图片"
    echo "  - 发送一个视频"
    echo "  - 按Ctrl+C停止测试"
    echo ""
    read -p "按Enter开始测试..."

    $PYTHON_CMD "$SCRIPT_DIR/sse_client.py" --verbose --save-json
}

# 完整测试
full_test() {
    echo "═══════════════════════════════════════════════════════════"
    echo " 运行完整测试套件"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo -e "${BLUE}[测试1/5]${NC} 队列状态检查..."
    $PYTHON_CMD "$SCRIPT_DIR/queue_monitor.py" --host localhost --port 6379
    echo ""
    read -p "按Enter继续..."

    echo -e "${BLUE}[测试2/5]${NC} SSE基础连接测试..."
    echo "请发送5条测试消息..."
    $PYTHON_CMD "$SCRIPT_DIR/sse_client.py" --client-id full_test_1
    echo ""
    read -p "按Enter继续..."

    echo -e "${BLUE}[测试3/5]${NC} 并发连接测试..."
    echo "启动3个并发客户端，请发送10条消息..."
    $PYTHON_CMD "$SCRIPT_DIR/sse_client.py" --client-id concurrent_1 --save-json &
    PID1=$!
    $PYTHON_CMD "$SCRIPT_DIR/sse_client.py" --client-id concurrent_2 --save-json &
    PID2=$!
    $PYTHON_CMD "$SCRIPT_DIR/sse_client.py" --client-id concurrent_3 --save-json &
    PID3=$!

    echo "等待30秒..."
    sleep 30

    kill $PID1 $PID2 $PID3 2>/dev/null || true
    wait
    echo ""
    read -p "按Enter继续..."

    echo -e "${BLUE}[测试4/5]${NC} 性能测试..."
    echo "请连续发送至少20条消息，测试将运行60秒..."
    $PYTHON_CMD "$SCRIPT_DIR/sse_performance_test.py" --duration 60 --benchmark
    echo ""
    read -p "按Enter继续..."

    echo -e "${BLUE}[测试5/5]${NC} 数据导出和分析..."
    $PYTHON_CMD "$SCRIPT_DIR/queue_monitor.py" --analyze
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    $PYTHON_CMD "$SCRIPT_DIR/queue_monitor.py" --export --output "$SCRIPT_DIR/test_results/queue_export_$TIMESTAMP.json"
    echo ""

    echo "═══════════════════════════════════════════════════════════"
    echo " 完整测试结束！"
    echo "═══════════════════════════════════════════════════════════"
}

# 性能测试
performance_test() {
    echo "═══════════════════════════════════════════════════════════"
    echo " 运行性能测试"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "性能测试将运行2分钟"
    echo "请在此期间持续发送消息（建议至少50条）"
    echo ""
    read -p "按Enter开始测试..."

    $PYTHON_CMD "$SCRIPT_DIR/sse_performance_test.py" --duration 120 --benchmark
}

# 仅监控
monitor_only() {
    echo "═══════════════════════════════════════════════════════════"
    echo " 启动队列监控"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "按 Ctrl+C 停止监控"
    echo ""

    $PYTHON_CMD "$SCRIPT_DIR/queue_monitor.py"
}

# 结束
echo ""
echo "═══════════════════════════════════════════════════════════"
echo " 测试完成"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "测试结果保存在: $SCRIPT_DIR/test_results/"
echo ""
