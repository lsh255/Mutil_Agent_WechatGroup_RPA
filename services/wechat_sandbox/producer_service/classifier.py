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
        # 媒体图标颜色范围（黄色/蓝色等）
        self.media_icon_hsv_lower = np.array([0, 100, 100])
        self.media_icon_hsv_upper = np.array([60, 255, 255])
        
        # 链接图标颜色范围
        self.link_icon_hsv_lower = np.array([90, 50, 100])
        self.link_icon_hsv_upper = np.array([130, 255, 255])
        
        self.min_icon_area = 50
        self.min_text_ratio = 2.0  # 宽高比大于此值可能是链接
        
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
            
            # 转换为 numpy 数组
            if hasattr(image, 'convert'):
                img_np = np.array(image)
            else:
                img_np = image
            
            # 如果是灰度图，转换为 RGB
            if len(img_np.shape) == 2:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
            
            # 转换为 HSV 颜色空间
            img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            
            # 检测媒体图标
            media_mask = cv2.inRange(img_hsv, self.media_icon_hsv_lower, self.media_icon_hsv_upper)
            media_contours, _ = cv2.findContours(media_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            media_area = sum(cv2.contourArea(c) for c in media_contours)
            
            if media_area > self.min_icon_area:
                # 进一步区分图片和视频
                if self._has_video_icon(img_np):
                    return 'video'
                return 'image'
            
            # 检测链接图标
            link_mask = cv2.inRange(img_hsv, self.link_icon_hsv_lower, self.link_icon_hsv_upper)
            link_contours, _ = cv2.findContours(link_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            link_area = sum(cv2.contourArea(c) for c in link_contours)
            
            if link_area > self.min_icon_area:
                return 'link'
            
            # 检查宽高比（链接通常较宽）
            h, w = img_np.shape[:2]
            aspect_ratio = w / h if h > 0 else 0
            if aspect_ratio > self.min_text_ratio:
                return 'link'
            
            # 默认为文本
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
            # 检测三角形形状（播放按钮）
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image  # 转换为灰度图
            
            # 使用边缘检测
            edges = cv2.Canny(gray, 50, 150)  # Canny边缘检测算法
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:  # 遍历所有轮廓
                # 计算轮廓的凸包
                hull = cv2.convexHull(contour)
                
                # 计算凸包的顶点数
                if len(hull) == 3:  # 三角形（播放按钮形状）
                    area = cv2.contourArea(contour)  # 计算轮廓面积
                    if area > 30:  # 面积足够大
                        return True  # 检测到播放按钮，返回True
            
            return False  # 未检测到播放按钮，返回False
            
        except Exception as e:  # 捕获异常
            logger.error(f"检测视频图标失败: {e}")  # 记录错误日志
            return False  # 返回False
