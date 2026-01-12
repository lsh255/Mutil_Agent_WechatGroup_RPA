"""
SSE性能测试工具
测试SSE推送的延迟、吞吐量和稳定性

用法:
    python sse_performance_test.py                      # 基础性能测试
    python sse_performance_test.py --duration 60        # 测试60秒
    python sse_performance_test.py --benchmark          # 基准测试模式
"""

import asyncio
import aiohttp
import json
import time
import argparse
from datetime import datetime
from collections import deque
from typing import List
import statistics


class PerformanceTracker:
    """性能跟踪器"""

    def __init__(self):
        self.message_count = 0
        self.latencies: List[float] = []  # 消息延迟（秒）
        self.throughputs: List[float] = []  # 吞吐量（消息/秒）
        self.start_time = None
        self.last_message_time = None
        self.message_intervals: List[float] = []  # 消息间隔（秒）
        self.error_count = 0
        self.reconnect_count = 0

        # 用于计算滑动窗口的吞吐量
        self.message_timestamps = deque(maxlen=100)

    def start(self):
        """开始测试"""
        self.start_time = time.time()

    def record_message(self):
        """记录接收到消息"""
        now = time.time()
        self.message_count += 1

        if self.start_time:
            # 计算总延迟（从测试开始到现在）
            latency = now - self.start_time
            self.latencies.append(latency)

        if self.last_message_time:
            # 计算消息间隔
            interval = now - self.last_message_time
            self.message_intervals.append(interval)

        self.last_message_time = now
        self.message_timestamps.append(now)

        # 计算当前吞吐量（基于最近100条消息）
        if len(self.message_timestamps) >= 2:
            time_span = self.message_timestamps[-1] - self.message_timestamps[0]
            if time_span > 0:
                throughput = (len(self.message_timestamps) - 1) / time_span
                self.throughputs.append(throughput)

    def record_error(self):
        """记录错误"""
        self.error_count += 1

    def record_reconnect(self):
        """记录重连"""
        self.reconnect_count += 1

    def get_duration(self) -> float:
        """获取测试时长"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

    def report(self, detailed: bool = False):
        """生成性能报告"""
        if self.message_count == 0:
            print("\n📊 性能报告")
            print("─" * 60)
            print("❌ 未收到任何消息")
            return

        duration = self.get_duration()

        print(f"\n{'='*60}")
        print(f"{'📊 SSE性能测试报告':^60}")
        print(f"{'='*60}\n")

        # 基本统计
        print("📈 基本统计:")
        print("─" * 60)
        print(f"测试时长:           {duration:.2f} 秒")
        print(f"接收消息数:         {self.message_count} 条")
        print(f"错误次数:           {self.error_count} 次")
        print(f"重连次数:           {self.reconnect_count} 次")

        if duration > 0:
            avg_throughput = self.message_count / duration
            print(f"平均吞吐量:         {avg_throughput:.2f} 条/秒")

        print()

        # 延迟统计
        if self.latencies:
            print("⏱️  消息延迟统计:")
            print("─" * 60)
            print(f"平均延迟:           {statistics.mean(self.latencies)*1000:.2f} ms")
            print(f"最小延迟:           {min(self.latencies)*1000:.2f} ms")
            print(f"最大延迟:           {max(self.latencies)*1000:.2f} ms")
            print(f"中位数延迟:         {statistics.median(self.latencies)*1000:.2f} ms")
            if len(self.latencies) > 1:
                print(f"标准差:             {statistics.stdev(self.latencies)*1000:.2f} ms")
            print()

        # 消息间隔统计
        if self.message_intervals:
            print("📏 消息间隔统计:")
            print("─" * 60)
            print(f"平均间隔:           {statistics.mean(self.message_intervals)*1000:.2f} ms")
            print(f"最小间隔:           {min(self.message_intervals)*1000:.2f} ms")
            print(f"最大间隔:           {max(self.message_intervals)*1000:.2f} ms")
            print(f"中位数间隔:         {statistics.median(self.message_intervals)*1000:.2f} ms")
            print()

        # 吞吐量统计
        if self.throughputs:
            print("🚀 实时吞吐量统计:")
            print("─" * 60)
            print(f"平均吞吐量:         {statistics.mean(self.throughputs):.2f} 条/秒")
            print(f"最小吞吐量:         {min(self.throughputs):.2f} 条/秒")
            print(f"最大吞吐量:         {max(self.throughputs):.2f} 条/秒")
            print(f"中位数吞吐量:       {statistics.median(self.throughputs):.2f} 条/秒")
            print()

        # 延迟分布
        if detailed and self.latencies:
            print("📊 延迟分布:")
            print("─" * 60)

            # 将延迟分组
            bins = [0, 100, 500, 1000, 2000, 5000, float('inf')]
            labels = ['<100ms', '100-500ms', '500ms-1s', '1-2s', '2-5s', '>5s']
            counts = [0] * len(bins)

            for latency in self.latencies:
                latency_ms = latency * 1000
                for i, threshold in enumerate(bins[1:], 1):
                    if latency_ms < threshold:
                        counts[i-1] += 1
                        break

            for label, count in zip(labels, counts):
                percent = (count / len(self.latencies)) * 100
                bar_length = int(percent / 2)
                bar = "█" * bar_length
                print(f"{label:>10}: {bar:<50} {count} ({percent:.1f}%)")

            print()

        # 性能评级
        print("🎯 性能评级:")
        print("─" * 60)

        if self.latencies:
            avg_latency = statistics.mean(self.latencies) * 1000

            if avg_latency < 100:
                grade = "A+ (优秀)"
                color = "🟢"
            elif avg_latency < 500:
                grade = "A (良好)"
                color = "🟢"
            elif avg_latency < 1000:
                grade = "B (一般)"
                color = "🟡"
            elif avg_latency < 2000:
                grade = "C (较慢)"
                color = "🟠"
            else:
                grade = "D (慢)"
                color = "🔴"

            print(f"{color} 平均延迟 {avg_latency:.0f}ms - {grade}")

        if duration > 0:
            throughput = self.message_count / duration
            if throughput > 10:
                grade = "A+ (优秀)"
                color = "🟢"
            elif throughput > 5:
                grade = "A (良好)"
                color = "🟢"
            elif throughput > 1:
                grade = "B (一般)"
                color = "🟡"
            else:
                grade = "C (较低)"
                color = "🟠"

            print(f"{color} 吞吐量 {throughput:.1f} 条/秒 - {grade}")

        if self.error_count == 0 and self.reconnect_count == 0:
            print("🟢 稳定性 - 优秀 (无错误、无重连)")
        elif self.error_count == 0:
            print(f"🟡 稳定性 - 良好 ({self.reconnect_count} 次重连)")
        else:
            print(f"🔴 稳定性 - 需改进 ({self.error_count} 个错误, {self.reconnect_count} 次重连)")

        print(f"\n{'='*60}\n")


class SSEPerformanceTester:
    """SSE性能测试器"""

    def __init__(
        self,
        url: str = "http://localhost:8000/api/stream/messages",
        duration: int = 0,  # 0表示无限时长
        benchmark: bool = False
    ):
        self.url = url
        self.duration = duration
        self.benchmark = benchmark
        self.tracker = PerformanceTracker()

    async def test(self):
        """执行性能测试"""
        print(f"\n{'='*60}")
        print(f"{'🚀 SSE性能测试':^60}")
        print(f"{'='*60}\n")

        print(f"测试URL:        {self.url}")
        if self.duration > 0:
            print(f"测试时长:       {self.duration} 秒")
        else:
            print(f"测试时长:       无限（按Ctrl+C停止）")
        print(f"基准测试模式:    {'是' if self.benchmark else '否'}")
        print(f"\n开始测试...")
        print("─" * 60)

        self.tracker.start()

        # 启动实时显示任务
        display_task = asyncio.create_task(self._display_progress())

        try:
            await self._connect_and_listen()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"\n❌ 测试错误: {e}")
            self.tracker.record_error()
        finally:
            display_task.cancel()
            try:
                await display_task
            except asyncio.CancelledError:
                pass

            # 生成最终报告
            self.tracker.report(detailed=self.benchmark)

    async def _connect_and_listen(self):
        """连接并监听SSE流"""
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                headers = {
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(self.url, headers=headers, timeout=None) as response:
                        if response.status != 200:
                            raise aiohttp.ClientError(f"HTTP {response.status}")

                        print(f"✅ 连接成功\n")

                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()

                            if line_str.startswith('data: '):
                                self.tracker.record_message()

                                # 检查是否达到测试时长
                                if self.duration > 0 and self.tracker.get_duration() >= self.duration:
                                    print(f"\n✅ 达到测试时长 ({self.duration}秒)")
                                    return

                        # 正常结束连接
                        return

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                retry_count += 1
                self.tracker.record_reconnect()
                print(f"⚠️  连接中断 ({retry_count}/{max_retries}): {e}")

                if retry_count < max_retries:
                    await asyncio.sleep(2)  # 等待后重连
                    print("🔄 尝试重连...")
                else:
                    print(f"❌ 达到最大重试次数 ({max_retries})")
                    raise

    async def _display_progress(self):
        """显示实时进度"""
        last_count = 0

        try:
            while True:
                await asyncio.sleep(1)

                current_count = self.tracker.message_count
                duration = self.tracker.get_duration()

                # 计算速率
                if duration > 0:
                    rate = (current_count - last_count) / 1.0  # 最近1秒的速率
                    avg_rate = current_count / duration
                else:
                    rate = 0
                    avg_rate = 0

                # 计算平均延迟
                if self.tracker.latencies:
                    avg_latency = statistics.mean(self.tracker.latencies) * 1000
                else:
                    avg_latency = 0

                # 实时统计
                print(
                    f"\r⏱️  {duration:>6.1f}s | "
                    f"📨 {current_count:>5}条 | "
                    f"📊 {rate:>5.1f}条/s (平均: {avg_rate:>5.1f}条/s) | "
                    f"⚡ {avg_latency:>6.0f}ms",
                    end=""
                )

                last_count = current_count

        except asyncio.CancelledError:
            # 清理显示
            print()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SSE性能测试工具")
    parser.add_argument("--url", default="http://localhost:8000/api/stream/messages", help="SSE服务URL")
    parser.add_argument("--duration", type=int, default=0, help="测试时长（秒），0表示无限")
    parser.add_argument("--benchmark", action="store_true", help="基准测试模式（显示详细报告）")

    args = parser.parse_args()

    tester = SSEPerformanceTester(
        url=args.url,
        duration=args.duration,
        benchmark=args.benchmark
    )

    try:
        await tester.test()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断测试")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  程序已退出")
