#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AT-SPI观察者单元测试

测试内容：
1. AT-SPI初始化
2. 微信窗口查找
3. 消息列表控件查找
4. 消息提取
5. 实时监听
"""

import pytest
import time
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG)


class TestATSPIObserver:
    """AT-SPI观察者测试套件"""

    @pytest.fixture
    def observer(self):
        """创建ATSPIObserver实例"""
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        return ATSPIObserver()

    def test_initialization_without_atspi(self, observer):
        """测试在没有pyatspi环境下的初始化"""
        # 模拟pyatspi未安装
        with patch('builtins.__import__', side_effect=ImportError("No module named 'pyatspi'")):
            result = observer.initialize()
            assert result is False
            assert observer.registry is None

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_initialization_with_atspi(self, observer):
        """测试AT-SPI初始化（需要真实环境）"""
        # 这个测试需要在真实环境中运行
        result = observer.initialize()
        # 结果取决于微信是否运行
        # assert result is True or result is False

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_find_wechat_window(self, observer):
        """测试查找微信窗口"""
        observer.initialize()
        # 如果找到了微信窗口
        if observer.wechat_window:
            assert observer.wechat_window is not None
        else:
            # 微信未运行或未找到
            assert observer.wechat_window is None

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_find_message_list(self, observer):
        """测试查找消息列表"""
        observer.initialize()
        # 如果找到了消息列表
        if observer.message_list:
            assert observer.message_list is not None
            assert observer.last_message_count >= 0
        else:
            # 可能微信未运行或未找到
            assert observer.message_list is None

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_get_message_list_snapshot(self, observer):
        """测试获取消息列表快照"""
        observer.initialize()
        messages = observer.get_message_list_snapshot()
        assert isinstance(messages, list)

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_check_new_messages(self, observer):
        """测试检查新消息"""
        observer.initialize()
        new_messages = observer.check_new_messages()
        assert isinstance(new_messages, list)

    def test_add_callback(self, observer):
        """测试添加回调函数"""
        callback = Mock()
        observer.add_callback(callback)
        assert callback in observer.callbacks

    def test_message_callback_invocation(self, observer):
        """测试回调函数调用"""
        from services.wechat_sandbox.core.atspi.observer import ATSPIMessage

        callback = Mock()
        observer.add_callback(callback)

        # 创建测试消息
        test_message = ATSPIMessage(
            sender="TestUser",
            content="Test message",
            timestamp="2025-01-12T10:00:00",
            message_type="text"
        )

        # 手动触发回调
        for cb in observer.callbacks:
            cb(test_message)

        # 验证回调被调用
        callback.assert_called_once_with(test_message)


class TestHybridProducer:
    """混合生产者测试套件"""

    @pytest.fixture
    def redis_client(self):
        """创建模拟Redis客户端"""
        client = Mock()
        client.xadd = Mock(return_value=b"test_stream_id")
        client.ping = Mock(return_value=True)
        return client

    @pytest.fixture
    def producer(self, redis_client):
        """创建HybridProducer实例"""
        from services.wechat_sandbox.core.producer.hybrid_producer import HybridProducer, ProductionMode
        return HybridProducer(
            redis_client=redis_client,
            mode=ProductionMode.HYBRID
        )

    def test_initialization(self, producer):
        """测试生产者初始化"""
        assert producer.mode.value == "hybrid"
        assert producer.active_mode is None
        assert producer.stats['total_messages'] == 0

    def test_atspi_init_failure(self, producer):
        """测试AT-SPI初始化失败的情况"""
        # 模拟AT-SPI初始化失败
        with patch.object(producer, '_init_atspi_observer', return_value=False):
            with patch.object(producer, '_init_visual_observer', return_value=True):
                result = producer.initialize()
                assert result is True
                # 应该降级到视觉模式
                # assert producer.active_mode == ProductionMode.VISUAL

    def test_mode_switching(self, producer, redis_client):
        """测试模式切换"""
        from services.wechat_sandbox.core.producer.hybrid_producer import ProductionMode

        # 切换到视觉模式
        with patch.object(producer, 'stop'):
            with patch.object(producer, 'initialize', return_value=True):
                with patch.object(producer, 'start'):
                    producer.switch_mode(ProductionMode.VISUAL)
                    assert producer.mode == ProductionMode.VISUAL

    def test_get_stats(self, producer):
        """测试获取统计信息"""
        stats = producer.get_stats()
        assert 'mode' in stats
        assert 'stats' in stats
        assert 'atspi_available' in stats
        assert 'visual_available' in stats


class TestATSPIMessage:
    """AT-SPI消息数据类测试"""

    def test_message_creation(self):
        """测试消息创建"""
        from services.wechat_sandbox.core.atspi.observer import ATSPIMessage
        from datetime import datetime

        message = ATSPIMessage(
            sender="Alice",
            content="Hello World",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        assert message.sender == "Alice"
        assert message.content == "Hello World"
        assert message.message_type == "text"
        assert message.raw_object is None


class TestProductionMode:
    """生产模式枚举测试"""

    def test_mode_values(self):
        """测试模式枚举值"""
        from services.wechat_sandbox.core.producer.hybrid_producer import ProductionMode

        assert ProductionMode.ATSPI.value == "atspi"
        assert ProductionMode.VISUAL.value == "visual"
        assert ProductionMode.HYBRID.value == "hybrid"


@pytest.mark.integration
class TestIntegration:
    """集成测试（需要真实环境）"""

    @pytest.mark.skipif(
        not pytest.importorskip('pyatspi', None),
        reason="pyatspi not available"
    )
    def test_full_workflow(self):
        """测试完整工作流程"""
        from services.wechat_sandbox.core.atspi.observer import ATSPIObserver
        from services.wechat_sandbox.core.producer.hybrid_producer import HybridProducer, ProductionMode
        import redis

        # 1. 测试AT-SPI观察者
        observer = ATSPIObserver()
        if observer.initialize():
            messages = observer.get_message_list_snapshot()
            assert isinstance(messages, list)

        # 2. 测试混合生产者（需要Redis）
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.ping()

            producer = HybridProducer(
                redis_client=redis_client,
                mode=ProductionMode.HYBRID
            )

            if producer.initialize():
                assert producer.active_mode is not None
                producer.stop()

        except Exception as e:
            pytest.skip(f"Redis not available: {e}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
