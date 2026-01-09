"""
双生产者队列管理器（基于Redis）
职责：
1. 使用Redis Stream存储消息队列
2. 提供生产者入队操作
3. 管理消息去重
"""

import json
import hashlib
import redis
from utils.logger import logger
from utils.config import config

class RedisQueueManager:
    """
    基于Redis的双队列管理器
    
    管理两个Redis Stream：
    - stream_raw: 原始消息队列（生产者1 -> 生产者2）
    - stream_precise: 精确消息队列（生产者2 -> 外部消费）
    """
    
    def __init__(self, redis_config=None):
        """
        初始化Redis队列管理器
        
        输入:
            redis_config: Redis配置字典，如果为None则从config读取
        """
        if redis_config is None:
            redis_config = config.get('redis', {})
        
        self.redis_client = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password', None),
            decode_responses=False
        )
        
        self.stream_raw = redis_config.get('stream_raw', 'wechat:messages:raw')
        self.stream_precise = redis_config.get('stream_precise', 'wechat:messages:precise')
        self.max_length = redis_config.get('max_length', 10000)
        
        self.consumer_group_raw = 'producer2_group'
        self.consumer_group_precise = 'external_consumers'
        self.consumer_name = f"producer_service_{config.get('system.instance_id', 'default')}"
        
        self._init_streams()
        
        logger.info("RedisQueueManager initialized")
    
    def _init_streams(self):
        """初始化Redis Stream和消费者组"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection successful")
            
            for stream, group in [(self.stream_raw, self.consumer_group_raw), 
                                  (self.stream_precise, self.consumer_group_precise)]:
                try:
                    self.redis_client.xgroup_create(
                        name=stream,
                        groupname=group,
                        id='0',
                        mkstream=True
                    )
                    logger.info(f"Created consumer group {group} for stream {stream}")
                except redis.ResponseError as e:
                    if 'BUSYGROUP' in str(e):
                        logger.debug(f"Consumer group {group} already exists for stream {stream}")
                    else:
                        logger.warning(f"Error creating group {group}: {e}")
                        
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _prepare_message_data(self, item):
        """
        准备消息数据，序列化为JSON
        
        输入:
            item: 消息字典
        返回:
            dict: 序列化后的消息数据
        """
        message_data = {}
        for key, value in item.items():
            if key == 'bubble_img' or key == 'media_img':
                value = value.tobytes() if hasattr(value, 'tobytes') else value
            message_data[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        return message_data
    
    def _generate_message_id(self, item):
        """
        生成消息唯一ID（基于内容hash）
        
        输入:
            item: 消息字典
        返回:
            str: 消息ID
        """
        content = json.dumps(item, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def enqueue_raw(self, item):
        """
        入队到原始消息队列
        
        输入:
            item: 消息字典
        返回:
            str: 消息ID，失败返回None
        """
        try:
            msg_id = self._generate_message_id(item)
            message_data = self._prepare_message_data(item)
            
            self.redis_client.xadd(
                name=self.stream_raw,
                fields=message_data,
                maxlen=self.max_length
            )
            
            logger.debug(f"enqueue_raw: Message {msg_id} enqueued to {self.stream_raw}")
            return msg_id
            
        except Exception as e:
            logger.error(f"enqueue_raw error: {e}")
            return None
    
    def read_raw_for_processing(self, block=True, timeout=None):
        """
        读取原始消息供生产者2处理
        
        输入:
            block: 是否阻塞
            timeout: 超时时间（毫秒）
        返回:
            list: 消息列表 [(message_id, {data}), ...]
        """
        try:
            messages = self.redis_client.xreadgroup(
                groupname=self.consumer_group_raw,
                consumername=self.consumer_name,
                streams={self.stream_raw: '>'},
                count=1,
                block=timeout if block else 0
            )
            
            if messages:
                for stream, msgs in messages:
                    for msg_id, msg_data in msgs:
                        item = {k: json.loads(v) if self._is_json(v) else v 
                                for k, v in msg_data.items()}
                        logger.debug(f"read_raw: Message {msg_id} read from {self.stream_raw}")
                        return [(msg_id, item)]
            
            return []
            
        except Exception as e:
            logger.error(f"read_raw error: {e}")
            return []
    
    def ack_raw(self, message_id):
        """
        确认原始消息处理完成
        
        输入:
            message_id: 消息ID
        """
        try:
            self.redis_client.xack(
                name=self.stream_raw,
                groupname=self.consumer_group_raw,
                id=message_id
            )
            logger.debug(f"ack_raw: Message {message_id} acknowledged")
        except Exception as e:
            logger.error(f"ack_raw error: {e}")
    
    def enqueue_precise(self, item):
        """
        入队到精确消息队列（供外部消费）
        
        输入:
            item: 消息字典
        返回:
            str: 消息ID，失败返回None
        """
        try:
            msg_id = self._generate_message_id(item)
            message_data = self._prepare_message_data(item)
            
            self.redis_client.xadd(
                name=self.stream_precise,
                fields=message_data,
                maxlen=self.max_length
            )
            
            logger.debug(f"enqueue_precise: Message {msg_id} enqueued to {self.stream_precise}")
            return msg_id
            
        except Exception as e:
            logger.error(f"enqueue_precise error: {e}")
            return None
    
    def read_precise_for_streaming(self, count=10):
        """
        读取精确消息用于SSE流式输出
        
        输入:
            count: 读取数量
        返回:
            list: 消息列表
        """
        try:
            messages = self.redis_client.xrange(
                name=self.stream_precise,
                count=count
            )
            
            result = []
            for msg_id, msg_data in messages:
                item = {k: json.loads(v) if self._is_json(v) else v 
                        for k, v in msg_data.items()}
                item['redis_id'] = msg_id
                result.append(item)
            
            logger.debug(f"read_precise: {len(result)} messages read")
            return result
            
        except Exception as e:
            logger.error(f"read_precise error: {e}")
            return []
    
    def _is_json(self, value):
        """
        检查字符串是否为JSON格式
        
        输入:
            value: 字符串值
        返回:
            bool: 是否为JSON
        """
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def get_stream_info(self):
        """
        获取Stream信息
        
        返回:
            dict: Stream状态信息
        """
        try:
            raw_info = self.redis_client.xinfo_stream(self.stream_raw)
            precise_info = self.redis_client.xinfo_stream(self.stream_precise)
            
            return {
                'raw': {
                    'length': raw_info.get('length', 0),
                    'groups': raw_info.get('groups', 0)
                },
                'precise': {
                    'length': precise_info.get('length', 0),
                    'groups': precise_info.get('groups', 0)
                }
            }
        except Exception as e:
            logger.error(f"get_stream_info error: {e}")
            return {'raw': {'length': 0}, 'precise': {'length': 0}}
    
    def close(self):
        """
        关闭Redis连接
        """
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")
