"""
消息内容提取模块（Linux微信版本）
负责从屏幕上提取消息的详细内容（文本或媒体）。
包含两个类：
1. MessageExtractor: 图像裁剪辅助类
2. PrecisionContentFetcher: 基于自动化操作（点击/复制）的内容获取器
"""

import time
import cv2
import numpy as np
import subprocess
from PIL import ImageGrab
from utils.logger import logger
from utils.config import config

def click_mouse(x, y):
    """
    模拟系统级鼠标点击（Linux版本，使用 xdotool）
    
    输入:
        x: 屏幕X坐标
        y: 屏幕Y坐标
    """
    try:
        subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
        subprocess.run(['xdotool', 'click', '1'], check=True)
    except Exception as e:
        logger.error(f"模拟鼠标点击失败: {e}")

def double_click(x, y):
    """
    模拟鼠标双击（Linux版本）
    
    输入:
        x: 屏幕X坐标
        y: 屏幕Y坐标
    """
    try:
        subprocess.run(['xdotool', 'mousemove', str(x), str(y)], check=True)
        subprocess.run(['xdotool', 'click', '--repeat', '2', '1'], check=True)
    except Exception as e:
        logger.error(f"模拟鼠标双击失败: {e}")

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
            x1, y1, x2, y2 = crop_coords  # 解包裁剪坐标
            # 确保坐标在图像范围内
            h, w = full_image.shape[:2]  # 获取图像高度和宽度
            x1 = max(0, int(x1))  # 确保x1不小于0
            y1 = max(0, int(y1))  # 确保y1不小于0
            x2 = min(w, int(x2))  # 确保x2不大于图像宽度
            y2 = min(h, int(y2))  # 确保y2不大于图像高度
            
            return full_image[y1:y2, x1:x2]  # 裁剪图像区域
        except Exception as e:  # 捕获异常
            logger.error(f"Extract compact failed: {e}")  # 记录错误日志
            return None  # 返回None表示失败

class PrecisionContentFetcher:
    """
    精确内容获取器（Linux微信版本）
    
    职责:
        通过模拟用户交互（双击、点击）来获取消息的真实内容。
        - 文本消息: 双击复制
        - 图片/视频: 点击打开查看器并截图
    """
    
    def __init__(self):
        """加载配置"""
        self.double_click_interval = 0.1  # 双击间隔时间（秒）
        self.clipboard_timeout = 1.0  # 剪贴板读取超时时间（秒）
        self.media_load_timeout = 3.0  # 媒体加载超时时间（秒）
        logger.info("PrecisionContentFetcher (Linux) initialized")  # 记录初始化日志

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
            # 双击消息气泡
            double_click(screen_x, screen_y)
            time.sleep(self.double_click_interval)
            
            # 模拟 Ctrl+C 复制
            subprocess.run(['xdotool', 'key', 'Ctrl+c'], check=True)
            time.sleep(self.clipboard_timeout)
            
            # 读取剪贴板内容
            try:
                result = subprocess.run(
                    ['xclip', '-selection', 'clipboard', '-o'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                text_content = result.stdout.strip()
            except:
                # 如果 xclip 不可用，尝试使用其他方法
                text_content = ""
            
            if text_content:
                logger.info(f"成功获取文本内容: {text_content[:50]}...")
                return text_content
            else:
                logger.warning("剪贴板内容为空")
                return None
                
        except Exception as e:
            logger.error(f"获取文本内容失败: {e}")
            return None

    def fetch_media(self, screen_x, screen_y):
        """
        获取媒体消息的精确内容（图片/视频）
        
        动作序列:
            1. 点击消息气泡打开媒体查看器
            2. 等待媒体加载
            3. 截取屏幕
            4. 关闭查看器
        
        输入:
            screen_x: 屏幕绝对坐标 X
            screen_y: 屏幕绝对坐标 Y
        返回:
            PIL.Image: 媒体截图，失败返回 None
        """
        try:
            # 点击消息气泡
            click_mouse(screen_x, screen_y)
            time.sleep(self.media_load_timeout)
            
            # 截取全屏
            screenshot = ImageGrab.grab()
            
            # 关闭查看器（按 ESC 键）
            subprocess.run(['xdotool', 'key', 'Escape'])
            
            logger.info("成功获取媒体截图")
            return screenshot
            
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
        if message_type == 'text':  # 文本消息
            text = self.fetch_text(screen_x, screen_y)  # 获取文本内容
            return {'type': 'text', 'content': text} if text else None  # 返回文本字典或None
        elif message_type == 'media':  # 媒体消息
            image = self.fetch_media(screen_x, screen_y)  # 获取媒体截图
            return {'type': 'media', 'content': image} if image else None  # 返回媒体字典或None
        else:  # 未知类型
            logger.warning(f"未知消息类型: {message_type}")  # 记录警告日志
            return None  # 返回None表示失败
