"""
SSE 客户端工具

用于监听和调试 SSE 消息流
"""

import requests
import json
import argparse
import sys
import time
from typing import Optional
from datetime import datetime


class SSEClient:
    """
    SSE 客户端类

    用于连接和监听 SSE 消息流
    """

    def __init__(self, url: str, timeout: Optional[int] = None):
        """
        初始化 SSE 客户端

        Args:
            url: SSE 端点 URL
            timeout: 超时时间（秒）
        """
        self.url = url
        self.timeout = timeout
        self.response = None
        self.message_count = 0
        self.messages_by_type = {}

    def connect(self) -> bool:
        """
        建立 SSE 连接

        Returns:
            连接是否成功
        """
        try:
            self.response = requests.get(
                self.url,
                stream=True,
                timeout=self.timeout
            )

            if self.response.status_code == 200:
                print(f"✅ SSE 连接成功: {self.url}")
                print(f"   Content-Type: {self.response.headers.get('Content-Type')}")
                return True
            else:
                print(f"❌ SSE 连接失败: HTTP {self.response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"❌ 连接错误：无法连接到 {self.url}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ 连接超时")
            return False
        except Exception as e:
            print(f"❌ 连接异常: {e}")
            return False

    def listen(self, duration: Optional[int] = None, max_messages: Optional[int] = None):
        """
        监听 SSE 消息

        Args:
            duration: 监听时长（秒），None 表示无限监听
            max_messages: 最大消息数量，None 表示无限制
        """
        if not self.response:
            print("❌ 未建立连接")
            return

        print(f"\n🎧 开始监听...")
        if duration:
            print(f"   时长: {duration} 秒")
        if max_messages:
            print(f"   最大消息数: {max_messages}")
        print()

        start_time = time.time()

        try:
            for line in self.response.iter_lines():
                # 检查时长
                if duration and (time.time() - start_time) > duration:
                    print(f"\n⏱️  监听时长结束")
                    break

                # 检查消息数量
                if max_messages and self.message_count >= max_messages:
                    print(f"\n📊 达到最大消息数: {max_messages}")
                    break

                if line:
                    self._process_line(line)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断")
        except Exception as e:
            print(f"\n\n❌ 监听异常: {e}")
        finally:
            self.close()

    def _process_line(self, line: bytes):
        """
        处理 SSE 行

        Args:
            line: SSE 行数据
        """
        try:
            line_str = line.decode('utf-8')

            # 跳过空行和注释
            if not line_str or line_str.startswith(':'):
                return

            # 解析消息
            if line_str.startswith("data: "):
                json_str = line_str[6:]
                message = json.loads(json_str)

                self.message_count += 1

                # 统计消息类型
                msg_type = message.get("type", "unknown")
                if msg_type not in self.messages_by_type:
                    self.messages_by_type[msg_type] = 0
                self.messages_by_type[msg_type] += 1

                # 显示消息
                self._display_message(message)

        except json.JSONDecodeError:
            print(f"⚠️  JSON 解析失败: {line_str}")
        except Exception as e:
            print(f"⚠️  处理错误: {e}")

    def _display_message(self, message: dict):
        """
        显示消息

        Args:
            message: 消息对象
        """
        msg_type = message.get("type", "unknown")
        sender = message.get("sender", "unknown")
        timestamp = message.get("timestamp", datetime.now().isoformat())

        # 图标
        type_icons = {
            "text": "📝",
            "photo": "📸",
            "video": "🎬",
            "file": "📁",
            "link": "🔗",
            "other": "❓"
        }

        icon = type_icons.get(msg_type, "❓")

        # 基本信息
        print(f"{icon} [#{self.message_count}] {msg_type.upper()} | {sender} | {timestamp}")

        # 内容
        content = message.get("content", {})

        if msg_type == "text":
            text = content.get("text", "")
            print(f"   {text}")

        elif msg_type in ["photo", "video"]:
            path = content.get("high_res_media_path", "")
            print(f"   📁 {path}")

        elif msg_type == "file":
            filename = content.get("filename", "")
            path = content.get("file_path", "")
            print(f"   📄 {filename}")
            print(f"   📁 {path}")

        # 其他字段
        if "window_detected" in message:
            print(f"   🔍 窗口检测: {message['window_detected']}")

        print()

    def close(self):
        """
        关闭连接
        """
        if self.response:
            self.response.close()

        self._print_summary()

    def _print_summary(self):
        """
        打印统计摘要
        """
        print("\n" + "=" * 60)
        print("📊 监听摘要")
        print("=" * 60)
        print(f"总消息数: {self.message_count}")
        print()
        print("按类型统计:")

        for msg_type, count in self.messages_by_type.items():
            percentage = (count / self.message_count * 100) if self.message_count > 0 else 0
            print(f"  {msg_type}: {count} ({percentage:.1f}%)")

        print("=" * 60)


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="SSE 客户端工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监听默认端点（无限时长）
  python sse_client.py

  # 监听指定端点
  python sse_client.py --url http://localhost:8000/api/stream/messages

  # 监听 30 秒
  python sse_client.py --duration 30

  # 监听最多 100 条消息
  python sse_client.py --max-messages 100

  # 监听 60 秒或 50 条消息
  python sse_client.py --duration 60 --max-messages 50
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/stream/messages",
        help="SSE 端点 URL"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="监听时长（秒）"
    )

    parser.add_argument(
        "--max-messages",
        type=int,
        default=None,
        dest="max_messages",
        help="最大消息数量"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="连接超时时间（秒），默认 60"
    )

    args = parser.parse_args()

    # 创建客户端
    client = SSEClient(
        url=args.url,
        timeout=args.timeout
    )

    # 连接
    if not client.connect():
        sys.exit(1)

    # 监听
    client.listen(
        duration=args.duration,
        max_messages=args.max_messages
    )


if __name__ == "__main__":
    main()
