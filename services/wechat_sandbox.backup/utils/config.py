"""
配置工具模块
"""

import os  # 操作系统接口，用于读取环境变量

class Config:
    """配置类，管理Redis连接和消息队列配置"""

    def __init__(self):
        """初始化配置，从环境变量读取配置项，使用默认值"""
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')  # Redis服务器地址，默认localhost
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))  # Redis服务器端口，默认6379
        self.REDIS_DB = int(os.getenv('REDIS_DB', 0))  # Redis数据库编号，默认0
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)  # Redis密码，默认无密码
        self.REDIS_STREAM_RAW = os.getenv('REDIS_STREAM_RAW', 'wechat:messages:raw')  # 原始消息流名称，默认wechat:messages:raw
        self.REDIS_STREAM_PRECISE = os.getenv('REDIS_STREAM_PRECISE', 'wechat:messages:precise')  # 精确消息流名称，默认wechat:messages:precise
        self.MEDIA_DIR = os.getenv('MEDIA_DIR', './media')  # 媒体文件存储目录，默认./media
        
        self.system = type('obj', (object,), {
            'capture_interval_ms': int(os.getenv('CAPTURE_INTERVAL_MS', '200')),
            'save_directory': os.getenv('SAVE_DIRECTORY', './data')
        })
        self.monitor = type('obj', (object,), {
            'target_group_name': os.getenv('TARGET_GROUP_NAME', 'Test Group')
        })

    def get(self, key, default=None):
        """字典式访问配置"""
        if '.' in key:
            parts = key.split('.')
            result = self
            for part in parts:
                if hasattr(result, part):
                    result = getattr(result, part)
                else:
                    return default
            return result
        else:
            return getattr(self, key, default)

    def to_dict(self):
        """转换为字典，用于Redis客户端初始化"""
        return {
            'host': self.REDIS_HOST,  # Redis主机地址
            'port': self.REDIS_PORT,  # Redis端口
            'db': self.REDIS_DB,  # Redis数据库编号
            'password': self.REDIS_PASSWORD,  # Redis密码
            'stream_raw': self.REDIS_STREAM_RAW,  # 原始消息流名称
            'stream_precise': self.REDIS_STREAM_PRECISE  # 精确消息流名称
        }

config = Config()  # 创建全局配置实例
