"""
测试辅助函数

提供测试中常用的辅助函数和工具
"""

import time
import requests
import redis
import json
from typing import Optional, Callable, Any, Dict, List
from functools import wraps
from datetime import datetime


def wait_for_service(
    url: str,
    timeout: int = 30,
    check_interval: int = 1
) -> bool:
    """
    等待服务启动

    Args:
        url: 服务 URL
        timeout: 超时时间（秒）
        check_interval: 检查间隔（秒）

    Returns:
        服务是否在超时前启动

    Examples:
        >>> if wait_for_service("http://localhost:8000/health"):
        ...     print("服务已启动")
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass

        time.sleep(check_interval)

    return False


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: int = 30,
    check_interval: int = 1,
    error_message: str = "条件超时"
) -> bool:
    """
    等待条件满足

    Args:
        condition: 条件函数
        timeout: 超时时间（秒）
        check_interval: 检查间隔（秒）
        error_message: 超时错误消息

    Returns:
        条件是否在超时前满足

    Examples:
        >>> wait_for_condition(
        ...     lambda: redis_client.xlen("stream") > 0,
        ...     timeout=10
        ... )
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return True

        time.sleep(check_interval)

    raise TimeoutError(error_message)


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    失败重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
        exceptions: 需要重试的异常类型

    Examples:
        >>> @retry_on_failure(max_attempts=3, delay=0.5)
        ... def unstable_function():
        ...     # 可能失败的函数
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


