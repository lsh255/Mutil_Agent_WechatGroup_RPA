"""
配置工具模块
"""

import os

class Config:
    """配置类"""
    
    def __init__(self):
        """初始化配置"""
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        self.REDIS_DB = int(os.getenv('REDIS_DB', 0))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
        self.REDIS_STREAM_RAW = os.getenv('REDIS_STREAM_RAW', 'wechat:messages:raw')
        self.REDIS_STREAM_PRECISE = os.getenv('REDIS_STREAM_PRECISE', 'wechat:messages:precise')
        self.MEDIA_DIR = os.getenv('MEDIA_DIR', './media')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'db': self.REDIS_DB,
            'password': self.REDIS_PASSWORD,
            'stream_raw': self.REDIS_STREAM_RAW,
            'stream_precise': self.REDIS_STREAM_PRECISE
        }

config = Config()
