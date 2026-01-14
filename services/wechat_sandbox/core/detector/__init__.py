from .change_detector import ChangeDetector
from .detector import BubbleDetector, BoundaryDetector
from .visual_monitor import VisualMonitor

__all__ = [
    'ChangeDetector',      # 图像变化检测（用于区分图片/视频）
    'BubbleDetector',      # 消息气泡检测（用于检测消息气泡边界）
    'BoundaryDetector',    # 边界扩展（用于扩展气泡区域）
    'VisualMonitor',       # 窗口监控（用于截图和定位）
]
