"""
Redis 监控工具

用于监控 Redis Stream 和队列状态
"""

import redis
import json
import argparse
import sys
from typing import Optional, List
from datetime import datetime


class RedisMonitor:
    """
    Redis 监控类

    用于监控 Redis Stream 和队列
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        初始化 Redis 监控器

        Args:
            host: Redis 主机
            port: Redis 端口
            db: 数据库编号
            password: 密码
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )

            # 测试连接
            self.client.ping()

            print(f"✅ Redis 连接成功: {host}:{port}")

        except redis.ConnectionError:
            print(f"❌ Redis 连接失败: {host}:{port}")
            sys.exit(1)
        except redis.AuthenticationError:
            print(f"❌ Redis 认证失败")
            sys.exit(1)

    def get_stream_length(self, stream_name: str) -> int:
        """
        获取 Stream 长度

        Args:
            stream_name: Stream 名称

        Returns:
            Stream 长度
        """
        try:
            return self.client.xlen(stream_name)
        except redis.ResponseError:
            return 0

    def get_stream_info(self, stream_name: str) -> dict:
        """
        获取 Stream 详细信息

        Args:
            stream_name: Stream 名称

        Returns:
            Stream 信息
        """
        try:
            info = self.client.xinfo_stream(stream_name)

            return {
                "length": info.get("length", 0),
                "groups": info.get("groups", 0),
                "first-entry": info.get("first-entry"),
                "last-entry": info.get("last-entry")
            }

        except redis.ResponseError as e:
            return {"error": str(e)}

    def read_stream(
        self,
        stream_name: str,
        count: int = 10,
        from_end: bool = True
    ) -> List[tuple]:
        """
        读取 Stream 消息

        Args:
            stream_name: Stream 名称
            count: 消息数量
            from_end: 是否从最新消息开始

        Returns:
            消息列表 [(id, fields), ...]
        """
        try:
            if from_end:
                messages = self.client.xrevrange(stream_name, count=count)
            else:
                messages = self.client.xrange(stream_name, count=count)

            return messages

        except redis.ResponseError:
            return []

    def monitor_stream(
        self,
        stream_name: str,
        duration: Optional[int] = None,
        interval: int = 1
    ):
        """
        监控 Stream 实时变化

        Args:
            stream_name: Stream 名称
            duration: 监控时长（秒），None 表示无限监控
            interval: 检查间隔（秒）
        """
        import time

        print(f"\n🎧 开始监控 Stream: {stream_name}")
        if duration:
            print(f"   时长: {duration} 秒")
        print(f"   间隔: {interval} 秒")
        print()

        last_length = 0
        start_time = time.time()

        try:
            while True:
                # 检查时长
                if duration and (time.time() - start_time) > duration:
                    print(f"\n⏱️  监控时长结束")
                    break

                # 获取当前长度
                current_length = self.get_stream_length(stream_name)

                # 显示变化
                if current_length != last_length:
                    now = datetime.now().strftime("%H:%M:%S")
                    diff = current_length - last_length

                    if diff > 0:
                        print(f"[{now}] ✅ 新增 {diff} 条消息 (总数: {current_length})")

                        # 读取最新消息
                        messages = self.read_stream(stream_name, count=diff, from_end=True)

                        for msg_id, fields in reversed(messages):
                            print(f"   📨 {msg_id}: {fields.get('type', 'unknown')} - {fields.get('sender', 'unknown')}")
                    else:
                        print(f"[{now}] ⚠️  消息减少 {diff} (总数: {current_length})")

                    last_length = current_length

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断")

    def display_stream_info(self, stream_name: str):
        """
        显示 Stream 详细信息

        Args:
            stream_name: Stream 名称
        """
        print(f"\n📊 Stream 信息: {stream_name}")
        print("=" * 60)

        info = self.get_stream_info(stream_name)

        if "error" in info:
            print(f"❌ 错误: {info['error']}")
            return

        print(f"长度: {info['length']}")
        print(f"消费组数: {info['groups']}")

        if info.get("first-entry"):
            first_id = info["first-entry"][0]
            print(f"第一条消息: {first_id}")

        if info.get("last-entry"):
            last_id = info["last-entry"][0]
            print(f"最后一条消息: {last_id}")

        print("=" * 60)

    def display_stream_messages(
        self,
        stream_name: str,
        count: int = 10,
        from_end: bool = True
    ):
        """
        显示 Stream 消息

        Args:
            stream_name: Stream 名称
            count: 消息数量
            from_end: 是否从最新消息开始
        """
        messages = self.read_stream(stream_name, count=count, from_end=from_end)

        if not messages:
            print(f"\n⚠️  Stream 为空或不存在: {stream_name}")
            return

        print(f"\n📨 Stream 消息: {stream_name}")
        print("=" * 60)
        print(f"显示 {len(messages)} 条消息\n")

        for msg_id, fields in messages:
            print(f"📬 ID: {msg_id}")

            for key, value in fields.items():
                print(f"   {key}: {value}")

            print()

        print("=" * 60)

    def clear_stream(self, stream_name: str) -> bool:
        """
        清空 Stream

        Args:
            stream_name: Stream 名称

        Returns:
            是否成功
        """
        try:
            self.client.delete(stream_name)
            print(f"✅ Stream 已清空: {stream_name}")
            return True

        except redis.ResponseError as e:
            print(f"❌ 清空失败: {e}")
            return False

    def close(self):
        """
        关闭连接
        """
        self.client.close()


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="Redis 监控工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看队列长度
  python redis_monitor.py --stream wechat:messages:precise --length

  # 显示队列信息
  python redis_monitor.py --stream wechat:messages:precise --info

  # 显示最近 10 条消息
  python redis_monitor.py --stream wechat:messages:precise --show

  # 显示最近 20 条消息
  python redis_monitor.py --stream wechat:messages:precise --show --count 20

  # 实时监控队列（无限时长）
  python redis_monitor.py --stream wechat:messages:precise --monitor

  # 实时监控队列（60 秒）
  python redis_monitor.py --stream wechat:messages:precise --monitor --duration 60

  # 清空队列
  python redis_monitor.py --stream wechat:messages:precise --clear
        """
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Redis 主机"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="Redis 端口"
    )

    parser.add_argument(
        "--db",
        type=int,
        default=0,
        help="数据库编号"
    )

    parser.add_argument(
        "--password",
        default=None,
        help="密码"
    )

    parser.add_argument(
        "--stream",
        required=True,
        help="Stream 名称"
    )

    # 操作模式（互斥）
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--length",
        action="store_true",
        help="显示队列长度"
    )

    mode_group.add_argument(
        "--info",
        action="store_true",
        help="显示队列详细信息"
    )

    mode_group.add_argument(
        "--show",
        action="store_true",
        help="显示队列消息"
    )

    mode_group.add_argument(
        "--monitor",
        action="store_true",
        help="实时监控队列"
    )

    mode_group.add_argument(
        "--clear",
        action="store_true",
        help="清空队列"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="消息数量（用于 --show）"
    )

    parser.add_argument(
        "--from-start",
        action="store_true",
        help="从最早消息开始（用于 --show）"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="监控时长（秒，用于 --monitor）"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="检查间隔（秒，用于 --monitor）"
    )

    args = parser.parse_args()

    # 创建监控器
    monitor = RedisMonitor(
        host=args.host,
        port=args.port,
        db=args.db,
        password=args.password
    )

    # 执行操作
    try:
        if args.length:
            length = monitor.get_stream_length(args.stream)
            print(f"队列长度: {length}")

        elif args.info:
            monitor.display_stream_info(args.stream)

        elif args.show:
            monitor.display_stream_messages(
                args.stream,
                count=args.count,
                from_end=not args.from_start
            )

        elif args.monitor:
            monitor.monitor_stream(
                args.stream,
                duration=args.duration,
                interval=args.interval
            )

        elif args.clear:
            monitor.clear_stream(args.stream)

        else:
            # 默认显示信息
            monitor.display_stream_info(args.stream)
            monitor.display_stream_messages(args.stream)

    finally:
        monitor.close()


if __name__ == "__main__":
    main()
