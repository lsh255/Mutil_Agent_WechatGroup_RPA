"""
精确内容提取器
职责：
1. 点击消息气泡（精确位置）
2. 复制到剪贴板
3. 获取剪贴板内容（文本）
4. 点击图片下载按钮并获取高清图片
"""

import time
import base64
import io
from PIL import Image
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from utils.platform_adapter import get_adapter

class PrecisionContentFetcher:
    """
    精确内容提取器
    
    使用 PlatformAdapter 实现跨平台的鼠标和剪贴板操作
    """
    
    def __init__(self):
        self.adapter = get_adapter()
        logger.info("PrecisionContentFetcher initialized")
    
    def fetch_text(self, screen_x: int, screen_y: int) -> Optional[str]:
        try:
            self.adapter.double_click(screen_x, screen_y)
            time.sleep(0.1)
            
            self.adapter.copy_to_clipboard()
            time.sleep(0.1)
            
            text_content = self.adapter.get_clipboard()
            
            if text_content:
                logger.debug(f"Fetched text: {text_content[:50]}...")
                return text_content
            else:
                logger.warning("Clipboard is empty after copy")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching text: {e}")
            return None
    
    def fetch_media(self, screen_x: int, screen_y: int) -> Optional[Image.Image]:
        try:
            import mss
            with mss.mss() as sct:
                monitor = {"top": screen_y, "left": screen_x, "width": 400, "height": 400}
                screenshot = sct.grab(monitor)
                image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                logger.debug(f"Fetched media image at ({screen_x}, {screen_y})")
                return image
                
        except Exception as e:
            logger.error(f"Error fetching media: {e}")
            return None
    
    def click(self, x: int, y: int) -> bool:
        try:
            result = self.adapter.click_mouse(x, y)
            if result:
                logger.debug(f"Clicked at ({x}, {y})")
            return result
        except Exception as e:
            logger.error(f"Error clicking at ({x}, {y}): {e}")
            return False
