"""
Redis队列监控工具 - Python版本
提供更丰富的监控功能和数据分析

用法:
    python queue_monitor.py              # 基础监控
    python queue_monitor.py --analyze    # 分析模式
    python queue_monitor.py --export     # 导出队列数据
"""

import redis
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
import sys


class QueueMonitor:
    """Redis队列监控器"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        raw_stream: str = "wechat:messages:raw",
        precise_stream: str = "wechat:messages:precise",
        lock_prefix: str = "wechat:lock:"
    ):
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
        self.raw_stream = raw_stream
        self.precise_stream = precise_stream
        self.lock_prefix = lock_prefix

        # 测试连接
        try:
            self.redis_client.ping()
            print(f"✅ 已连接到Redis ({host}:{port})")
        except redis.ConnectionError as e:
            print(f"❌ 无法连接到Redis: {e}")
            sys.exit(1)

    def get_queue_lengths(self) -> Tuple[int, int]:
        """获取队列长度"""
        raw_len = self.redis_client.xlen(self.raw_stream)
        precise_len = self.redis_client.xlen(self.precise_stream)
        return raw_len, precise_len

    def get_latest_message(self, stream: str) -> Dict:
        """获取最新消息"""
        messages = self.redis_client.xrevrange(stream, '+', '-', count=1)
        if messages:
            msg_id, fields = messages[0]
            return {"id": msg_id, "data": fields}
        return None

    def get_lock_count(self) -> int:
        """获取当前锁数量"""
        keys = self.redis_client.keys(f"{self.lock_prefix}*")
        return len(keys)

    def get_memory_usage(self) -> Tuple[str, str]:
        """获取Redis内存使用情况"""
        info = self.redis_client.info('memory')
        used = info.get('used_memory_human', 'N/A')
        peak = info.get('used_memory_peak_human', 'N/A')
        return used, peak

    def monitor(self, interval: int = 2):
        """实时监控模式"""
        print(f"\n{'='*70}")
        print(f"{'🔍 微信沙盒队列实时监控':^70}")
        print(f"{'='*70}")
        print(f"刷新间隔: {interval}秒 | 按Ctrl+C退出")
        print(f"{'='*70}\n")

        try:
            while True:
                # 清屏（兼容不同操作系统）
                print("\033[2J\033[H", end="")

                # 标题
                print(f"╔{'═'*68}╗")
                print(f"║{'微信沙盒队列监控 - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^68}║")
                print(f"╚{'═'*68}╝")
                print()

                # 队列长度
                raw_len, precise_len = self.get_queue_lengths()
                print(f"📥 原始队列 (Raw):          {raw_len:>6} 条消息")
                print(f"📤 精确队列 (Precise):      {precise_len:>6} 条消息")

                # 处理进度
                total = raw_len + precise_len
                if total > 0:
                    percent = (precise_len * 100) // total
                    progress_bar = self._make_progress_bar(percent)
                    print(f"📊 处理进度:                {progress_bar} {percent}%")

                print()
                print("─" * 70)

                # 最新原始消息
                latest_raw = self.get_latest_message(self.raw_stream)
                if latest_raw:
                    print("\n📌 最新原始消息:")
                    print("─" * 70)
                    self._display_message(latest_raw['data'], "raw")
                else:
                    print("\n📭 原始队列为空")

                print()
                print("─" * 70)

                # 最新精确消息
                latest_precise = self.get_latest_message(self.precise_stream)
                if latest_precise:
                    print("\n📌 最新精确消息:")
                    print("─" * 70)
                    self._display_message(latest_precise['data'], "precise")
                else:
                    print("\n📭 精确队列为空")

                print()
                print("─" * 70)

                # 锁和内存
                lock_count = self.get_lock_count()
                used, peak = self.get_memory_usage()
                print(f"\n🔒 当前锁定消息:            {lock_count:>6} 条")
                print(f"💾 Redis内存使用:           {used:>6} (峰值: {peak})")

                print()
                print("╚" + "═" * 68 + "╝")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  监控已停止")

    def analyze(self):
        """分析模式 - 深入分析队列数据"""
        print(f"\n{'='*70}")
        print(f"{'📊 队列数据分析':^70}")
        print(f"{'='*70}\n")

        # 分析原始队列
        print("📥 原始队列分析:")
        print("─" * 70)
        self._analyze_stream(self.raw_stream)

        print()

        # 分析精确队列
        print("📤 精确队列分析:")
        print("─" * 70)
        self._analyze_stream(self.precise_stream)

    def export(self, output_file: str = None):
        """导出队列数据到JSON文件"""
        print(f"\n{'='*70}")
        print(f"{'💾 导出队列数据':^70}")
        print(f"{'='*70}\n")

        raw_messages = self._export_stream(self.raw_stream)
        precise_messages = self._export_stream(self.precise_stream)

        data = {
            "export_time": datetime.now().isoformat(),
            "raw_queue": {
                "stream": self.raw_stream,
                "count": len(raw_messages),
                "messages": raw_messages
            },
            "precise_queue": {
                "stream": self.precise_stream,
                "count": len(precise_messages),
                "messages": precise_messages
            }
        }

        if output_file is None:
            output_file = f"queue_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 原始队列: {len(raw_messages)} 条消息")
        print(f"✅ 精确队列: {len(precise_messages)} 条消息")
        print(f"\n💾 数据已导出到: {output_file}")

    def _analyze_stream(self, stream: str):
        """分析单个流"""
        length = self.redis_client.xlen(stream)
        print(f"队列长度: {length} 条消息")

        if length == 0:
            print("队列为空")
            return

        # 获取最近10条消息
        messages = self.redis_client.xrevrange(stream, '+', '-', count=10)

        # 统计消息类型
        type_count = {}
        for msg_id, fields in messages:
            msg_type = fields.get('type', 'unknown')
            type_count[msg_type] = type_count.get(msg_type, 0) + 1

        print(f"\n消息类型分布 (最近10条):")
        for msg_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {msg_type}: {count} 条")

        # 显示第一条消息
        if messages:
            print(f"\n最新消息预览:")
            self._display_message(messages[0][1], stream)

    def _export_stream(self, stream: str) -> List[Dict]:
        """导出流数据"""
        messages = []
        length = self.redis_client.xlen(stream)

        if length == 0:
            return messages

        # 读取所有消息（最多1000条）
        count = min(length, 1000)
        messages_data = self.redis_client.xrevrange(stream, '+', '-', count=count)

        for msg_id, fields in messages_data:
            try:
                # 尝试解析JSON字段
                parsed_fields = {}
                for key, value in fields.items():
                    try:
                        parsed_fields[key] = json.loads(value)
                    except:
                        parsed_fields[key] = value

                messages.append({
                    "id": msg_id,
                    "data": parsed_fields
                })
            except Exception as e:
                print(f"⚠️  跳过消息 {msg_id}: {e}")

        return messages

    def _display_message(self, fields: Dict, stream: str):
        """显示消息内容"""
        timestamp = fields.get('timestamp', 'N/A')
        msg_type = fields.get('type', 'N/A')
        producer = fields.get('metadata', '{}')

        try:
            metadata = json.loads(producer) if isinstance(producer, str) else producer
            producer_name = metadata.get('producer', 'N/A')
        except:
            producer_name = 'N/A'

        print(f"时间:     {timestamp}")
        print(f"类型:     {msg_type}")
        print(f"生产者:   {producer_name}")

        # 根据流类型显示不同内容
        if stream == self.precise_stream:
            precise_content = fields.get('precise_content', '{}')
            try:
                content = json.loads(precise_content) if isinstance(precise_content, str) else precise_content
                if content.get('type') == 'text':
                    text = content.get('text', '')
                    preview = text[:60] + "..." if len(text) > 60 else text
                    print(f"内容:     {preview}")
                elif content.get('type') in ['image', 'video']:
                    print(f"媒体:     {content.get('type')}")
                    print(f"路径:     {content.get('media_path', 'N/A')}")
            except:
                pass

    def _make_progress_bar(self, percent: int, width: int = 30) -> str:
        """制作进度条"""
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Redis队列监控工具")
    parser.add_argument("--host", default="localhost", help="Redis主机")
    parser.add_argument("--port", type=int, default=6379, help="Redis端口")
    parser.add_argument("--interval", type=int, default=2, help="监控刷新间隔（秒）")
    parser.add_argument("--analyze", action="store_true", help="分析模式")
    parser.add_argument("--export", action="store_true", help="导出队列数据")
    parser.add_argument("--output", help="导出文件名")

    args = parser.parse_args()

    monitor = QueueMonitor(
        host=args.host,
        port=args.port
    )

    if args.analyze:
        monitor.analyze()
    elif args.export:
        monitor.export(args.output)
    else:
        monitor.monitor(interval=args.interval)


if __name__ == "__main__":
    main()
