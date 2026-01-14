"""
生产者服务编排层（已废弃）

⚠️ 此文件已废弃，原因是：
- 导入的模块不存在（core.producer.monitor, core.producer.observer 等）
- 功能已被 HybridProducer 替代
- 请使用 core.producer.hybrid_producer.HybridProducer

保留此文件仅用于历史参考，请勿在新代码中使用。
"""

# 以下导入已失效，注释掉以避免 ImportError
# import threading
# from utils.logger import logger
# from core.producer.monitor import VisualMonitor
# from core.producer.observer import Observer
# from core.producer.content_fetcher import ContentFetcher
# from core.detector import ChangeDetector, BoundaryDetector
# from core.classifier import MessageTypeClassifier
# from core.extractor import PrecisionContentFetcher

import warnings
warnings.warn(
    "ProducerService 已废弃，请使用 HybridProducer 替代。",
    DeprecationWarning,
    stacklevel=2
)


# 以下类已废弃，保留仅用于历史参考
class ProducerService:
    """
    生产者服务类

    职责:
        1. 初始化和管理所有生产者组件
        2. 启动和停止消息生产流程
        3. 协调 Observer 和 ContentFetcher 的交互
    """

    def __init__(self, queue_manager):
        """
        初始化生产者服务

        参数:
            queue_manager: Redis 队列管理器实例
        """
        self.queue_manager = queue_manager
        self.observer = None
        self.content_fetcher = None
        self.classifier = None
        self.boundary_detector = None
        self.running = False
        self.thread = None

        logger.info("ProducerService initialized")

    def initialize(self):
        """
        初始化所有组件
        """
        try:
            self.observer = Observer(self.queue_manager)
            self.content_fetcher = ContentFetcher(self.queue_manager)
            self.classifier = MessageTypeClassifier()
            self.boundary_detector = BoundaryDetector()

            logger.info("ProducerService 所有组件初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化 ProducerService 失败: {e}")
            return False

    def start(self):
        """
        启动消息生产流程
        """
        if self.running:
            logger.warning("ProducerService 已在运行")
            return False

        try:
            self.running = True

            self.observer.start()
            self.content_fetcher.start()

            logger.info("ProducerService 已启动")
            return True
        except Exception as e:
            logger.error(f"启动 ProducerService 失败: {e}")
            self.running = False
            return False

    def stop(self):
        """
        停止消息生产流程
        """
        if not self.running:
            logger.warning("ProducerService 未运行")
            return False

        try:
            self.running = False

            if self.observer:
                self.observer.stop()
            if self.content_fetcher:
                self.content_fetcher.stop()

            logger.info("ProducerService 已停止")
            return True
        except Exception as e:
            logger.error(f"停止 ProducerService 失败: {e}")
            return False

    def get_status(self):
        """
        获取服务状态

        返回:
            dict: 包含运行状态的字典
        """
        return {
            'running': self.running,
            'observer_running': self.observer.running if self.observer else False,
            'content_fetcher_running': self.content_fetcher.running if self.content_fetcher else False
        }
