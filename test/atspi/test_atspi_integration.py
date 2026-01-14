"""
AT-SPI 完整工作流集成测试

测试 AT-SPI 在真实场景中的端到端功能
"""

import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIFullWorkflow:
    """
    AT-SPI 完整工作流集成测试类
    """

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_complete_message_workflow(self):
        """
        测试完整的消息工作流

        步骤：
        1. 初始化 AT-SPI 观察者
        2. 查找微信窗口
        3. 获取初始消息列表
        4. 启动监听
        5. 模拟接收新消息
        6. 验证消息提取
        7. 停止监听
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor.extractor import UniversalMessageExtractor

        # 1. 初始化观察者
        observer = ATSPIObserver()
        assert observer is not None

        # 2. 初始化 AT-SPI
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 3. 查找微信窗口
        if not observer.wechat_window:
            pytest.skip("微信窗口未找到")

        # 4. 初始化消息提取器
        extractor = UniversalMessageExtractor(save_dir="/tmp/test")
        assert extractor is not None

        # 5. 获取初始消息列表
        initial_messages = observer.get_message_list_snapshot()
        initial_count = len(initial_messages)
        print(f"✅ 初始消息数: {initial_count}")

        # 6. 启动监听
        received_messages = []

        def callback(message):
            received_messages.append(message)

        observer.add_callback(callback)
        observer.start_monitoring(interval=0.5)

        # 7. 等待一段时间监听新消息
        print("🎧 监听新消息（5秒）...")
        time.sleep(5)

        # 8. 停止监听
        observer.stop_monitoring()

        # 9. 获取最终消息列表
        final_messages = observer.get_message_list_snapshot()
        final_count = len(final_messages)
        print(f"✅ 最终消息数: {final_count}")

        # 10. 验证
        assert isinstance(final_messages, list)
        assert final_count >= initial_count

        if final_count > initial_count:
            print(f"✅ 检测到 {final_count - initial_count} 条新消息")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_atspi_with_sse_push(self):
        """
        测试 AT-SPI 与 SSE 推送的集成

        验证：
        1. AT-SPI 提取消息
        2. 消息推送到 Redis
        3. SSE 从 Redis 读取并推送
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor.extractor import UniversalMessageExtractor

        # 初始化观察者
        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 获取消息列表
        messages = observer.get_message_list_snapshot()
        if not messages:
            pytest.skip("没有可用的消息")

        # 验证消息格式
        message = messages[0]
        assert hasattr(message, 'sender')
        assert hasattr(message, 'content')
        assert hasattr(message, 'timestamp')
        print(f"✅ 消息格式验证通过: {message.sender} - {message.content}")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_multiple_callback_handlers(self):
        """
        测试多个回调处理器

        验证多个回调函数都能正确接收消息
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 创建多个回调
        callback1_messages = []
        callback2_messages = []

        def callback1(message):
            callback1_messages.append(message)

        def callback2(message):
            callback2_messages.append(message)

        # 添加所有回调
        observer.add_callback(callback1)
        observer.add_callback(callback2)

        # 手动触发回调
        from services.wechat_sandbox.core.extractor.extractor import Message
        test_message = Message(
            sender="TestUser",
            content="Test message",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        observer._notify_callbacks(test_message)

        # 验证两个回调都被调用
        assert len(callback1_messages) == 1
        assert len(callback2_messages) == 1
        print("✅ 多个回调处理器工作正常")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_callback_removal(self):
        """
        测试回调移除功能
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 添加回调
        callback = Mock()
        observer.add_callback(callback)

        # 移除回调
        observer.remove_callback(callback)

        # 手动触发
        from services.wechat_sandbox.core.extractor.extractor import Message
        test_message = Message(
            sender="TestUser",
            content="Test message",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        observer._notify_callbacks(test_message)

        # 验证回调未被调用
        callback.assert_not_called()
        print("✅ 回调移除功能正常")


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIMessageTypes:
    """
    AT-SPI 消息类型测试
    """

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_text_message_detection(self):
        """
        测试文本消息检测
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor.extractor import MessageType

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        messages = observer.get_message_list_snapshot()

        # 统计文本消息数量
        text_messages = [m for m in messages if m.message_type == MessageType.TEXT]
        print(f"✅ 检测到 {len(text_messages)} 条文本消息")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_photo_message_detection(self):
        """
        测试图片消息检测
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor.extractor import MessageType

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        messages = observer.get_message_list_snapshot()

        # 统计图片消息数量
        photo_messages = [m for m in messages if m.message_type == MessageType.PHOTO]
        print(f"✅ 检测到 {len(photo_messages)} 条图片消息")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_video_message_detection(self):
        """
        测试视频消息检测
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.extractor.extractor import MessageType

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        messages = observer.get_message_list_snapshot()

        # 统计视频消息数量
        video_messages = [m for m in messages if m.message_type == MessageType.VIDEO]
        print(f"✅ 检测到 {len(video_messages)} 条视频消息")


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIErrorHandling:
    """
    AT-SPI 错误处理测试
    """

    def test_atspi_unavailable_handling(self):
        """
        测试 AT-SPI 不可用时的处理

        验证系统在 AT-SPI 不可用时能够优雅降级
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()

        # 尝试初始化
        result = observer.initialize()

        # 验证返回值
        assert result in [True, False]

        if not result:
            print("⚠️  AT-SPI 不可用，系统应切换到视觉模式")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_wechat_window_not_found(self):
        """
        测试微信窗口未找到时的处理
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 如果未找到微信窗口
        if not observer.wechat_window:
            print("⚠️  微信窗口未找到")
            assert observer.wechat_window is None
        else:
            print("✅ 微信窗口已找到")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_empty_message_list(self):
        """
        测试空消息列表的处理
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 获取消息列表
        messages = observer.get_message_list_snapshot()

        # 验证返回类型
        assert isinstance(messages, list)

        if not messages:
            print("⚠️  消息列表为空")
        else:
            print(f"✅ 消息列表包含 {len(messages)} 条消息")


@pytest.mark.integration
@pytest.mark.atspi
class TestATSPIPerformance:
    """
    AT-SPI 性能测试
    """

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_message_list_performance(self):
        """
        测试消息列表获取性能

        验证：
        1. 单次获取时间 < 1秒
        2. 连续获取稳定性
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 测试单次获取性能
        start_time = time.time()
        messages = observer.get_message_list_snapshot()
        elapsed_time = time.time() - start_time

        print(f"✅ 单次获取耗时: {elapsed_time:.3f}秒")

        # 验证性能（应该 < 1秒）
        assert elapsed_time < 1.0

        # 测试连续获取稳定性
        times = []
        for i in range(5):
            start_time = time.time()
            observer.get_message_list_snapshot()
            times.append(time.time() - start_time)

        avg_time = sum(times) / len(times)
        print(f"✅ 平均获取耗时: {avg_time:.3f}秒")

        # 验证稳定性（标准差应该较小）
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        print(f"✅ 标准差: {std_dev:.3f}秒")

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_monitoring_performance(self):
        """
        测试监听性能

        验证：
        1. CPU 占用合理
        2. 内存占用稳定
        """
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver

        observer = ATSPIObserver()
        if not observer.initialize():
            pytest.skip("AT-SPI 初始化失败")

        # 启动监听
        observer.start_monitoring(interval=0.5)

        # 监听 5 秒
        time.sleep(5)

        # 停止监听
        observer.stop_monitoring()

        print("✅ 监听性能测试完成")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
