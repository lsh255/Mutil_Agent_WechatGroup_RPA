"""
微信窗口监控器
职责：
1. 定位微信窗口
2. 定义消息监控区域（ROI）
3. 抓取ROI区域截图
"""

import threading
import time
import subprocess
from PIL import ImageGrab, Image
from typing import Optional, Tuple
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from config.config import config

class VisualMonitor:
    """
    微信窗口监控器
    
    使用系统命令定位窗口
    定时截取指定ROI区域
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.wechat_window = None
        self.roi = config.get('monitor.roi', [0, 0, 400, 600])
        self.refresh_interval = config.get('monitor.window_check_interval', 60)
        self.last_check_time = 0
        
        logger.info("VisualMonitor initialized")
    
    def _locate_window_linux(self):
        try:
            result = subprocess.run(
                ['xdotool', 'search', '--name', 'WeChat'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.wechat_window = result.stdout.strip().split('\n')[0]
                logger.info(f"WeChat window located: {self.wechat_window}")
                return True
            
            logger.warning("WeChat window not found on Linux")
            return False
            
        except FileNotFoundError:
            logger.error("xdotool not found. Please install: sudo apt install xdotool")
            return False
        except Exception as e:
            logger.error(f"Error locating WeChat window on Linux: {e}")
            return False
    
    def _locate_window_windows(self):
        try:
            import win32gui
            import win32process
            
            def callback(hwnd, windows):
                title = win32gui.GetWindowText(hwnd)
                if 'WeChat' in title:
                    windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(callback, windows)
            
            if windows:
                self.wechat_window = str(windows[0])
                logger.info(f"WeChat window located: {self.wechat_window}")
                return True
            
            logger.warning("WeChat window not found on Windows")
            return False
            
        except ImportError:
            logger.error("pywin32 not found. Please install: pip install pywin32")
            return False
        except Exception as e:
            logger.error(f"Error locating WeChat window on Windows: {e}")
            return False
    
    def locate_wechat(self) -> bool:
        with self.lock:
            current_time = time.time()
            
            if current_time - self.last_check_time < self.refresh_interval:
                return self.wechat_window is not None
            
            self.last_check_time = current_time
            
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                return self._locate_window_linux()
            elif system == 'windows':
                return self._locate_window_windows()
            else:
                logger.error(f"Unsupported platform: {system}")
                return False
    
    def capture(self) -> Optional[Image.Image]:
        try:
            if not self.locate_wechat():
                logger.warning("Cannot capture: WeChat window not located")
                return None
            
            x, y, w, h = self.roi
            
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                logger.error(f"Invalid ROI: {self.roi}")
                return None
            
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            
            if screenshot is None or screenshot.size == (0, 0):
                logger.warning("Captured empty image")
                return None
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def update_roi(self, new_roi: Tuple[int, int, int, int]):
        with self.lock:
            x, y, w, h = new_roi
            if x < 0 or y < 0 or w <= 0 or h <= 0:
                logger.error(f"Invalid new ROI: {new_roi}")
                return False
            
            old_roi = self.roi
            self.roi = list(new_roi)
            logger.info(f"ROI updated: {old_roi} -> {self.roi}")
            return True
    
    def get_window_geometry(self) -> Optional[Tuple[int, int, int, int]]:
        if not self.wechat_window:
            return None
        
        try:
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                result = subprocess.run(
                    ['xdotool', 'getwindowgeometry', self.wechat_window],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Position:' in line:
                            pos = line.split(':')[1].strip()
                            x, y = map(int, pos.split(','))
                        elif 'Geometry:' in line:
                            geom = line.split(':')[1].strip()
                            w, h = map(int, geom.split('x'))
                    
                    return (x, y, w, h)
                    
            elif system == 'windows':
                import win32gui
                rect = win32gui.GetWindowRect(int(self.wechat_window))
                return rect
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting window geometry: {e}")
            return None
