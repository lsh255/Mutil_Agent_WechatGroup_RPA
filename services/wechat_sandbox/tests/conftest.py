"""
测试配置文件 (v2.0)
"""
import pytest
import redis
import time
import os
import sys
import logging
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用标准 logging，避免依赖问题
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def redis_config():
    """
    Redis配置
    """
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0)),
        "stream_raw": "test:messages:raw",
        "stream_precise": "test:messages:precise"
    }


@pytest.fixture(scope="function")
def redis_client(redis_config):
    """
    Redis客户端
    """
    client = redis.Redis(
        host=redis_config["host"],
        port=redis_config["port"],
        db=redis_config["db"],
        decode_responses=True
    )
    
    try:
        client.ping()
        logger.info(f"Redis连接成功: {redis_config['host']}:{redis_config['port']}")
    except redis.ConnectionError as e:
        pytest.skip(f"Redis连接失败: {e}")
    
    yield client
    
    client.close()


@pytest.fixture(scope="function")
def queue_manager(redis_config, redis_client):
    """
    队列管理器（v2.0：模拟接口）
    """
    # v2.0：QueueManager 已被移除，使用简化的队列接口
    class SimpleQueueManager:
        def __init__(self, client, config):
            self.client = client
            self.config = config
            self.stream_raw = config["stream_raw"]
            self.stream_precise = config["stream_precise"]
            self.redis_client = client  # 兼容测试

        def enqueue_raw(self, message):
            """发送原始消息"""
            # 转换值为字符串（Redis要求）
            converted_message = {}
            for key, value in message.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                converted_message[key] = str(value)
            return self.client.xadd(self.stream_raw, converted_message)

        def enqueue_precise(self, message):
            """发送精确消息"""
            # 转换值为字符串（Redis要求）
            converted_message = {}
            for key, value in message.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                converted_message[key] = str(value)
            return self.client.xadd(self.stream_precise, converted_message)

        def read_raw_messages(self, count=10, block=0):
            """读取原始消息"""
            messages = self.client.xread({self.stream_raw: 0}, count=count, block=block)
            return messages

        def read_precise_messages(self, count=10, block=0):
            """读取精确消息"""
            messages = self.client.xread({self.stream_precise: 0}, count=count, block=block)
            return messages

        def read_precise_for_streaming(self, count=1):
            """读取精确消息（流式）"""
            messages = self.client.xread({self.stream_precise: 0}, count=count)
            # 返回格式化结果
            if messages and len(messages) > 0:
                return messages[0][1]  # 返回消息列表
            return []

        def read_raw_for_processing(self):
            """读取原始消息（处理用）"""
            messages = self.client.xread({self.stream_raw: 0}, count=1)
            return messages

        def ack_raw(self, stream_or_id):
            """确认消息（模拟）"""
            # 兼容两种调用方式
            # 1. ack_raw(stream_name) - 只传递流名
            # 2. ack_raw(message_id) - 只传递消息ID
            # 在实际系统中会使用 XACK，这里模拟返回
            return True

        def get_stream_info(self):
            """获取流信息"""
            info = {}
            try:
                raw_info = self.client.xinfo_stream(self.stream_raw)
                precise_info = self.client.xinfo_stream(self.stream_precise)
                # 转换为字典格式
                info['raw'] = {item[0]: item[1] for item in raw_info}
                info['precise'] = {item[0]: item[1] for item in precise_info}
            except Exception as e:
                # 如果流不存在，返回默认信息
                info['raw'] = {'length': 0, 'groups': 0}
                info['precise'] = {'length': 0, 'groups': 0}
            return info

        def close(self):
            """关闭连接"""
            pass

    manager = SimpleQueueManager(redis_client, redis_config)

    yield manager

    manager.close()


@pytest.fixture(scope="function")
def clean_redis(redis_client, redis_config):
    """
    清理Redis测试数据
    """
    yield
    
    try:
        redis_client.delete(redis_config["stream_raw"])
        redis_client.delete(redis_config["stream_precise"])
        logger.info("Redis测试数据已清理")
    except Exception as e:
        logger.warning(f"清理Redis数据失败: {e}")


@pytest.fixture(scope="session")
def api_base_url():
    """
    API基础URL
    """
    host = os.getenv("API_HOST", "localhost")
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"


@pytest.fixture(scope="function")
def wait_for_service():
    """
    等待服务启动
    """
    def _wait(url, timeout=30, interval=1):
        import requests
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(interval)
        return False
    
    return _wait
