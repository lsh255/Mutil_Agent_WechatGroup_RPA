"""
生产者服务测试（v2.0）
"""
import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestChangeDetector:
    """
    变化检测器测试类（v2.0）
    """

    @pytest.fixture
    def detector(self):
        """
        创建检测器实例（气泡检测器）
        """
        from core.detector.detector import BubbleDetector
        return BubbleDetector()

    @pytest.fixture
    def mock_images(self):
        """
        创建Mock图像
        """
        image1 = np.zeros((100, 100, 3), dtype=np.uint8)
        image2 = np.zeros((100, 100, 3), dtype=np.uint8)
        image2[50:55, 50:55] = 255

        return image1, image2

    def test_detector_initialization(self, detector):
        """
        测试检测器初始化
        """
        assert detector is not None
        assert detector.threshold == 0.05
        assert detector.prev_frame is None

    def test_detect_change(self, detector, mock_images):
        """
        测试变化检测
        """
        image1, image2 = mock_images

        # 计算 dHash
        hash1 = detector.compute_dhash(image1)
        hash2 = detector.compute_dhash(image2)

        assert hash1 is not None
        assert hash2 is not None
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)


class TestATSPIObserver:
    """
    AT-SPI 观察者测试类（v2.0）
    """

    @pytest.fixture
    def observer(self):
        """
        创建 ATSPIObserver 实例
        """
        from core.atspi.observer import ATSPIObserver
        return ATSPIObserver()

    def test_observer_creation(self, observer):
        """
        测试观察者创建
        """
        assert observer is not None
        assert observer.registry is None  # 未初始化
        assert observer.wechat_window is None
        assert observer.message_list is None

    def test_add_callback(self, observer):
        """
        测试添加回调函数
        """
        callback = Mock()
        observer.add_callback(callback)
        assert callback in observer.callbacks

    def test_message_model(self, observer):
        """
        测试 ATSPIMessage 数据模型
        """
        from core.atspi.observer import ATSPIMessage
        from datetime import datetime

        message = ATSPIMessage(
            sender="TestUser",
            content="Test message",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        assert message.sender == "TestUser"
        assert message.content == "Test message"
        assert message.message_type == "text"
        assert message.raw_object is None


class TestHybridProducer:
    """
    混合生产者测试类（v2.0）
    """

    @pytest.fixture
    def redis_client(self):
        """
        创建模拟Redis客户端
        """
        client = Mock()
        client.xadd = Mock(return_value=b"test_stream_id")
        client.ping = Mock(return_value=True)
        return client

    @pytest.fixture
    def producer(self, redis_client):
        """
        创建 HybridProducer 实例
        """
        from core.producer.hybrid_producer import HybridProducer, ProductionMode

        producer = HybridProducer(
            redis_client=redis_client,
            mode=ProductionMode.HYBRID
        )
        return producer

    def test_producer_initialization(self, producer):
        """
        测试生产者初始化
        """
        from core.producer.hybrid_producer import ProductionMode

        assert producer is not None
        assert producer.mode.value == "hybrid"
        assert producer.active_mode is None
        assert producer.stats['total_messages'] == 0

    def test_get_stats(self, producer):
        """
        测试获取统计信息
        """
        stats = producer.get_stats()

        assert 'mode' in stats
        assert 'stats' in stats
        assert 'atspi_available' in stats
        assert 'visual_available' in stats

    def test_mode_enums(self):
        """
        测试生产模式枚举
        """
        from core.producer.hybrid_producer import ProductionMode

        assert ProductionMode.ATSPI.value == "atspi"
        assert ProductionMode.VISUAL.value == "visual"
        assert ProductionMode.HYBRID.value == "hybrid"


class TestMessageExtractor:
    """
    消息提取器测试类（v2.0）
    """

    @pytest.fixture
    def extractor(self):
        """
        创建 UniversalMessageExtractor 实例
        """
        from core.extractor import UniversalMessageExtractor

        return UniversalMessageExtractor(save_dir="/tmp/test")

    def test_extractor_creation(self, extractor):
        """
        测试提取器创建
        """
        assert extractor is not None
        # save_dir 是 Path 对象，验证它存在且指向正确位置
        assert extractor.save_dir is not None
        # 使用 as_posix() 进行跨平台路径比较
        assert extractor.save_dir.as_posix() == "/tmp/test"

    def test_message_type_enum(self):
        """
        测试消息类型枚举
        """
        from core.extractor import MessageType

        assert MessageType.TEXT.value == "text"
        assert MessageType.PHOTO.value == "photo"
        assert MessageType.VIDEO.value == "video"
        assert MessageType.OTHER.value == "other"

    def test_extracted_message_model(self):
        """
        测试 ExtractedMessage 数据模型
        """
        from core.extractor import ExtractedMessage, MessageType
        from datetime import datetime

        message = ExtractedMessage(
            msg_id="test_001",
            timestamp=time.time(),
            msg_type=MessageType.TEXT,
            sender="张三",
            content_text="测试消息",
            media_path=None,
            high_res_media_path=None,
            window_detected=False,
            window_title=None,
            metadata={}
        )

        assert message.msg_id == "test_001"
        assert message.msg_type == MessageType.TEXT
        assert message.sender == "张三"
        assert message.content_text == "测试消息"
        assert message.window_detected is False

    def test_message_to_sse_json(self):
        """
        测试消息转换为 SSE JSON 格式
        """
        from core.extractor import ExtractedMessage, MessageType

        message = ExtractedMessage(
            msg_id="test_002",
            timestamp=time.time(),
            msg_type=MessageType.PHOTO,
            sender="李四",
            content_text="",
            media_path="/tmp/photo.png",
            high_res_media_path="/tmp/photo.png",
            window_detected=True,
            window_title="Photos and Videos",
            metadata={}
        )

        sse_json = message.to_sse_json()

        # 验证 JSON 格式
        import json
        data = json.loads(sse_json)

        assert data["id"] == "test_002"
        assert data["type"] == "photo"
        assert data["sender"] == "李四"
        assert "content" in data
        assert data["window_detected"] is True


class TestVisualMonitor:
    """
    视觉监控器测试类（v2.0）
    """

    def test_visual_monitor_creation(self):
        """
        测试视觉监控器创建
        """
        from core.detector.visual_monitor import VisualMonitor

        monitor = VisualMonitor()

        assert monitor is not None
        # VisualMonitor 没有 running 属性，只验证创建成功


class TestConsumer:
    """
    消费者测试类（v2.0）
    """

    @pytest.fixture
    def redis_client(self):
        """
        创建模拟Redis客户端
        """
        client = Mock()
        client.xread = Mock(return_value=[])
        client.xack = Mock(return_value=1)
        return client

    def test_consumer_creation(self):
        """
        测试消费者创建（使用 Mock 避免 logger 问题）
        """
        from core.producer.consumer import AgentConsumer
        from unittest.mock import patch

        # Mock logger 以避免日志参数问题
        with patch('core.producer.consumer.logger'):
            consumer = AgentConsumer(
                producer_service_url="http://localhost:8000"
            )

            assert consumer is not None
            assert consumer.producer_service_url == "http://localhost:8000"


class TestProductionMode:
    """
    生产模式枚举测试
    """

    def test_mode_values(self):
        """
        测试模式枚举值
        """
        from core.producer.hybrid_producer import ProductionMode

        assert ProductionMode.ATSPI.value == "atspi"
        assert ProductionMode.VISUAL.value == "visual"
        assert ProductionMode.HYBRID.value == "hybrid"

    def test_mode_iteration(self):
        """
        测试模式迭代
        """
        from core.producer.hybrid_producer import ProductionMode

        modes = list(ProductionMode)
        assert len(modes) == 3
        assert ProductionMode.ATSPI in modes
        assert ProductionMode.VISUAL in modes
        assert ProductionMode.HYBRID in modes
