"""
变化检测与边界识别模块
包含两个核心类：
1. ChangeDetector: 负责检测屏幕内容变化，识别并定位消息气泡。
2. BoundaryDetector: 负责推断消息气泡的逻辑边界（包含头像、昵称等上下文）。
"""

import cv2  # OpenCV图像处理库，提供图像读取、转换、轮廓检测等功能
import numpy as np  # 数值计算库，提供数组操作和数学运算
from utils.logger import logger  # 日志工具，用于记录运行时信息
from utils.config import config  # 配置管理，读取项目配置参数


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
        self.threshold = 0.05  # 变化阈值（未使用，保留用于未来扩展）
        self.hash_diff_threshold = 2  # dHash差异阈值，超过此值认为图像有变化
        self.hsv_lower = np.array([35, 20, 240])  # 微信气泡颜色范围下限（HSV颜色空间）
        self.hsv_upper = np.array([85, 255, 255])  # 微信气泡颜色范围上限（HSV颜色空间）
        self.min_height = 20  # 检测气泡的最小高度（像素）
        self.max_height = 1000  # 检测气泡的最大高度（像素）
        self.min_width = 100  # 检测气泡的最小宽度（像素）
        self.min_area = 500  # 检测气泡的最小面积（像素平方）
        self.prev_hash = None  # 上一帧的dHash值，用于帧间差异比较
        self.prev_frame = None  # 上一帧图像数据（未使用，保留用于未来扩展）

        logger.info("ChangeDetector initialized")  # 记录初始化完成日志

    def compute_dhash(self, image):
        """
        计算图像的 dHash（差分哈希），用于快速比较图像相似度

        输入:
            image: PIL.Image 或 numpy.ndarray，输入图像对象
        返回:
            str: dHash 字符串，由0和1组成的二进制字符串
        """
        try:
            if isinstance(image, str):  # 检查是否为字符串路径（异常情况）
                return None  # 字符串路径不支持直接计算dHash

            if hasattr(image, 'convert'):  # 检查是否为PIL.Image对象
                image = image.convert('L')  # 转换为灰度图像
                image = np.array(image)  # 转换为numpy数组
            elif len(image.shape) == 3:  # 检查是否为彩色图像（3通道）
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转换为灰度图像

            resized = cv2.resize(image, (9, 8))  # 缩放到9x8尺寸
            diff = resized[:, 1:] > resized[:, :-1]  # 计算每行相邻像素的差分（右像素大于左像素则为True）
            return ''.join(diff.flatten().astype(str))  # 展平并转换为0/1字符串
        except Exception as e:  # 捕获处理过程中的异常
            logger.error(f"计算 dHash 失败: {e}")  # 记录错误日志
            return None  # 返回None表示计算失败

    def hash_distance(self, hash1, hash2):
        """
        计算两个 dHash 的汉明距离（不同字符的个数）

        输入:
            hash1: 第一个哈希字符串
            hash2: 第二个哈希字符串
        返回:
            int: 汉明距离，值越大表示图像差异越大
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):  # 检查哈希是否有效且长度一致
            return float('inf')  # 返回无穷大表示无法比较
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))  # 逐字符比较，统计不同字符个数

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
            current_hash = self.compute_dhash(current_frame)  # 计算当前帧的dHash
            if not current_hash:  # 检查哈希计算是否成功
                return False  # 计算失败则认为无变化

            prev_hash = prev_frame or self.prev_hash  # 使用传入的上一帧或内部保存的哈希
            if not prev_hash:  # 检查是否有上一帧哈希
                self.prev_hash = current_hash  # 保存当前帧作为初始参考
                return False  # 首次检测无变化

            distance = self.hash_distance(current_hash, prev_hash)  # 计算两帧哈希的汉明距离
            changed = distance >= self.hash_diff_threshold  # 判断是否超过阈值

            self.prev_hash = current_hash  # 更新内部保存的哈希
            return changed  # 返回变化检测结果
        except Exception as e:  # 捕获处理过程中的异常
            logger.error(f"检测变化失败: {e}")  # 记录错误日志
            return False  # 返回False表示检测失败

    def detect_bubbles(self, image):
        """
        识别消息气泡，使用颜色过滤和轮廓检测定位微信消息气泡

        输入:
            image: 输入图像 (PIL.Image 或 numpy.ndarray)
        返回:
            list: 检测到的气泡列表，每个元素为字典 {'rect': (x, y, w, h), 'contour': contour}
        """
        try:
            if isinstance(image, str):  # 检查是否为字符串路径（异常情况）
                return []  # 字符串路径不支持直接检测

            if hasattr(image, 'convert'):  # 检查是否为PIL.Image对象
                image_np = np.array(image)  # 转换为numpy数组
            else:
                image_np = image  # 直接使用numpy数组

            if len(image_np.shape) == 3:  # 检查是否为彩色图像（3通道）
                image_hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)  # 转换为HSV颜色空间
            else:  # 灰度图像
                image_hsv = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)  # 先转换为RGB
                image_hsv = cv2.cvtColor(image_hsv, cv2.COLOR_RGB2HSV)  # 再转换为HSV

            mask = cv2.inRange(image_hsv, self.hsv_lower, self.hsv_upper)  # 根据HSV范围创建二值掩码

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))  # 创建5x5矩形结构元素
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 闭运算：填充小孔洞
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # 开运算：去除小噪点

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 查找轮廓

            bubbles = []  # 初始化气泡列表
            for contour in contours:  # 遍历所有轮廓
                x, y, w, h = cv2.boundingRect(contour)  # 获取轮廓的边界矩形

                if h < self.min_height or h > self.max_height:  # 检查高度是否在有效范围内
                    continue  # 跳过不符合高度要求的轮廓
                if w < self.min_width:  # 检查宽度是否满足最小要求
                    continue  # 跳过宽度不足的轮廓
                area = cv2.contourArea(contour)  # 计算轮廓面积
                if area < self.min_area:  # 检查面积是否满足最小要求
                    continue  # 跳过面积不足的轮廓

                bubbles.append({  # 添加符合条件的气泡
                    'rect': (x, y, w, h),  # 边界矩形坐标和尺寸
                    'contour': contour  # 轮廓对象
                })

            bubbles.sort(key=lambda b: b['rect'][1])  # 按Y坐标排序（从上到下）
            return bubbles  # 返回检测到的气泡列表
        except Exception as e:  # 捕获处理过程中的异常
            logger.error(f"检测气泡失败: {e}")  # 记录错误日志
            return []  # 返回空列表表示检测失败


class BoundaryDetector:
    """
    边界检测器

    职责:
        1. 扩展气泡边界以包含头像、昵称等上下文
        2. 确保边界不超出图像范围
    """

    def __init__(self):
        """初始化边界检测器"""
        self.avatar_width = 50  # 微信头像宽度（像素）
        self.nickname_height = 30  # 昵称高度（像素）
        self.padding = 10  # 额外留白（像素）

        logger.info("BoundaryDetector initialized")  # 记录初始化完成日志

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
            x, y, w, h = bubble_rect  # 解包原始气泡矩形
            img_h, img_w = image_shape[:2]  # 获取图像高度和宽度

            new_x = max(0, x - self.avatar_width - self.padding)  # 向左扩展头像宽度和留白，不超出图像左边界
            new_y = max(0, y - self.nickname_height - self.padding)  # 向上扩展昵称高度和留白，不超出图像上边界
            new_w = min(img_w - new_x, w + self.avatar_width + 2 * self.padding)  # 扩展宽度，不超出图像右边界
            new_h = min(img_h - new_y, h + self.nickname_height + 2 * self.padding)  # 扩展高度，不超出图像下边界

            return (new_x, new_y, new_w, new_h)  # 返回扩展后的边界
        except Exception as e:  # 捕获处理过程中的异常
            logger.error(f"扩展边界失败: {e}")  # 记录错误日志
            return bubble_rect  # 返回原始矩形
