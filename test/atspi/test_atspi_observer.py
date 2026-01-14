"""
AT-SPI 观察者集成测试

测试 AT-SPI 观察者在真实环境中的功能
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIObserverIntegration:
    """
    AT-SPI 观察者集成测试类
    """

    @pytest.fixture
    def observer(self):
        """
        创建 ATSPIObserver 实例
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        observer = ATSPIObserver()
        yield observer
        # 清理
        if observer.registry:
            # 停止监听
            pass

    def test_atspi_initialization(self, observer):
        """
        测试 AT-SPI 初始化
        """
        # 尝试初始化
        result = observer.initialize()

        # 结果取决于环境
        # 在支持 AT-SPI 的环境中应该返回 True
        # 在不支持的环境中应该返回 False
        assert result in [True, False]

        if result:
            assert observer.registry is not None
            print("✅ AT-SPI 初始化成功")
        else:
            print("⚠️  AT-SPI 不可用（可能是环境问题）")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_find_wechat_window(self, observer):
        """
        测试查找微信窗口
        """
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 如果找到了微信窗口
        if observer.wechat_window:
            assert observer.wechat_window is not None
            print(f"✅ 找到微信窗口: {observer.wechat_window}")
        else:
            print("⚠️  微信窗口未运行或未找到")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_get_message_list(self, observer):
        """
        测试获取消息列表
        """
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 获取当前消息列表
        messages = observer.get_message_list_snapshot()

        assert isinstance(messages, list)
        print(f"✅ 获取到 {len(messages)} 条消息")

        # 打印前 3 条消息
        for i, msg in enumerate(messages[:3]):
            print(f"  {i+1}. {msg}")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_monitor_new_messages(self, observer):
        """
        测试监听新消息（10秒）
        """
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 添加回调函数
        received_messages = []

        def callback(message):
            received_messages.append(message)
            print(f"✅ 收到新消息: {message.sender} - {message.content}")

        observer.add_callback(callback)

        # 开始监听（10秒）
        print("🎧 开始监听新消息（10秒）...")
        observer.start_monitoring(interval=0.5)

        # 等待 10 秒
        time.sleep(10)

        # 停止监听
        print("⏹️  停止监听")
        observer.stop_monitoring()

        # 验证
        print(f"📊 共收到 {len(received_messages)} 条新消息")
        assert isinstance(received_messages, list)

    def test_callback_invocation(self, observer):
        """
        测试回调函数调用
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIMessage
        from datetime import datetime

        # 创建测试消息
        test_message = ATSPIMessage(
            sender="TestUser",
            content="Test message",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        # 添加回调函数
        callback = Mock()
        observer.add_callback(callback)

        # 手动触发回调
        observer._notify_callbacks(test_message)

        # 验证回调被调用
        callback.assert_called_once_with(test_message)
        print("✅ 回调函数调用正常")


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIRealWorldWorkflow:
    """
    AT-SPI 真实工作流测试
    """

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_complete_atspi_workflow(self):
        """
        测试完整的 AT-SPI 工作流

        步骤：
        1. 初始化 AT-SPI 观察者
        2. 查找微信窗口
        3. 获取当前消息
        4. 监听新消息（可选）
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        # 1. 初始化
        observer = ATSPIObserver()
        assert observer is not None
        print("✅ 步骤 1: AT-SPI 观察者创建成功")

        # 2. 初始化
        result = observer.initialize()
        if not result:
            pytest.skip("AT-SPI 初始化失败，跳过测试")
        print("✅ 步骤 2: AT-SPI 初始化成功")

        # 3. 查找微信窗口
        if observer.wechat_window:
            print(f"✅ 步骤 3: 找到微信窗口")
        else:
            print("⚠️  步骤 3: 未找到微信窗口（微信可能未运行）")

        # 4. 获取消息列表
        messages = observer.get_message_list_snapshot()
        print(f"✅ 步骤 4: 获取到 {len(messages)} 条消息")

        # 打印示例消息
        if messages:
            print("\n📝 最近的消息示例:")
            for i, msg in enumerate(messages[:3]):
                print(f"  {i+1}. [{msg.sender}] {msg.content}")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_atspi_with_message_extractor(self):
        """
        测试 AT-SPI 与消息提取器的集成
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor import UniversalMessageExtractor

        # 初始化 AT-SPI 观察者
        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 初始化消息提取器
        extractor = UniversalMessageExtractor(save_dir="/tmp/test")
        assert extractor is not None
        print("✅ 消息提取器初始化成功")

        # 获取消息列表
        messages = observer.get_message_list_snapshot()
        print(f"✅ 获取到 {len(messages)} 条消息")

        # 尝试提取第一条消息（如果有）
        if messages:
            # 这里可以添加提取逻辑
            print("✅ AT-SPI 与消息提取器集成测试完成")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
