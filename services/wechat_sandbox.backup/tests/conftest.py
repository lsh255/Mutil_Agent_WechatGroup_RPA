"""
测试配置文件
"""
import pytest
import redis
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import logger
from producer_service.queue_manager import RedisQueueManager as QueueManager


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
    队列管理器
    """
    manager = QueueManager(redis_config)
    
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
