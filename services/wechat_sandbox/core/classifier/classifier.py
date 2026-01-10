"""
消息类型分类模块（Linux微信版本）
基于图像特征识别消息类型（文本/图片/视频/链接等）
"""

import cv2
import numpy as np
from utils.logger import logger
from utils.config import config

class MessageTypeClassifier:
    """
    消息类型分类器
    
    职责:
        根据图像特征判断消息类型
    """
    
    def __init__(self):
        """初始化分类器"""
        self.media_icon_hsv_lower = np.array([0, 100, 100])
        self.media_icon_hsv_upper = np.array([60, 255, 255])
        
        self.link_icon_hsv_lower = np.array([90, 50, 100])
        self.link_icon_hsv_upper = np.array([130, 255, 255])
        
        self.min_icon_area = 50
        self.min_text_ratio = 2.0
        
        logger.info("MessageTypeClassifier (Linux) initialized")

    def classify(self, image):
        """
        分类消息类型
        
        输入:
            image: 气泡截图 (PIL.Image 或 numpy.ndarray)
        返回:
            str: 消息类型 ('text', 'image', 'video', 'link', 'unknown')
        """
        try:
            if image is None:
                return 'unknown'
            
            if hasattr(image, 'convert'):
                img_np = np.array(image)
            else:
                img_np = image
            
            if len(img_np.shape) == 2:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
            
            img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            
            media_mask = cv2.inRange(img_hsv, self.media_icon_hsv_lower, self.media_icon_hsv_upper)
            media_contours, _ = cv2.findContours(media_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            media_area = sum(cv2.contourArea(c) for c in media_contours)
            
            if media_area > self.min_icon_area:
                if self._has_video_icon(img_np):
                    return 'video'
                return 'image'
            
            link_mask = cv2.inRange(img_hsv, self.link_icon_hsv_lower, self.link_icon_hsv_upper)
            link_contours, _ = cv2.findContours(link_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            link_area = sum(cv2.contourArea(c) for c in link_contours)
            
            if link_area > self.min_icon_area:
                return 'link'
            
            h, w = img_np.shape[:2]
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio > self.min_text_ratio:
                return 'link'
            
            return 'text'
            
        except Exception as e:
            logger.error(f"分类消息类型失败: {e}")
            return 'unknown'

    def _has_video_icon(self, image):
        """
        检测是否为视频（查找播放按钮图标）
        
        输入:
            image: 图像
        返回:
            bool: 是否为视频
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            
            edges = cv2.Canny(gray, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                hull = cv2.convexHull(contour)
                
                if len(hull) == 3:
                    area = cv2.contourArea(contour)
                    if area > 30:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"检测视频图标失败: {e}")
            return False
