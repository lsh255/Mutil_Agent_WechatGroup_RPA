"""
消息类型分类器
职责：
1. 根据消息气泡的特征判断消息类型（文本/图片/视频/链接）
2. 使用图像特征进行分类
"""

import numpy as np
import cv2
from PIL import Image
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from utils.config import config

class Classifier:
    """
    消息类型分类器
    
    使用颜色特征识别消息类型图标
    """
    
    def __init__(self, config_dict=None):
        if config_dict is None:
            config_dict = config.get('classification', {})
        
        self.media_icon_hsv_lower = np.array(config_dict.get('media_icon_hsv_lower', [100, 43, 46]))
        self.media_icon_hsv_upper = np.array(config_dict.get('media_icon_hsv_upper', [124, 255, 255]))
        self.link_icon_hsv_lower = np.array(config_dict.get('link_icon_hsv_lower', [0, 43, 46]))
        self.link_icon_hsv_upper = np.array(config_dict.get('link_icon_hsv_upper', [10, 255, 255]))
        self.min_icon_area = config_dict.get('min_icon_area', 100)
        
        self.video_icon_color = config_dict.get('video_icon_color', [100, 150, 200])
        self.video_color_tolerance = config_dict.get('video_color_tolerance', 30)
        
        logger.info("Classifier initialized")
    
    def _has_video_icon(self, image):
        try:
            if isinstance(image, Image.Image):
                image_np = np.array(image)
            else:
                image_np = image
            
            lower_bound = np.array([
                max(0, self.video_icon_color[0] - self.video_color_tolerance),
                max(0, self.video_icon_color[1] - self.video_color_tolerance),
                max(0, self.video_icon_color[2] - self.video_color_tolerance)
            ])
            upper_bound = np.array([
                min(255, self.video_icon_color[0] + self.video_color_tolerance),
                min(255, self.video_icon_color[1] + self.video_color_tolerance),
                min(255, self.video_icon_color[2] + self.video_color_tolerance)
            ])
            
            if len(image_np.shape) == 3:
                mask = cv2.inRange(image_np, lower_bound, upper_bound)
                video_area = cv2.countNonZero(mask)
                
                if video_area > self.min_icon_area:
                    logger.debug(f"Detected video icon: area={video_area}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting video icon: {e}")
            return False
    
    def classify(self, image) -> str:
        try:
            if isinstance(image, Image.Image):
                img_hsv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
            else:
                if len(image.shape) == 3:
                    img_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
                else:
                    img_hsv = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                    img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_RGB2HSV)
            
            media_mask = cv2.inRange(img_hsv, self.media_icon_hsv_lower, self.media_icon_hsv_upper)
            media_contours, _ = cv2.findContours(media_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if sum(cv2.contourArea(c) for c in media_contours) > self.min_icon_area:
                if self._has_video_icon(image):
                    return 'video'
                return 'image'
            
            link_mask = cv2.inRange(img_hsv, self.link_icon_hsv_lower, self.link_icon_hsv_upper)
            link_contours, _ = cv2.findContours(link_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if sum(cv2.contourArea(c) for c in link_contours) > self.min_icon_area:
                return 'link'
            
            return 'text'
            
        except Exception as e:
            logger.error(f"Error classifying message type: {e}")
            return 'text'
