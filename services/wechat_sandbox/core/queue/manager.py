"""
双生产者队列管理器（基于Redis）
职责：
1. 使用Redis Stream存储消息队列
2. 提供生产者入队操作
3. 管理消息去重
4. 提供消息锁定机制防止并发重复处理
"""

import json
import hashlib
import time
import redis
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from utils.config import config

class QueueManager:
    """
    基于Redis的双队列管理器
    
    管理两个Redis Stream：
    - stream_raw: 原始消息队列（生产者1 -> 生产者2）
    - stream_precise: 精确消息队列（生产者2 -> 外部消费）
    """
    
    def __init__(self, redis_config=None):
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
        instance_id = getattr(config, 'instance_id', None) if hasattr(config, 'instance_id') else None
        self.consumer_name = f"producer_service_{instance_id if instance_id else 'default'}"
        self.lock_ttl = redis_config.get('lock_ttl', 300)
        self.lock_prefix = redis_config.get('lock_prefix', 'wechat:lock:')
        
        self._init_streams()
        
        logger.info("QueueManager initialized")
    
    def _init_streams(self):
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
        message_data = {}
        for key, value in item.items():
            if key == 'bubble_img' or key == 'media_img':
                value = value.tobytes() if hasattr(value, 'tobytes') else value
            message_data[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        return message_data
    
    def _generate_message_id(self, item):
        content = json.dumps(item, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _acquire_lock(self, message_id):
        lock_key = f"{self.lock_prefix}{message_id}"
        lock_value = f"{self.consumer_name}_{int(time.time() * 1000)}"
        
        try:
            result = self.redis_client.set(
                lock_key,
                lock_value,
                nx=True,
                ex=self.lock_ttl
            )
            
            if result:
                logger.info(f"Acquired lock for message {message_id}")
            else:
                logger.debug(f"Lock already held for message {message_id}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for message {message_id}: {e}")
            return False
    
    def _release_lock(self, message_id):
        lock_key = f"{self.lock_prefix}{message_id}"
        
        try:
            self.redis_client.delete(lock_key)
            logger.debug(f"Released lock for message {message_id}")
        except Exception as e:
            logger.error(f"Failed to release lock for message {message_id}: {e}")
    
    def enqueue_raw(self, item):
        try:
            msg_id = self._generate_message_id(item)
            message_data = self._prepare_message_data(item)
            
            self.redis_client.xadd(
                name=self.stream_raw,
                fields=message_data,
                maxlen=self.max_length
            )
            
            logger.info(f"enqueue_raw: Message {msg_id} enqueued to {self.stream_raw}")
            return msg_id
            
        except Exception as e:
            logger.error(f"enqueue_raw error: {e}")
            return None
    
    def read_raw_for_processing(self, block=True, timeout=None):
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
                        if not self._acquire_lock(msg_id):
                            logger.debug(f"Message {msg_id} already locked, skipping")
                            continue
                        
                        item = {k: json.loads(v) if self._is_json(v) else v 
                                for k, v in msg_data.items()}
                        logger.info(f"read_raw: Message {msg_id} read from {self.stream_raw}")
                        return [(msg_id, item)]
            
            return []
            
        except Exception as e:
            logger.error(f"read_raw error: {e}")
            return []
    
    def ack_raw(self, message_id):
        try:
            self.redis_client.xack(
                self.stream_raw,
                self.consumer_group_raw,
                message_id
            )
            self._release_lock(message_id)
            logger.info(f"ack_raw: Message {message_id} acknowledged and lock released")
            return True
        except Exception as e:
            logger.error(f"ack_raw error: {e}")
            return False
    
    def enqueue_precise(self, item):
        try:
            msg_id = self._generate_message_id(item)
            message_data = self._prepare_message_data(item)
            
            self.redis_client.xadd(
                name=self.stream_precise,
                fields=message_data,
                maxlen=self.max_length
            )
            
            logger.info(f"enqueue_precise: Message {msg_id} enqueued to {self.stream_precise}")
            return msg_id
            
        except Exception as e:
            logger.error(f"enqueue_precise error: {e}")
            return None
    
    def read_precise_for_streaming(self, count=10):
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
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def get_stream_info(self):
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
        try:
            if self.redis_client:
                self.redis_client.close()
                logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {e}")
