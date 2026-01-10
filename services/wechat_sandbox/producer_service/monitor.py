"""
视觉监控核心模块（Linux微信版本）
负责调用操作系统 API 和图像处理库，实现对微信窗口的定位、ROI 设定和屏幕截取。

功能说明:
- 使用 xdotool 定位微信窗口
- 使用 PIL.ImageGrab 截取屏幕
- 支持自定义 ROI（感兴趣区域）配置
- 线程安全的配置管理
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

    使用方法:
        monitor = VisualMonitor()
        monitor.set_roi(left, top, right, bottom)
        monitor.start_monitoring(callback=screenshot_handler, interval=0.2)
    """

    def __init__(self):
        """
        初始化监控器

        初始化内容:
        - 微信窗口 ID（使用 xdotool 获取）
        - 子窗口 ID（暂未实现）
        - ROI 坐标（从配置文件加载或默认为 None）
        - 监控间隔（默认 200ms）
        - 运行状态标志
        - 线程安全锁
        """
        self.wechat_window = None  # 微信主窗口 ID
        self.sub_window = None  # 消息渲染子窗口 ID
        self.roi = None  # 监控区域坐标 (left, top, right, bottom)
        self.interval = 0.2  # 截图间隔（秒），默认 200ms
        self.running = False  # 监控运行状态标志
        self.config_lock = threading.Lock()  # 配置更新锁，保证线程安全

        # 从配置文件加载 ROI 设置
        self.load_roi_from_config()

        logger.info("VisualMonitor (Linux WeChat) initialized")

    def load_roi_from_config(self):
        """
        从配置文件加载 ROI 设置

        配置文件路径: ../config.yaml
        配置格式:
            roi:
              presets:
                send_area:
                  coordinates: [left, top, right, bottom]
                receive_area:
                  coordinates: [left, top, right, bottom]
              active_preset: receive_area
        """
        try:
            import yaml
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                    if cfg and 'roi' in cfg:
                        roi_config = cfg['roi']
                        
                        # 支持新格式：multi-preset
                        if isinstance(roi_config, dict) and 'presets' in roi_config:
                            active_preset = roi_config.get('active_preset', 'receive_area')
                            if active_preset in roi_config['presets']:
                                coordinates = roi_config['presets'][active_preset]['coordinates']
                                self.roi = tuple(coordinates)
                                logger.info(f"已加载 ROI (预设: {active_preset}): {self.roi}")
                        # 兼容旧格式：flat list
                        elif isinstance(roi_config, list) and len(roi_config) == 4:
                            self.roi = tuple(roi_config)
                            logger.info(f"已加载 ROI (旧格式): {self.roi}")
        except Exception as e:
            logger.warning(f"加载 ROI 配置失败: {e}")

    def set_roi(self, left, top, right, bottom):
        """
        设置监控区域（感兴趣区域）

        参数:
            left: 左边界像素坐标
            top: 上边界像素坐标
            right: 右边界像素坐标
            bottom: 下边界像素坐标

        注意:
            - 使用线程锁确保配置更新的线程安全
            - 坐标范围应与屏幕分辨率匹配
        """
        with self.config_lock:
            self.roi = (left, top, right, bottom)
            logger.info(f"ROI 已更新: {self.roi}")

    def locate_wechat(self):
        """
        定位微信窗口及消息渲染区域（Linux版本）

        方法:
            使用 xdotool 搜索包含 'WeChat' 的窗口名称

        注意:
            - 此实现需要根据 Linux 微信的实际窗口名称进行调整
            - 如果微信窗口名称不是 'WeChat'，需要修改搜索参数

        返回:
            bool: 是否成功找到窗口
        """
        try:
            # 使用 xdotool 查找微信窗口
            # 注意：窗口名称可能因微信版本或语言设置而不同
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'WeChat'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                # 获取第一个匹配的窗口 ID
                window_id = result.stdout.strip().split('\n')[0]
                self.wechat_window = window_id
                logger.info(f"已找到微信窗口 ID: {window_id}")

                # 获取窗口几何信息（位置和尺寸）
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

        方法:
            使用 PIL.ImageGrab 截取屏幕截图

        参数:
            roi: 区域坐标 (left, top, right, bottom)，None 则截取全屏

        返回:
            PIL.Image: 截取的图像对象
            None: 截图失败时返回

        注意:
            - 在无头环境（如 Docker）中，需要使用虚拟显示（xvfb）
            - 截图分辨率受显示设置影响
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
