"""
生产者1：消息观察者
职责：
1. 监控微信群消息界面
2. 检测新消息和消息气泡位置
3. 返回：消息气泡截图 + 消息气泡内容的像素位置
"""

import threading  # 线程支持
import time  # 时间相关函数
import hashlib  # 哈希计算
from datetime import datetime  # 日期时间处理
from PIL import Image  # 图像处理
import numpy as np  # 数值计算
import cv2  # OpenCV图像处理
import base64  # Base64编码
import io  # 字节流操作
import sys  # 系统相关
import os  # 操作系统接口

from .monitor import VisualMonitor  # 视觉监控器
from .detector import ChangeDetector  # 变化检测器
from .queue_manager import RedisQueueManager  # Redis队列管理器

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # 添加父目录到路径
from utils.logger import logger  # 日志工具
from utils.config import config  # 配置管理

class Producer1Observer:
    """
    生产者1：消息观察者
    
    集成 VisualMonitor 和 ChangeDetector，实现：
    - 持续监控微信窗口ROI区域
    - 检测新消息气泡
    - 返回气泡截图和屏幕像素位置
    """
    
    def __init__(self, queue_manager):
        """
        初始化生产者1
        
        输入:
            queue_manager: 消息队列管理器实例
        """
        self.queue_manager = queue_manager  # Redis队列管理器
        self.monitor = VisualMonitor()  # 视觉监控器实例
        self.detector = ChangeDetector()  # 变化检测器实例
        self.running = False  # 运行状态标志
        self.thread = None  # 工作线程
        
        self.capture_interval = config.get('system.capture_interval_ms', 200) / 1000  # 捕获间隔（秒）
        
        logger.info("Producer1 Observer initialized")  # 记录初始化日志
    
    def _generate_message_id(self, bubble_img):
        """
        生成消息唯一ID（基于图像内容的hash）
        
        输入:
            bubble_img: 气泡截图（PIL Image或numpy数组）
        返回:
            str: 消息ID（SHA256 hash）
        """
        if isinstance(bubble_img, Image.Image):  # 检查是否为PIL Image
            img_array = np.array(bubble_img)  # 转换为numpy数组
        else:
            img_array = bubble_img  # 已经是numpy数组
        
        # 计算图像内容的hash
        img_hash = hashlib.sha256(img_array.tobytes()).hexdigest()  # SHA256哈希
        return f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{img_hash[:12]}"  # 返回唯一ID
    
    def _image_to_base64(self, image):
        """
        将PIL Image转换为base64编码字符串
        
        输入:
            image: PIL Image对象
        返回:
            str: base64编码的图片字符串
        """
        if image is None:  # 检查图像是否为空
            return None  # 返回None
        
        buffered = io.BytesIO()  # 创建字节流缓冲区
        image.save(buffered, format="PNG")  # 保存为PNG格式到缓冲区
        img_bytes = buffered.getvalue()  # 获取字节数据
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')  # Base64编码并解码为字符串
        return img_base64  # 返回base64字符串
    
    def _convert_screen_coords(self, roi_x, roi_y, screen_x, screen_y):
        """
        将ROI内坐标转换为屏幕绝对坐标
        
        输入:
            roi_x, roi_y: ROI内的相对坐标
            screen_x, screen_y: ROI左上角的屏幕坐标
        返回:
            tuple: (screen_abs_x, screen_abs_y)
        """
        return (screen_x + roi_x, screen_y + roi_y)  # 计算绝对坐标并返回
    
    def start(self):
        """启动生产者1线程"""
        if self.running:
            logger.warning("Producer1 Observer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Producer1 Observer started")
    
    def stop(self):
        """停止生产者1线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Producer1 Observer stopped")
    
    def _run(self):
        """
        主循环：持续监控和检测新消息
        """
        try:
            # 定位微信窗口
            self.monitor.locate_wechat()  # 定位微信窗口和子窗口
            if not self.monitor.wechat_window:  # 检查是否定位成功
                logger.error("Failed to locate WeChat window")  # 记录错误日志
                return  # 退出方法
            
            logger.info(f"Monitoring WeChat window: {config.get('monitor.target_group_name')}")  # 记录监控日志
            
            # 获取ROI的屏幕绝对坐标
            roi_screen_x = self.monitor.roi[0]  # ROI左上角X坐标
            roi_screen_y = self.monitor.roi[1]  # ROI左上角Y坐标
            
            while self.running:  # 持续运行直到停止信号
                try:
                    # 1. 截取ROI区域
                    screenshot = self.monitor.capture()  # 截取ROI区域图像
                    if screenshot is None:  # 检查截图是否成功
                        time.sleep(self.capture_interval)  # 等待后继续
                        continue  # 跳过本次循环
                    
                    # 2. 检测变化和新气泡
                    has_changed = self.detector.detect_changes(screenshot)  # 检测是否有变化
                    
                    if has_changed:  # 如果检测到变化
                        # 检测气泡
                        bubbles = self.detector.detect_bubbles(screenshot)  # 检测所有气泡
                        
                        if bubbles:  # 如果有气泡
                            logger.info(f"Detected {len(bubbles)} new bubble(s)")  # 记录检测日志
                            
                            for bubble_info in bubbles:  # 遍历所有气泡
                                bubble_rect = bubble_info['rect']  # 获取气泡矩形
                            try:
                                # bubble_rect格式: (x, y, w, h) - ROI内坐标
                                roi_x, roi_y, w, h = bubble_rect  # 解包矩形坐标和尺寸
                                
                                # 计算气泡中心点的屏幕绝对坐标
                                center_x = roi_x + w // 2  # 中心X坐标
                                center_y = roi_y + h // 2  # 中心Y坐标
                                screen_abs_x, screen_abs_y = self._convert_screen_coords(  # 转换为绝对坐标
                                    center_x, center_y, roi_screen_x, roi_screen_y
                                )
                                
                                # 截取气泡图像
                                bubble_img = screenshot.crop((roi_x, roi_y, roi_x + w, roi_y + h))  # 裁剪气泡区域
                                
                                # 生成消息ID
                                msg_id = self._generate_message_id(bubble_img)  # 生成唯一ID
                                
                                # 构造消息数据（将PIL Image转换为base64字符串）
                                message_data = {
                                    'id': msg_id,  # 消息ID
                                    'timestamp': datetime.now().isoformat(),  # 时间戳
                                    'type': 'raw_bubble',  # 消息类型
                                    'bubble_img_base64': self._image_to_base64(bubble_img),  # 气泡图像base64
                                    'position': {  # 位置信息
                                        'roi_x': roi_x,  # ROI内X坐标
                                        'roi_y': roi_y,  # ROI内Y坐标
                                        'screen_x': screen_abs_x,  # 屏幕绝对X坐标
                                        'screen_y': screen_abs_y,  # 屏幕绝对Y坐标
                                        'width': w,  # 宽度
                                        'height': h  # 高度
                                    },
                                    'priority': 10,  # 优先级
                                    'metadata': {  # 元数据
                                        'producer': 'producer1_observer',  # 生产者标识
                                        'detection_time': datetime.now().isoformat()  # 检测时间
                                    }
                                }
                                
                                # 入队到raw队列
                                self.queue_manager.enqueue_raw(message_data)  # 将消息入队
                                logger.info(f"Producer1: Enqueued raw bubble {msg_id} at ({screen_abs_x}, {screen_abs_y})")  # 记录入队日志
                                
                            except Exception as e:  # 捕获处理异常
                                logger.error(f"Error processing bubble {bubble_rect}: {e}")  # 记录错误日志
                                continue  # 继续处理下一个气泡
                    
                    time.sleep(self.capture_interval)  # 等待下次捕获
                    
                except Exception as e:  # 捕获主循环异常
                    logger.error(f"Error in Producer1 main loop: {e}")  # 记录错误日志
                    time.sleep(1)  # 等待1秒后继续
                    
        except Exception as e:  # 捕获方法级异常
            logger.error(f"Producer1 Observer failed: {e}")  # 记录错误日志
        finally:
            self.running = False  # 确保运行状态设置为False
