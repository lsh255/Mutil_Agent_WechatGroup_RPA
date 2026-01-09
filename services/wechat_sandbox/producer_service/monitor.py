"""
视觉监控核心模块（Linux微信版本）
负责调用操作系统 API 和图像处理库，实现对微信窗口的定位、ROI 设定和屏幕截取。
"""

import time
import os
import threading
import subprocess
import numpy as np
from PIL import ImageGrab
import cv2

from utils.logger import logger
from utils.config import config

class VisualMonitor:
    """
    视觉监控器类（Linux微信版本）
    
    职责:
        1. 定位微信主窗口和消息渲染子窗口
        2. 管理监控区域 (ROI) 的设定和坐标计算
        3. 按照指定频率截取屏幕图像
    """

    def __init__(self):
        """初始化监控器"""
        self.wechat_window = None
        self.sub_window = None
        self.roi = None  # (left, top, right, bottom)
        self.interval = 0.2  # 默认 200ms
        self.running = False
        self.config_lock = threading.Lock()
        
        # 从配置加载 ROI
        self.load_roi_from_config()
        
        logger.info("VisualMonitor (Linux WeChat) initialized")

    def load_roi_from_config(self):
        """从配置文件加载 ROI"""
        try:
            import yaml
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                    if cfg and 'roi' in cfg:
                        self.roi = tuple(cfg['roi'])
                        logger.info(f"已加载 ROI: {self.roi}")
        except Exception as e:
            logger.warning(f"加载 ROI 配置失败: {e}")

    def set_roi(self, left, top, right, bottom):
        """
        设置监控区域
        
        输入:
            left: 左边界
            top: 上边界
            right: 右边界
            bottom: 下边界
        """
        with self.config_lock:
            self.roi = (left, top, right, bottom)
            logger.info(f"ROI 已更新: {self.roi}")

    def locate_wechat(self):
        """
        定位微信窗口及消息渲染区域（Linux版本）
        
        注意：此实现需要根据 Linux 微信的实际窗口结构进行调整
        
        返回:
            bool: 是否成功找到窗口
        """
        try:
            # 使用 xdotool 或 wmctrl 查找微信窗口
            # 这里需要根据实际 Linux 微信的窗口名称进行调整
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'WeChat'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                window_id = result.stdout.strip().split('\n')[0]
                self.wechat_window = window_id
                logger.info(f"已找到微信窗口 ID: {window_id}")
                
                # 获取窗口几何信息
                geom_result = subprocess.run(
                    ['xdotool', 'getwindowgeometry', window_id],
                    capture_output=True,
                    text=True
                )
                
                if geom_result.returncode == 0:
                    logger.info(f"窗口几何信息: {geom_result.stdout}")
                
                return True
            else:
                logger.warning("未找到微信窗口")
                return False
                
        except Exception as e:
            logger.error(f"定位微信窗口时发生错误: {e}")
            return False

    def capture_screen(self, roi=None):
        """
        截取屏幕或指定区域
        
        输入:
            roi: 区域坐标 (left, top, right, bottom)，None 则截取全屏
        返回:
            PIL.Image: 截取的图像
        """
        try:
            if roi:
                image = ImageGrab.grab(bbox=roi)
            else:
                image = ImageGrab.grab()
            return image
        except Exception as e:
            logger.error(f"截屏失败: {e}")
            return None

    def start_monitoring(self, callback, interval=None):
        """
        启动监控线程
        
        输入:
            callback: 截图回调函数
            interval: 截图间隔（秒）
        """
        if self.running:
            logger.warning("监控已在运行")
            return
        
        self.running = True
        self.interval = interval or self.interval
        
        def monitor_loop():
            while self.running:
                try:
                    screenshot = self.capture_screen(self.roi)
                    if screenshot and callback:
                        callback(screenshot)
                except Exception as e:
                    logger.error(f"监控循环错误: {e}")
                time.sleep(self.interval)
        
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
        logger.info("监控线程已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("监控已停止")
