"""
生产者2：内容获取者
职责：
1. 从raw队列读取消息气泡位置
2. 点击消息气泡获取更精确的聊天内容
3. 返回：高精内容（文本/高清图片）
"""

import threading
import time
import os
from datetime import datetime
from PIL import Image
import base64
import io
import sys
import json

from .queue_manager import RedisQueueManager
from .extractor import PrecisionContentFetcher
from .classifier import MessageTypeClassifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger
from utils.config import config

class Producer2ContentFetcher:
    """
    生产者2：内容获取者
    
    集成 PrecisionContentFetcher，实现：
    - 从raw队列读取气泡位置
    - 点击气泡获取精确内容
    - 返回文本内容或高清图片
    """
    
    def __init__(self, queue_manager):
        """
        初始化生产者2
        
        输入:
            queue_manager: 消息队列管理器实例
        """
        self.queue_manager = queue_manager
        self.content_fetcher = PrecisionContentFetcher()
        self.classifier = MessageTypeClassifier()
        self.running = False
        self.thread = None
        
        self.save_directory = config.get('system.save_directory', './data')
        self.media_directory = os.path.join(self.save_directory, 'media')
        
        if not os.path.exists(self.media_directory):
            os.makedirs(self.media_directory)
        
        logger.info("Producer2 ContentFetcher initialized")
    
    def _save_media(self, image, msg_id):
        """
        保存高清图片到本地
        
        输入:
            image: PIL Image对象
            msg_id: 消息ID
        返回:
            str: 保存的文件路径
        """
        filename = f"{msg_id}_high_res.png"
        filepath = os.path.join(self.media_directory, filename)
        
        try:
            image.save(filepath, 'PNG')
            logger.info(f"Saved high-res image: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save image {filepath}: {e}")
            return None
    
    def _base64_to_image(self, base64_str):
        """
        将base64字符串转换为PIL Image
        
        输入:
            base64_str: base64编码的图片字符串
        返回:
            PIL.Image: PIL Image对象
        """
        if not base64_str:
            return None
        
        try:
            img_bytes = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(img_bytes))
            return image
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            return None
    
    def _image_to_base64(self, image):
        """
        将PIL Image转换为base64编码字符串
        
        输入:
            image: PIL Image对象
        返回:
            str: base64编码的图片字符串
        """
        if image is None:
            return None
        
        try:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
        except Exception as e:
            logger.error(f"Failed to encode image to base64: {e}")
            return None
    
    def start(self):
        """启动生产者2线程"""
        if self.running:
            logger.warning("Producer2 ContentFetcher is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Producer2 ContentFetcher started")
    
    def stop(self):
        """停止生产者2线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Producer2 ContentFetcher stopped")
    
    def _run(self):
        """
        主循环：从raw队列读取消息，点击获取精确内容
        """
        try:
            while self.running:
                try:
                    # 从raw队列获取消息（使用Redis消费者组）
                    messages = self.queue_manager.read_raw_for_processing(block=True, timeout=1000)
                    
                    if not messages:
                        continue
                    
                    for redis_msg_id, raw_message in messages:
                        msg_id = raw_message['id']
                        position = raw_message['position']
                        
                        # 将base64转换回PIL Image
                        bubble_img = self._base64_to_image(raw_message['bubble_img_base64'])
                        if bubble_img is None:
                            logger.error(f"Producer2: Failed to decode bubble image for {msg_id}")
                            self.queue_manager.ack_raw(redis_msg_id)
                            continue
                        
                        screen_x = position['screen_x']
                        screen_y = position['screen_y']
                        
                        logger.info(f"Producer2: Processing message {msg_id} at ({screen_x}, {screen_y})")
                        
                        # 1. 分类消息类型（先进行非交互式分类）
                        import numpy as np
                        bubble_array = np.array(bubble_img)
                        msg_type = self.classifier.classify(bubble_array)
                        
                        # 2. 根据类型获取精确内容
                        precise_content = {
                            'type': msg_type,
                            'text': None,
                            'media_path': None,
                            'media_image_base64': None
                        }
                        
                        if msg_type == 'text':
                            # 尝试双击复制文本
                            text_content = self.content_fetcher.fetch_text(screen_x, screen_y)
                            if text_content:
                                precise_content['text'] = text_content
                                logger.info(f"Producer2: Fetched text for {msg_id}: {text_content[:50]}...")
                            else:
                                logger.warning(f"Producer2: Failed to fetch text for {msg_id}")
                        
                        elif msg_type in ['image', 'video']:
                            # 点击打开媒体查看器，获取高清图
                            media_img = self.content_fetcher.fetch_media(screen_x, screen_y)
                            if media_img:
                                # 保存高清图片
                                media_path = self._save_media(media_img, msg_id)
                                if media_path:
                                    precise_content['media_path'] = media_path
                                    precise_content['media_image_base64'] = self._image_to_base64(media_img)
                                    logger.info(f"Producer2: Fetched high-res image for {msg_id}: {media_path}")
                            else:
                                logger.warning(f"Producer2: Failed to fetch media for {msg_id}")
                        
                        else:
                            logger.info(f"Producer2: Skipping message type {msg_type} for {msg_id}")
                        
                        # 3. 构造完整消息数据
                        enhanced_message = {
                            'id': msg_id,
                            'timestamp': raw_message['timestamp'],
                            'type': msg_type,
                            'bubble_img_base64': raw_message['bubble_img_base64'],
                            'position': position,
                            'precise_content': precise_content,
                            'priority': 10,
                            'metadata': {
                                'producer': 'producer2_content_fetcher',
                                'processed_at': datetime.now().isoformat(),
                                'raw_message': raw_message.get('metadata', {})
                            }
                        }
                        
                        # 4. 入队到precise队列供外部消费
                        self.queue_manager.enqueue_precise(enhanced_message)
                        logger.info(f"Producer2: Enqueued precise message {msg_id}")
                        
                        # 5. 确认消息处理完成
                        self.queue_manager.ack_raw(redis_msg_id)
                    
                except Exception as e:
                    logger.error(f"Error processing message in Producer2: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Producer2 ContentFetcher failed: {e}")
        finally:
            self.running = False
