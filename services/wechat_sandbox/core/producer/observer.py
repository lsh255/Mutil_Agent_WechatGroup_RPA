"""
生产者1：消息观察者
职责：
1. 监控微信群消息界面
2. 检测新消息和消息气泡位置
3. 返回：消息气泡截图 + 消息气泡内容的像素位置
"""

import threading
import time
import hashlib
from datetime import datetime
from PIL import Image
import numpy as np
import cv2
import base64
import io
import sys
import os

from core.detector.visual_monitor import VisualMonitor
from core.detector.change_detector import ChangeDetector
from core.queue.manager import QueueManager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from utils.config import config

class Observer:
    """
    生产者1：消息观察者
    
    集成 VisualMonitor 和 ChangeDetector，实现：
    - 持续监控微信窗口ROI区域
    - 检测新消息气泡
    - 返回气泡截图和屏幕像素位置
    """
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.monitor = VisualMonitor()
        self.detector = ChangeDetector()
        self.running = False
        self.thread = None
        
        self.capture_interval = config.get('system.capture_interval_ms', 200) / 1000
        
        logger.info("Producer1 Observer initialized")
    
    def _generate_message_id(self, bubble_img):
        if isinstance(bubble_img, Image.Image):
            img_array = np.array(bubble_img)
        else:
            img_array = bubble_img
        
        img_hash = hashlib.sha256(img_array.tobytes()).hexdigest()
        return f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{img_hash[:12]}"
    
    def _image_to_base64(self, image):
        if image is None:
            return None
        
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_base64
    
    def _convert_screen_coords(self, roi_x, roi_y, screen_x, screen_y):
        return (screen_x + roi_x, screen_y + roi_y)
    
    def start(self):
        if self.running:
            logger.warning("Producer1 Observer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Producer1 Observer started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Producer1 Observer stopped")
    
    def _run(self):
        try:
            self.monitor.locate_wechat()
            if not self.monitor.wechat_window:
                logger.error("Failed to locate WeChat window")
                return
            
            logger.info(f"Monitoring WeChat window: {config.get('monitor.target_group_name')}")
            
            roi_screen_x = self.monitor.roi[0]
            roi_screen_y = self.monitor.roi[1]
            
            while self.running:
                try:
                    screenshot = self.monitor.capture()
                    if screenshot is None:
                        time.sleep(self.capture_interval)
                        continue
                    
                    has_changed = self.detector.detect_changes(screenshot)
                    
                    if has_changed:
                        bubbles = self.detector.detect_bubbles(screenshot)
                        
                        if bubbles:
                            logger.info(f"Detected {len(bubbles)} new bubble(s)")
                            
                            for bubble_info in bubbles:
                                bubble_rect = bubble_info['rect']
                                try:
                                    roi_x, roi_y, w, h = bubble_rect
                                    
                                    center_x = roi_x + w // 2
                                    center_y = roi_y + h // 2
                                    screen_abs_x, screen_abs_y = self._convert_screen_coords(
                                        center_x, center_y, roi_screen_x, roi_screen_y
                                    )
                                    
                                    bubble_img = screenshot.crop((roi_x, roi_y, roi_x + w, roi_y + h))
                                    
                                    msg_id = self._generate_message_id(bubble_img)
                                    
                                    message_data = {
                                        'id': msg_id,
                                        'timestamp': datetime.now().isoformat(),
                                        'type': 'raw_bubble',
                                        'bubble_img_base64': self._image_to_base64(bubble_img),
                                        'position': {
                                            'roi_x': roi_x,
                                            'roi_y': roi_y,
                                            'screen_x': screen_abs_x,
                                            'screen_y': screen_abs_y,
                                            'width': w,
                                            'height': h
                                        },
                                        'priority': 10,
                                        'metadata': {
                                            'producer': 'producer1_observer',
                                            'detection_time': datetime.now().isoformat()
                                        }
                                    }
                                    
                                    self.queue_manager.enqueue_raw(message_data)
                                    logger.info(f"Producer1: Enqueued raw bubble {msg_id} at ({screen_abs_x}, {screen_abs_y})")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing bubble {bubble_rect}: {e}")
                                    continue
                    
                    time.sleep(self.capture_interval)
                    
                except Exception as e:
                    logger.error(f"Error in Producer1 main loop: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Producer1 Observer failed: {e}")
        finally:
            self.running = False
