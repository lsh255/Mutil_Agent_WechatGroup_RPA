#!/bin/bash
# =====================================================
# AT-SPI混合方案测试脚本
# =====================================================
# 功能：测试AT-SPI UI控件自动化消息获取方案
# 用途：验证AT-SPI功能，与视觉方案对比
# =====================================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "AT-SPI混合方案测试脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在容器中
if [ ! -f /.dockerenv ]; then
    echo -e "${YELLOW}警告：此脚本应该在Docker容器中运行${NC}"
    echo "建议命令："
    echo "  docker exec -it wechat_sandbox_test bash /app/test_atspi_solution.sh"
    echo ""
fi

# 检查环境变量
echo "1. 检查环境变量..."
if [ -z "$QT_ACCESSIBILITY" ]; then
    echo -e "${YELLOW}⚠️  QT_ACCESSIBILITY未设置${NC}"
    echo "   设置：export QT_ACCESSIBILITY=1"
    export QT_ACCESSIBILITY=1
else
    echo -e "${GREEN}✅ QT_ACCESSIBILITY=$QT_ACCESSIBILITY${NC}"
fi
echo ""

# 检查AT-SPI服务
echo "2. 检查AT-SPI服务..."
if pgrep -f 'at-spi-bus-launcher' > /dev/null; then
    echo -e "${GREEN}✅ AT-SPI服务正在运行${NC}"
else
    echo -e "${YELLOW}⚠️  AT-SPI服务未运行，正在启动...${NC}"
    /usr/libexec/at-spi-bus-launcher --launch-immediately &
    sleep 2
    if pgrep -f 'at-spi-bus-launcher' > /dev/null; then
        echo -e "${GREEN}✅ AT-SPI服务已启动${NC}"
    else
        echo -e "${RED}❌ AT-SPI服务启动失败${NC}"
        exit 1
    fi
fi
echo ""

# 检查pyatspi
echo "3. 检查pyatspi库..."
if python3 -c "import pyatspi" 2>/dev/null; then
    echo -e "${GREEN}✅ pyatspi已安装${NC}"
    python3 -c "import pyatspi; print(f'   版本: {pyatspi.__version__}')"
else
    echo -e "${RED}❌ pyatspi未安装${NC}"
    echo "   安装命令：pip install pyatspi"
    exit 1
fi
echo ""

# 检查微信是否运行
echo "4. 检查微信客户端..."
if pgrep -f '/opt/wechat/wechat' > /dev/null; then
    echo -e "${GREEN}✅ 微信正在运行${NC}"
else
    echo -e "${YELLOW}⚠️  微信未运行${NC}"
    echo "   启动微信：/opt/wechat/wechat &"
    echo "   提示：请先在noVNC中扫码登录微信"
    read -p "是否继续测试？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# 进入工作目录
cd /app

# 测试1：运行AT-SPI观察者测试
echo "========================================"
echo "测试1：AT-SPI观察者基础功能"
echo "========================================"
echo "正在测试AT-SPI初始化、窗口查找、控件树遍历..."
echo ""

python3 << 'EOF'
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

try:
    from core.producer.atspi_observer import ATSPIObserver

    print("正在初始化AT-SPI观察者...")
    observer = ATSPIObserver()

    if observer.initialize():
        print("\n✅ AT-SPI初始化成功")
        print(f"   微信窗口: {observer.wechat_window.name if observer.wechat_window else 'N/A'}")

        # 获取当前消息列表
        print("\n正在获取当前消息列表...")
        messages = observer.get_message_list_snapshot()
        print(f"✅ 找到 {len(messages)} 条消息")

        if messages:
            print("\n最近的消息:")
            for i, msg in enumerate(messages[-5:], 1):
                print(f"  {i}. [{msg['sender']}] {msg['content'][:50]}")

        sys.exit(0)
    else:
        print("\n❌ AT-SPI初始化失败")
        print("\n可能的原因：")
        print("  1. 微信未启动")
        print("  2. QT_ACCESSIBILITY未设置")
        print("  3. AT-SPI服务未运行")
        print("  4. 微信版本不支持AT-SPI")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

TEST1_RESULT=$?
echo ""