def measure_time(func: Callable) -> Callable:
    """
    测量函数执行时间的装饰器

    Examples:
        >>> @measure_time
        ... def slow_function():
        ...     time.sleep(1)
        ...     return "done"
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time

        print(f"⏱️  {func.__name__} 耗时: {elapsed_time:.3f}秒")

        return result

    return wrapper


def create_test_message(
    msg_type: str = "text",
    sender: str = "test_user",
    content: Optional[Dict] = None
) -> Dict:
    """
    创建测试消息

    Args:
        msg_type: 消息类型
        sender: 发送者
        content: 消息内容

    Returns:
        测试消息字典

    Examples:
        >>> msg = create_test_message("text", "Alice", {"text": "Hello"})
        >>> msg = create_test_message("photo", "Bob", {"high_res_media_path": "/data/photo.png"})
    """
    if content is None:
        content = {}

    if msg_type == "text" and "text" not in content:
        content["text"] = "Test message"

    return {
        "id": f"test_{int(time.time() * 1000)}",
        "type": msg_type,
        "sender": sender,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "window_detected": False
    }


def validate_message_format(message: Dict) -> bool:
    """
    验证消息格式

    Args:
        message: 消息字典

    Returns:
        格式是否正确

    Examples:
        >>> is_valid = validate_message_format(test_message)
    """
    required_fields = ["id", "type", "sender", "content", "timestamp"]

    for field in required_fields:
        if field not in message:
            return False

    # 验证消息类型
    valid_types = {"text", "photo", "video", "file", "link", "other"}
    if message["type"] not in valid_types:
        return False

    # 验证内容字段
    content = message["content"]
    if not isinstance(content, dict):
        return False

    return True


def create_redis_client(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
) -> Optional[redis.Redis]:
    """
    创建 Redis 客户端

    Args:
        host: 主机
        port: 端口
        db: 数据库编号
        password: 密码

    Returns:
        Redis 客户端，连接失败返回 None

    Examples:
        >>> client = create_redis_client()
        >>> if client:
        ...     client.ping()
    """
    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )

        # 测试连接
        client.ping()

        return client

    except:
        return None


def clear_redis_stream(
    client: redis.Redis,
    stream_name: str
) -> bool:
    """
    清空 Redis Stream

    Args:
        client: Redis 客户端
        stream_name: Stream 名称

    Returns:
        是否成功

    Examples:
        >>> clear_redis_stream(client, "wechat:messages:precise")
    """
    try:
        client.delete(stream_name)
        return True
    except:
        return False


def get_stream_length(
    client: redis.Redis,
    stream_name: str
) -> int:
    """
    获取 Stream 长度

    Args:
        client: Redis 客户端
        stream_name: Stream 名称

    Returns:
        Stream 长度

    Examples:
        >>> length = get_stream_length(client, "wechat:messages:precise")
    """
    try:
        return client.xlen(stream_name)
    except:
        return 0


def read_recent_messages(
    client: redis.Redis,
    stream_name: str,
    count: int = 10
) -> List[tuple]:
    """
    读取最近的 Stream 消息

    Args:
        client: Redis 客户端
        stream_name: Stream 名称
        count: 消息数量

    Returns:
        消息列表 [(id, fields), ...]

    Examples:
        >>> messages = read_recent_messages(client, "wechat:messages:precise", 10)
    """
    try:
        return client.xrevrange(stream_name, count=count)
    except:
        return []


def send_test_message_to_api(
    api_url: str,
    message: Dict
) -> bool:
    """
    发送测试消息到 API

    Args:
        api_url: API URL
        message: 消息字典

    Returns:
        是否成功

    Examples:
        >>> msg = create_test_message()
        >>> send_test_message_to_api("http://localhost:8000/api/test", msg)
    """
    try:
        response = requests.post(api_url, json=message, timeout=10)
        return response.status_code == 200
    except:
        return False


class MessageCollector:
    """
    消息收集器

    用于从 SSE 流收集消息
    """

    def __init__(self, max_messages: int = 100):
        """
        初始化收集器

        Args:
            max_messages: 最大收集数量
        """
        self.messages: List[Dict] = []
        self.max_messages = max_messages

    def collect(self, duration: int = 10, url: str = "http://localhost:8000/api/stream/messages"):
        """
        收集消息

        Args:
            duration: 收集时长（秒）
            url: SSE URL

        Returns:
            收集到的消息列表

        Examples:
        >>> collector = MessageCollector()
        >>> messages = collector.collect(duration=5)
        >>> print(f"收集到 {len(messages)} 条消息")
        """
        try:
            response = requests.get(url, stream=True, timeout=duration + 10)

            start_time = time.time()

            for line in response.iter_lines():
                if time.time() - start_time > duration:
                    break

                if len(self.messages) >= self.max_messages:
                    break

                if line:
                    line_str = line.decode('utf-8')

                    if line_str.startswith("data: "):
                        json_str = line_str[6:]
                        message = json.loads(json_str)
                        self.messages.append(message)

            response.close()

        except Exception as e:
            print(f"⚠️  收集失败: {e}")

        return self.messages

    def get_messages_by_type(self, msg_type: str) -> List[Dict]:
        """
        按类型获取消息

        Args:
            msg_type: 消息类型

        Returns:
            该类型的消息列表

        Examples:
        >>> text_messages = collector.get_messages_by_type("text")
        """
        return [msg for msg in self.messages if msg.get("type") == msg_type]

    def count_by_type(self) -> Dict[str, int]:
        """
        按类型统计消息

        Returns:
            类型统计字典

        Examples:
        >>> stats = collector.count_by_type()
        >>> print(stats)  # {"text": 10, "photo": 5, ...}
        """
        stats = {}

        for msg in self.messages:
            msg_type = msg.get("type", "unknown")
            stats[msg_type] = stats.get(msg_type, 0) + 1

        return stats


class PerformanceMonitor:
    """
    性能监控器

    用于监控资源使用情况
    """

    def __init__(self):
        """初始化监控器"""
        try:
            import psutil
            self.psutil = psutil
            self.process = psutil.Process()
            self.available = True
        except ImportError:
            self.available = False

    def get_memory_mb(self) -> Optional[float]:
        """
        获取内存占用（MB）

        Returns:
            内存占用，不可用时返回 None

        Examples:
        >>> monitor = PerformanceMonitor()
        >>> memory = monitor.get_memory_mb()
        >>> print(f"内存: {memory:.2f}MB")
        """
        if not self.available:
            return None

        return self.process.memory_info().rss / 1024 / 1024

    def get_cpu_percent(self) -> Optional[float]:
        """
        获取 CPU 占用率

        Returns:
            CPU 占用率，不可用时返回 None

        Examples:
        >>> monitor = PerformanceMonitor()
        >>> cpu = monitor.get_cpu_percent()
        >>> print(f"CPU: {cpu:.2f}%")
        """
        if not self.available:
            return None

        return self.process.cpu_percent()

    def get_num_threads(self) -> Optional[int]:
        """
        获取线程数

        Returns:
            线程数，不可用时返回 None

        Examples:
        >>> monitor = PerformanceMonitor()
        >>> threads = monitor.get_num_threads()
        >>> print(f"线程数: {threads}")
        """
        if not self.available:
            return None

        return self.process.num_threads()


# 便捷导出
__all__ = [
    "wait_for_service",
    "wait_for_condition",
    "retry_on_failure",
    "measure_time",
    "create_test_message",
    "validate_message_format",
    "create_redis_client",
    "clear_redis_stream",
    "get_stream_length",
    "read_recent_messages",
    "send_test_message_to_api",
    "MessageCollector",
    "PerformanceMonitor"
]
