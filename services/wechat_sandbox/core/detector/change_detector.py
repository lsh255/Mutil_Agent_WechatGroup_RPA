"""
消息变化检测器
职责：
1. 检测微信ROI区域是否发生变化（是否有新消息）
2. 检测消息气泡边界（返回气泡的矩形区域）
"""

import hashlib
import numpy as np
import cv2
from PIL import Image
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from utils.config import config

class ChangeDetector:
    """
    消息变化检测器
    
    使用dHash（差值哈希）检测图像变化
    使用颜色分割和轮廓检测识别消息气泡
    """
    
    def __init__(self, config_dict=None):
        if config_dict is None:
            config_dict = config.get('detection', {})
        
        self.hash_threshold = config_dict.get('hash_threshold', 10)
        self.min_bubble_area = config_dict.get('min_bubble_area', 1000)
        self.max_bubble_area = config_dict.get('max_bubble_area', 50000)
        
        self.hsv_lower = np.array(config_dict.get('hsv_lower', [100, 43, 46]))
        self.hsv_upper = np.array(config_dict.get('hsv_upper', [124, 255, 255]))
        
        self.prev_hash = None
        self.prev_bubble_count = 0
        
        logger.info("ChangeDetector initialized")
    
    def _calculate_dhash(self, image):
        if isinstance(image, Image.Image):
            image_np = np.array(image)
        else:
            image_np = image
        
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_np
        
        resized = cv2.resize(gray, (8, 8))
        diff = resized[:, 1:] > resized[:, :-1]
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])
    
    def _detect_bubble_contours(self, image):
        if isinstance(image, Image.Image):
            image_np = np.array(image)
        else:
            image_np = image
        
        if len(image_np.shape) == 3:
            image_hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
        else:
            image_hsv = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
            image_hsv = cv2.cvtColor(image_hsv, cv2.COLOR_RGB2HSV)
        
        mask = cv2.inRange(image_hsv, self.hsv_lower, self.hsv_upper)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubbles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if self.min_bubble_area <= area <= self.max_bubble_area:
                x, y, w, h = cv2.boundingRect(contour)
                bubbles.append({
                    'rect': (x, y, w, h),
                    'area': area,
                    'contour': contour
                })
        
        return bubbles
    
    def detect_changes(self, image):
        try:
            current_hash = self._calculate_dhash(image)
            
            if self.prev_hash is None:
                self.prev_hash = current_hash
                logger.debug("First frame captured as reference")
                return False
            
            hamming_distance = bin(current_hash ^ self.prev_hash).count('1')
            
            if hamming_distance > self.hash_threshold:
                logger.debug(f"Change detected: hamming_distance={hamming_distance}")
                self.prev_hash = current_hash
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            return False
    
    def detect_bubbles(self, image):
        try:
            bubbles = self._detect_bubble_contours(image)
            
            if len(bubbles) != self.prev_bubble_count:
                self.prev_bubble_count = len(bubbles)
                logger.info(f"Detected {len(bubbles)} bubble(s)")
            
            return bubbles
            
        except Exception as e:
            logger.error(f"Error detecting bubbles: {e}")
            return []
