"""
消息内容提取模块（已废弃）

⚠️ 此文件已废弃，原因是：
- 导入的模块不存在（..platform.adapter）
- 功能已被 message_extractor.py 替代
- 请使用 core.extractor.message_extractor.UniversalMessageExtractor

保留此文件仅用于历史参考，请勿在新代码中使用。
"""

# 以下导入已失效，注释掉以避免 ImportError
# import time
# import cv2
# import numpy as np
# import subprocess
# import mss
# from utils.logger import logger
# from config.config import config
# from ..platform.adapter import get_adapter

import warnings
warnings.warn(
    "extractor.py 已废弃，请使用 message_extractor.py 替代。",
    DeprecationWarning,
    stacklevel=2
)

class MessageExtractor:
    """
    消息区域提取器
    
    职责:
        提供图像裁剪等辅助功能
    """
    
    def extract_compact(self, full_image, crop_coords):
        """
        从完整截图中裁剪出消息区域 (小截图)
        
        输入:
            full_image: 完整屏幕截图
            crop_coords: (x1, y1, x2, y2)
        返回:
            numpy.ndarray: 裁剪后的图像
        """
        try:
            x1, y1, x2, y2 = crop_coords
            h, w = full_image.shape[:2]
            x1 = max(0, int(x1))
            y1 = max(0, int(y1))
            x2 = min(w, int(x2))
            y2 = min(h, int(y2))
            
            return full_image[y1:y2, x1:x2]
        except Exception as e:
            logger.error(f"Extract compact failed: {e}")
            return None

class PrecisionContentFetcher:
    """
    精确内容获取器（跨平台版本）
    
    职责:
        通过模拟用户交互（双击、点击）来获取消息的真实内容。
        - 文本消息: 双击复制
        - 图片/视频: 点击打开查看器并截图
    """
    
    def __init__(self):
        """加载配置和平台适配器"""
        self.double_click_interval = 0.1
        self.clipboard_timeout = 1.0
        self.media_load_timeout = 3.0
        self.adapter = get_adapter()
        logger.info("PrecisionContentFetcher initialized")

    def fetch_text(self, screen_x, screen_y):
        """
        获取文本消息的精确内容
        
        动作序列:
            1. 移动鼠标到指定位置
            2. 双击消息气泡选中文本
            3. 模拟 Ctrl+C 复制
            4. 从剪贴板读取内容
            5. 清除剪贴板
        
        输入:
            screen_x: 屏幕绝对坐标 X
            screen_y: 屏幕绝对坐标 Y
        返回:
            str: 复制的文本内容，失败返回 None
        """
        try:
            self.adapter.double_click(screen_x, screen_y)
            time.sleep(self.double_click_interval)
            
            self.adapter.copy_to_clipboard()
            time.sleep(self.clipboard_timeout)
            
            text_content = self.adapter.get_clipboard()
            
            if text_content:
                logger.info(f"成功获取文本内容: {text_content[:50]}...")
                return text_content
            else:
                logger.warning("剪贴板内容为空")
                return None
                
        except Exception as e:
            logger.error(f"获取文本内容失败: {e}")
            return None

    def _close_media_viewer(self):
        """关闭媒体查看器（跨平台）"""
        try:
            import platform
            system = platform.system().lower()
            if system == 'linux':
                subprocess.run(['xdotool', 'key', 'Escape'], check=True)
            elif system == 'windows':
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                VK_ESCAPE = 0x1B
                KEYEVENTF_KEYDOWN = 0x0000
                KEYEVENTF_KEYUP = 0x0002
                user32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYDOWN, 0)
                time.sleep(0.01)
                user32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            logger.error(f"关闭媒体查看器失败: {e}")

    def fetch_media(self, screen_x, screen_y):
        """
        获取媒体消息的精确内容（图片/视频）
        
        动作序列:
            1. 点击消息气泡打开媒体查看器
            2. 等待媒体加载
            3. 截取屏幕（使用 mss，兼容 Docker Xvfb）
            4. 关闭查看器
        
        输入:
            screen_x: 屏幕绝对坐标 X
            screen_y: 屏幕绝对坐标 Y
        返回:
            PIL.Image: 媒体截图，失败返回 None
        """
        try:
            self.adapter.click_mouse(screen_x, screen_y)
            time.sleep(self.media_load_timeout)
            
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                screenshot = sct.grab(monitor)
                from PIL import Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            self._close_media_viewer()
            
            logger.info("成功获取媒体截图")
            return img
            
        except Exception as e:
            logger.error(f"获取媒体内容失败: {e}")
            return None

    def fetch_content(self, screen_x, screen_y, message_type='text'):
        """
        根据消息类型获取精确内容
        
        输入:
            screen_x: 屏幕绝对坐标 X
            screen_y: 屏幕绝对坐标 Y
            message_type: 消息类型 ('text' 或 'media')
        返回:
            dict: 包含内容的字典 {'type': ..., 'content': ...}
        """
        if message_type == 'text':
            text = self.fetch_text(screen_x, screen_y)
            return {'type': 'text', 'content': text} if text else None
        elif message_type == 'media':
            image = self.fetch_media(screen_x, screen_y)
            return {'type': 'media', 'content': image} if image else None
        else:
            logger.warning(f"未知消息类型: {message_type}")
            return None
