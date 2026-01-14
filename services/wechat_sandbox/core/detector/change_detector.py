"""
消息变化检测器
职责：
1. 检测微信ROI区域是否发生变化（是否有新消息）
2. 检测消息气泡边界（返回气泡的矩形区域）
3. 对比两张图片是否发生变化（区分图片/视频）
"""

import hashlib
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from config.config import config

# 尝试导入 cv2
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

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

    def detect_image_change(self, img1, img2, threshold: float = 0.01) -> bool:
        """
        检测两张图片是否发生变化（用于区分图片/视频）

        Args:
            img1: 第一张图片（PIL Image 或 numpy array）
            img2: 第二张图片（PIL Image 或 numpy array）
            threshold: 变化阈值（0-1），默认0.01表示1%的像素变化

        Returns:
            bool: True表示有变化（视频），False表示无变化（图片）
        """
        try:
            if img1 is None or img2 is None:
                logger.warning("检测图片变化：输入图片为None")
                return False

            # 转换为 numpy array
            if isinstance(img1, Image.Image):
                arr1 = np.array(img1)
            else:
                arr1 = img1

            if isinstance(img2, Image.Image):
                arr2 = np.array(img2)
            else:
                arr2 = img2

            # 使用 OpenCV 或 numpy 检测
            if CV2_AVAILABLE:
                return self._detect_with_opencv(arr1, arr2, threshold)
            else:
                return self._detect_with_numpy(arr1, arr2, threshold)

        except Exception as e:
            logger.error(f"检测图片变化失败: {e}")
            return False

    def _detect_with_opencv(self, img1: np.ndarray, img2: np.ndarray, threshold: float) -> bool:
        """使用 OpenCV 检测图像变化"""
        try:
            # 转换为灰度图
            gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY) if len(img1.shape) == 3 else img1
            gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY) if len(img2.shape) == 3 else img2

            # 调整大小以加快计算
            resize_size = (64, 64)
            gray1 = cv2.resize(gray1, resize_size)
            gray2 = cv2.resize(gray2, resize_size)

            # 计算差异
            diff = cv2.absdiff(gray1, gray2)

            # 统计变化像素数量
            change_pixels = np.sum(diff > 30)
            total_pixels = diff.size
            change_ratio = change_pixels / total_pixels

            logger.debug(f"图像变化比例: {change_ratio:.4f}, 阈值: {threshold}")

            # 变化比例超过阈值则认为有变化
            return change_ratio > threshold

        except Exception as e:
            logger.warning(f"OpenCV 检测失败，回退到 numpy: {e}")
            return self._detect_with_numpy(img1, img2, threshold)

    def _detect_with_numpy(self, img1: np.ndarray, img2: np.ndarray, threshold: float) -> bool:
        """使用 numpy 进行简单的像素比较"""
        try:
            # 转换为灰度
            if len(img1.shape) == 3:
                gray1 = np.dot(img1, [0.299, 0.587, 0.114]).astype(np.uint8)
            else:
                gray1 = img1

            if len(img2.shape) == 3:
                gray2 = np.dot(img2, [0.299, 0.587, 0.114]).astype(np.uint8)
            else:
                gray2 = img2

            # 调整大小
            resize_size = (64, 64)
            gray1 = np.array(Image.fromarray(gray1).resize(resize_size))
            gray2 = np.array(Image.fromarray(gray2).resize(resize_size))

            # 计算差异
            diff = np.abs(gray1.astype(int) - gray2.astype(int))
            mean_diff = np.mean(diff)

            # 转换为比例（0-255范围，归一化到0-1）
            change_ratio = mean_diff / 255.0

            logger.debug(f"图像平均差异: {mean_diff:.2f}, 比例: {change_ratio:.4f}")

            return change_ratio > threshold

        except Exception as e:
            logger.error(f"numpy 检测失败: {e}")
            return False
