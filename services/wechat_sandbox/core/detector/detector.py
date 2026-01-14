"""
变化检测与边界识别模块
包含两个核心类：
1. ChangeDetector: 负责检测屏幕内容变化，识别并定位消息气泡。
2. BoundaryDetector: 负责推断消息气泡的逻辑边界（包含头像、昵称等上下文）。
"""

import cv2
import numpy as np
from utils.logger import logger
from config.config import config


class ChangeDetector:
    """
    屏幕变化检测器

    职责:
        1. 计算图像哈希 (dHash) 以检测帧间差异
        2. 使用计算机视觉算法 (阈值、形态学、轮廓查找) 识别消息气泡
        3. 验证气泡的完整性和有效性
    """

    def __init__(self):
        """初始化检测器参数"""
        self.threshold = 0.05
        self.hash_diff_threshold = 2
        self.hsv_lower = np.array([35, 20, 240])
        self.hsv_upper = np.array([85, 255, 255])
        self.min_height = 20
        self.max_height = 1000
        self.min_width = 100
        self.min_area = 500
        self.prev_hash = None
        self.prev_frame = None

        logger.info("ChangeDetector initialized")

    def compute_dhash(self, image):
        """
        计算图像的 dHash（差分哈希），用于快速比较图像相似度

        输入:
            image: PIL.Image 或 numpy.ndarray，输入图像对象
        返回:
            str: dHash 字符串，由0和1组成的二进制字符串
        """
        try:
            if isinstance(image, str):
                return None

            if hasattr(image, 'convert'):
                image = image.convert('L')
                image = np.array(image)
            elif len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            resized = cv2.resize(image, (9, 8))
            diff = resized[:, 1:] > resized[:, :-1]
            return ''.join(diff.flatten().astype(str))
        except Exception as e:
            logger.error(f"计算 dHash 失败: {e}")
            return None

    def hash_distance(self, hash1, hash2):
        """
        计算两个 dHash 的汉明距离（不同字符的个数）

        输入:
            hash1: 第一个哈希字符串
            hash2: 第二个哈希字符串
        返回:
            int: 汉明距离，值越大表示图像差异越大
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return float('inf')
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def detect_changes(self, current_frame, prev_frame=None):
        """
        检测图像变化，判断当前帧与上一帧是否有显著差异

        输入:
            current_frame: 当前帧图像
            prev_frame: 上一帧图像（可选，不提供则使用内部状态self.prev_hash）
        返回:
            bool: 是否检测到显著变化（True表示有变化，False表示无变化）
        """
        try:
            current_hash = self.compute_dhash(current_frame)
            if not current_hash:
                return False

            prev_hash = prev_frame or self.prev_hash
            if not prev_hash:
                self.prev_hash = current_hash
                return False

            distance = self.hash_distance(current_hash, prev_hash)
            changed = distance >= self.hash_diff_threshold

            self.prev_hash = current_hash
            return changed
        except Exception as e:
            logger.error(f"检测变化失败: {e}")
            return False

    def detect_bubbles(self, image):
        """
        识别消息气泡，使用颜色过滤和轮廓检测定位微信消息气泡

        输入:
            image: 输入图像 (PIL.Image 或 numpy.ndarray)
        返回:
            list: 检测到的气泡列表，每个元素为字典 {'rect': (x, y, w, h), 'contour': contour}
        """
        try:
            if isinstance(image, str):
                return []

            if hasattr(image, 'convert'):
                image_np = np.array(image)
            else:
                image_np = image

            if len(image_np.shape) == 3:
                image_hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
            else:
                image_hsv = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
                image_hsv = cv2.cvtColor(image_hsv, cv2.COLOR_RGB2HSV)

            mask = cv2.inRange(image_hsv, self.hsv_lower, self.hsv_upper)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            bubbles = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                if h < self.min_height or h > self.max_height:
                    continue
                if w < self.min_width:
                    continue
                area = cv2.contourArea(contour)
                if area < self.min_area:
                    continue

                bubbles.append({
                    'rect': (x, y, w, h),
                    'contour': contour
                })

            bubbles.sort(key=lambda b: b['rect'][1])
            return bubbles
        except Exception as e:
            logger.error(f"检测气泡失败: {e}")
            return []


class BoundaryDetector:
    """
    边界检测器

    职责:
        1. 扩展气泡边界以包含头像、昵称等上下文
        2. 确保边界不超出图像范围
    """

    def __init__(self):
        """初始化边界检测器"""
        self.avatar_width = 50
        self.nickname_height = 30
        self.padding = 10

        logger.info("BoundaryDetector initialized")

    def expand_boundary(self, bubble_rect, image_shape):
        """
        扩展气泡边界，将消息气泡扩展为包含头像、昵称等上下文的完整区域

        输入:
            bubble_rect: 原始气泡矩形 (x, y, w, h)
            image_shape: 图像形状 (height, width)
        返回:
            tuple: 扩展后的边界 (x, y, w, h)
        """
        try:
            x, y, w, h = bubble_rect
            img_h, img_w = image_shape[:2]

            new_x = max(0, x - self.avatar_width - self.padding)
            new_y = max(0, y - self.nickname_height - self.padding)
            new_w = min(img_w - new_x, w + self.avatar_width + 2 * self.padding)
            new_h = min(img_h - new_y, h + self.nickname_height + 2 * self.padding)

            return (new_x, new_y, new_w, new_h)
        except Exception as e:
            logger.error(f"扩展边界失败: {e}")
            return bubble_rect
