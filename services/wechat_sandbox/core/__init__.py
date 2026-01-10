"""
核心业务逻辑模块
"""

from core.producer.observer import Observer
from core.producer.content_fetcher import ContentFetcher
from core.producer.agent_consumer import AgentConsumer
from core.queue.manager import QueueManager
from core.detector.change_detector import ChangeDetector
from core.detector.visual_monitor import VisualMonitor
from core.detector.classifier import Classifier
from core.extractor.text_extractor import PrecisionContentFetcher
from core.platform.adapter import PlatformAdapter, get_adapter

__all__ = [
    'Observer',
    'ContentFetcher',
    'AgentConsumer',
    'QueueManager',
    'ChangeDetector',
    'VisualMonitor',
    'Classifier',
    'PrecisionContentFetcher',
    'PlatformAdapter',
    'get_adapter'
]
