"""
生产者服务测试
"""
import pytest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestMonitor:
    """
    监控器测试类
    """
    
    @pytest.fixture
    def monitor(self, queue_manager):
        """
        创建监控器实例
        """
        from producer_service.monitor import Monitor
        
        mock_config = {
            "target_group_name": "测试群",
            "roi": (100, 200, 500, 800),
            "capture_interval_ms": 200
        }
        
        with patch('producer_service.mct.mct_getCursorPos', return_value=(0, 0)):
            monitor = Monitor(
                config=mock_config,
                queue_manager=queue_manager
            )
        
        yield monitor
    
    def test_monitor_initialization(self, monitor):
        """
        测试监控器初始化
        """
        assert monitor is not None
        assert monitor.roi == (100, 200, 500, 800)
        assert monitor.config_lock is not None
    
    def test_set_roi(self, monitor):
        """
        测试设置ROI
        """
        new_roi = (150, 250, 550, 850)
        
        monitor.set_roi(*new_roi)
        
        assert monitor.roi == new_roi
    
    def test_capture_screenshot(self, monitor):
        """
        测试截图功能（Mock）
        """
        with patch('producer_service.monitor.ImageGrab.grab') as mock_grab:
            mock_image = MagicMock()
            mock_image.size = (1920, 1080)
            mock_grab.return_value = mock_image
            
            screenshot = monitor.capture_screenshot()
            
            assert screenshot is not None
            mock_grab.assert_called_once()
    
    def test_start_stop(self, monitor):
        """
        测试启动和停止监控
        """
        monitor.start()
        
        time.sleep(0.5)
        
        assert monitor.running is True
        
        monitor.stop()
        
        assert monitor.running is False


class TestDetector:
    """
    检测器测试类
    """
    
    @pytest.fixture
    def detector(self):
        """
        创建检测器实例
        """
        from producer_service.detector import ChangeDetector
        return ChangeDetector()
    
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


class TestClassifier:
    """
    分类器测试类
    """
    
    @pytest.fixture
    def classifier(self):
        """
        创建分类器实例
        """
        from producer_service.classifier import MessageTypeClassifier
        return MessageTypeClassifier()
    
    def test_classifier_initialization(self, classifier):
        """
        测试分类器初始化
        """
        assert classifier is not None
        assert classifier.min_icon_area == 50
    
    def test_classify_text_message(self, classifier):
        """
        测试文本消息分类
        """
        # 创建纯文本消息图像（没有特殊图标）
        image = np.full((100, 200, 3), 255, dtype=np.uint8)
        
        message_type = classifier.classify(image)
        
        assert message_type is not None
        assert message_type == 'text'
    
    def test_classify_image_message(self, classifier):
        """
        测试图片消息分类（黄色图标）
        """
        # 创建包含黄色图标的图像
        image = np.full((100, 200, 3), 255, dtype=np.uint8)
        image[20:40, 20:40] = [255, 200, 0]  # 黄色图标
        
        message_type = classifier.classify(image)
        
        assert message_type is not None
        assert message_type in ['image', 'video']
    
    def test_classify_link_message(self, classifier):
        """
        测试链接消息分类（蓝色图标）
        """
        # 创建包含蓝色图标的图像
        image = np.full((100, 200, 3), 255, dtype=np.uint8)
        image[20:40, 20:40] = [0, 100, 255]  # 蓝色图标
        
        message_type = classifier.classify(image)
        
        assert message_type is not None
        assert message_type == 'link'
    
    def test_classify_unknown_message(self, classifier):
        """
        测试未知消息分类
        """
        message_type = classifier.classify(None)
        
        assert message_type == 'unknown'


class TestProducer1:
    """
    生产者1测试类
    """
    
    def test_producer1_initialization(self, queue_manager):
        """
        测试生产者1初始化
        """
        from producer_service.producer1_observer import Producer1
        
        mock_monitor = Mock()
        mock_detector = Mock()
        
        producer = Producer1(
            monitor=mock_monitor,
            detector=mock_detector,
            queue_manager=queue_manager
        )
        
        assert producer is not None
        assert producer.monitor == mock_monitor
        assert producer.detector == mock_detector
    
    def test_producer1_send_message(self, queue_manager):
        """
        测试生产者1发送消息
        """
        from producer_service.producer1_observer import Producer1
        
        mock_monitor = Mock()
        mock_detector = Mock()
        
        producer = Producer1(
            monitor=mock_monitor,
            detector=mock_detector,
            queue_manager=queue_manager
        )
        
        test_message = {
            "message_id": "test_p1_001",
            "bubble_position": {"x": 100, "y": 200, "width": 50, "height": 30}
        }
        
        with patch.object(producer.queue_manager, 'send_raw_message', return_value=True) as mock_send:
            producer.send_raw_message(test_message)
            mock_send.assert_called_once_with(test_message)


class TestProducer2:
    """
    生产者2测试类
    """
    
    def test_producer2_initialization(self, queue_manager):
        """
        测试生产者2初始化
        """
        from producer_service.producer2_content_fetcher import Producer2
        
        producer = Producer2(queue_manager=queue_manager)
        
        assert producer is not None
        assert producer.queue_manager == queue_manager
    
    def test_producer2_send_precise_message(self, queue_manager):
        """
        测试生产者2发送精确消息
        """
        from producer_service.producer2_content_fetcher import Producer2
        
        producer = Producer2(queue_manager=queue_manager)
        
        test_message = {
            "message_id": "test_p2_001",
            "content": "精确消息内容",
            "sender": "张三"
        }
        
        with patch.object(producer.queue_manager, 'send_precise_message', return_value=True) as mock_send:
            producer.send_precise_message(test_message)
            mock_send.assert_called_once_with(test_message)