if [ $TEST1_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 测试1通过${NC}"
else
    echo -e "${RED}❌ 测试1失败${NC}"
    echo ""
    echo "故障排查建议："
    echo "  1. 检查微信是否已启动并登录"
    echo "  2. 使用Accerciser查看UI控件树"
    echo "  3. 检查AT-SPI服务状态"
    exit 1
fi
echo ""

# 测试2：实时监听新消息
echo "========================================"
echo "测试2：实时监听新消息（10秒）"
echo "========================================"
echo "请在微信群中发送测试消息..."
echo ""

timeout 10 python3 << 'EOF'
import sys
import logging
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    from core.producer.atspi_observer import ATSPIObserver

    observer = ATSPIObserver()

    if not observer.initialize():
        print("❌ AT-SPI初始化失败")
        sys.exit(1)

    print("✅ AT-SPI观察者已启动")
    print("👂 正在监听新消息...")

    # 添加回调
    def on_message(message):
        print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] 新消息!")
        print(f"   发送者: {message.sender}")
        print(f"   内容: {message.content}")
        print()

    observer.add_callback(on_message)

    # 启动监听
    observer.start_monitoring(interval=0.5)

    # 运行10秒
    time.sleep(10)

    # 停止监听
    observer.stop_monitoring()

    print("\n⏱️  监听结束")

except KeyboardInterrupt:
    print("\n⚠️  用户中断")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ 监听失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

TEST2_RESULT=$?
echo ""

if [ $TEST2_RESULT -eq 0 ] || [ $TEST2_RESULT -eq 124 ]; then
    echo -e "${GREEN}✅ 测试2完成${NC}"
else
    echo -e "${YELLOW}⚠️  测试2异常退出（代码：$TEST2_RESULT）${NC}"
fi
echo ""

# 测试3：混合生产者测试（可选）
echo "========================================"
echo "测试3：混合生产者（可选）"
echo "========================================"
echo "此测试需要Redis服务运行..."
echo ""

read -p "是否运行混合生产者测试？(y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 << 'EOF'
import sys
import time
import redis
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    from core.producer.hybrid_producer import HybridProducer, ProductionMode

    print("正在连接Redis...")
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=False
    )

    # 测试Redis连接
    redis_client.ping()
    print("✅ Redis连接成功")

    print("\n正在初始化混合生产者...")
    producer = HybridProducer(
        redis_client=redis_client,
        mode=ProductionMode.HYBRID
    )

    if producer.initialize():
        print("✅ 混合生产者初始化成功")
        print(f"   当前模式: {producer.active_mode.value if producer.active_mode else 'N/A'}")

        print("\n启动生产者（运行10秒）...")
        producer.start()

        time.sleep(10)

        producer.stop()

        # 打印统计
        stats = producer.get_stats()
        print(f"\n📊 统计信息:")
        print(f"   总消息数: {stats['stats']['total_messages']}")
        print(f"   AT-SPI成功: {stats['stats']['atspi_success']}")
        print(f"   AT-SPI失败: {stats['stats']['atspi_failed']}")
        print(f"   视觉兜底: {stats['stats']['visual_fallback']}")

    else:
        print("❌ 混合生产者初始化失败")
        sys.exit(1)

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

    TEST3_RESULT=$?
    echo ""

    if [ $TEST3_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ 测试3通过${NC}"
    else
        echo -e "${RED}❌ 测试3失败${NC}"
    fi
else
    echo -e "${YELLOW}⏭️  跳过测试3${NC}"
fi
echo ""

# 总结
echo "========================================"
echo "测试总结"
echo "========================================"
echo ""
echo "如果所有测试通过，说明AT-SPI方案可用！"
echo ""
echo "下一步："
echo "  1. 在生产环境中使用混合生产者"
echo "  2. 根据实际使用情况调整参数"
echo "  3. 监控AT-SPI和视觉方案的性能差异"
echo ""
echo "文档："
echo "  📖 docs/atspi_hybrid_solution.md"
echo ""
echo "相关文件："
echo "  - core/producer/atspi_observer.py"
echo "  - core/producer/hybrid_producer.py"
echo ""
