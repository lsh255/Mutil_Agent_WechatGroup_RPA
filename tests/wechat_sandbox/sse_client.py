"""
微信沙盒SSE客户端 - 用于测试SSE实时推送功能

用法:
    python sse_client.py                    # 基础监听
    python sse_client.py --verbose          # 详细输出
    python sse_client.py --save-json        # 保存消息到JSON文件
    python sse_client.py --client-id test1  # 指定客户端ID
"""

import asyncio
import aiohttp
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional


class SSEClient:
    """SSE客户端类"""

    def __init__(
        self,
        url: str = "http://localhost:8000/api/stream/messages",
        client_id: str = "default",
        verbose: bool = False,
        save_json: bool = False,
        save_dir: str = "./test_results"
    ):
        self.url = url
        self.client_id = client_id
        self.verbose = verbose
        self.save_json = save_json
        self.save_dir = Path(save_dir)
        self.message_count = 0
        self.messages = []
        self.start_time = None

        # 创建保存目录
        if self.save_json:
            self.save_dir.mkdir(parents=True, exist_ok=True)

    async def listen(self):
        """监听SSE流"""
        print(f"\n{'='*60}")
        print(f"客户端ID: {self.client_id}")
        print(f"连接URL: {self.url}")
        print(f"{'='*60}\n")
        print("开始监听SSE流...")
        print("按 Ctrl+C 停止监听\n")

        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers) as response:
                    if response.status != 200:
                        print(f"❌ 连接失败: HTTP {response.status}")
                        return

                    print(f"✅ 连接成功 (Status: {response.status})")
                    print("-" * 60)

                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()

                        # 跳过空行和注释
                        if not line_str or line_str.startswith(':'):
                            continue

                        # 解析SSE数据
                        if line_str.startswith('data: '):
                            await self._process_message(line_str[6:])

        except aiohttp.ClientError as e:
            print(f"\n❌ 连接错误: {e}")
        except KeyboardInterrupt:
            print("\n\n⏹️  用户中断监听")
        finally:
            await self._cleanup()

    async def _process_message(self, data: str):
        """处理接收到的消息"""
        try:
            message = json.loads(data)
            self.message_count += 1

            if self.start_time is None:
                self.start_time = datetime.now()

            # 保存消息
            if self.save_json:
                self.messages.append(message)

            # 显示消息
            self._display_message(message)

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析错误: {e}")
            print(f"   原始数据: {data}")

    def _display_message(self, message: dict):
        """显示消息内容"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\n📨 [消息 #{self.message_count}] {timestamp}")
        print("-" * 60)

        # 基本信息
        print(f"ID:         {message.get('id', 'N/A')}")
        print(f"类型:       {message.get('type', 'N/A')}")
        print(f"时间戳:     {message.get('timestamp', 'N/A')}")

        # 位置信息
        position = message.get('position', {})
        if position and self.verbose:
            print(f"位置:       X={position.get('screen_x')}, Y={position.get('screen_y')}")

        # 精确内容
        precise_content = message.get('precise_content', {})
        if precise_content:
            content_type = precise_content.get('type', 'N/A')

            if content_type == 'text':
                text = precise_content.get('text', '')
                # 截断长文本
                display_text = text if len(text) <= 100 else text[:97] + "..."
                print(f"文本内容:   {display_text}")

            elif content_type in ['image', 'video']:
                print(f"媒体类型:   {content_type}")
                print(f"媒体路径:   {precise_content.get('media_path', 'N/A')}")
                if self.verbose:
                    print(f"Base64长度: {len(precise_content.get('media_image_base64', ''))}")

            elif content_type == 'mixed':
                print(f"混合内容:")
                if precise_content.get('text'):
                    print(f"  - 文本: {precise_content.get('text')[:50]}...")
                if precise_content.get('media_path'):
                    print(f"  - 媒体: {precise_content.get('media_path')}")

        # 元数据
        metadata = message.get('metadata', {})
        if self.verbose and metadata:
            print(f"生产者:     {metadata.get('producer', 'N/A')}")

        print("-" * 60)

    async def _cleanup(self):
        """清理和保存结果"""
        print(f"\n\n{'='*60}")
        print(f"监听结束")
        print(f"{'='*60}")
        print(f"总消息数:   {self.message_count}")

        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if duration > 0:
                rate = self.message_count / duration
                print(f"监听时长:   {duration:.2f} 秒")
                print(f"消息速率:   {rate:.2f} 条/秒")

        # 保存消息到JSON
        if self.save_json and self.messages:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.save_dir / f"messages_{self.client_id}_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)

            print(f"\n💾 消息已保存到: {filename}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="微信沙盒SSE客户端")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/stream/messages",
        help="SSE服务URL"
    )
    parser.add_argument(
        "--client-id",
        default="default",
        help="客户端ID（用于标识不同的客户端实例）"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出（位置信息、元数据等）"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="保存接收到的消息到JSON文件"
    )
    parser.add_argument(
        "--save-dir",
        default="./test_results",
        help="保存JSON文件的目录（默认: ./test_results）"
    )

    args = parser.parse_args()

    client = SSEClient(
        url=args.url,
        client_id=args.client_id,
        verbose=args.verbose,
        save_json=args.save_json,
        save_dir=args.save_dir
    )

    await client.listen()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  程序已退出")
