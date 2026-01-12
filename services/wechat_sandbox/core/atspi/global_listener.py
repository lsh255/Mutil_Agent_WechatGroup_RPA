#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全聊天监听器 - 监听微信中所有聊天窗口的消息变化
"""

import sys
import time
import logging
from datetime import datetime
from typing import List, Callable, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GlobalChatListener:
    """
    全局聊天监听器

    监听整个微信应用的消息变化，不管哪个聊天窗口
    """

    def __init__(self):
        self.desktop = None
        self.wechat_app = None
        self.message_lists = {}  # 存储所有消息列表及其当前消息数
        self.callbacks: List[Callable] = []

    def initialize(self) -> bool:
        """初始化"""
        try:
            import pyatspi

            logger.info("正在连接AT-SPI...")
            self.desktop = pyatspi.Registry.getDesktop(0)

            logger.info(f"AT-SPI已连接，找到 {self.desktop.childCount} 个应用")

            # 查找微信应用
            for i in range(self.desktop.childCount):
                app = self.desktop.getChildAtIndex(i)
                if "wechat" in app.name.lower():
                    self.wechat_app = app
                    logger.info(f"找到微信应用: {app.name}")
                    break

            if not self.wechat_app:
                logger.error("未找到微信应用")
                return False

            # 扫描所有消息列表
            self._scan_all_message_lists()

            logger.info(f"✓ 初始化成功，找到 {len(self.message_lists)} 个消息列表")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            return False

    def _scan_all_message_lists(self):
        """扫描所有消息列表控件"""
        try:
            import pyatspi

            logger.info("正在扫描所有消息列表控件...")

            def scan_recursive(acc, depth=0):
                if depth > 20:
                    return

                try:
                    role_id = acc.getRole()
                    role_name = acc.getRoleName()
                    child_count = acc.childCount

                    # 查找所有list类型的控件，且子项数大于0
                    if role_id == pyatspi.ROLE_LIST and child_count > 0:
                        # 生成唯一标识
                        list_id = f"{id(acc)}"
                        self.message_lists[list_id] = {
                            'obj': acc,
                            'count': child_count,
                            'role': role_name,
                            'name': acc.name or '',
                            'depth': depth
                        }
                        logger.info(f"  [{len(self.message_lists)}] {role_name}: {acc.name or '(无)'} ({child_count} 项)")

                    for i in range(acc.childCount):
                        scan_recursive(acc.getChildAtIndex(i), depth + 1)

                except Exception as e:
                    pass

            scan_recursive(self.wechat_app)

        except Exception as e:
            logger.error(f"扫描消息列表失败: {e}")

    def check_new_messages(self) -> List[Dict]:
        """检查所有消息列表的新消息"""
        all_new_messages = []

        try:
            import pyatspi

            for list_id, list_info in self.message_lists.items():
                try:
                    acc = list_info['obj']
                    current_count = acc.childCount

                    # 如果有新消息
                    if current_count > list_info['count']:
                        new_count = current_count - list_info['count']
                        logger.info(f"✓ [{list_info['name']}] 检测到 {new_count} 条新消息")

                        # 提取新增的消息
                        for i in range(list_info['count'], current_count):
                            try:
                                msg_item = acc.getChildAtIndex(i)
                                msg_data = self._extract_message_content(msg_item)
                                if msg_data:
                                    msg_data['source'] = list_info['name']
                                    all_new_messages.append(msg_data)
                                    logger.info(f"    [{msg_data['sender']}] {msg_data['content'][:50]}")
                            except Exception as e:
                                logger.error(f"提取消息{i}失败: {e}")

                        # 更新计数
                        list_info['count'] = current_count

                except Exception as e:
                    logger.debug(f"检查列表{list_id}失败: {e}")

            return all_new_messages

        except Exception as e:
            logger.error(f"检查新消息失败: {e}")
            return []

    def _extract_message_content(self, msg_item) -> Dict:
        """提取消息内容"""
        try:
            import pyatspi

            content = ""
            sender = ""

            def extract_text(acc, depth=0):
                nonlocal content, sender

                if depth > 8:
                    return

                try:
                    role = acc.getRole()
                    name = acc.name or ""

                    # 提取文本
                    if role == pyatspi.ROLE_TEXT:
                        try:
                            text_iface = acc.queryText()
                            if text_iface:
                                text = text_iface.getText(0, text_iface.characterCount)
                                if text:
                                    content = text
                        except:
                            content = name

                    elif role == pyatspi.ROLE_LABEL and name and not sender:
                        # 可能是发送者名称
                        if len(name) < 50:  # 发送者名称通常较短
                            sender = name

                    for i in range(acc.childCount):
                        extract_text(acc.getChildAtIndex(i), depth + 1)

                except:
                    pass

            extract_text(msg_item)

            return {
                'sender': sender or 'Unknown',
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"提取消息内容失败: {e}")
            return None

    def add_callback(self, callback: Callable):
        """添加回调函数"""
        self.callbacks.append(callback)

    def start_listening(self, interval: float = 1.0):
        """开始监听"""
        logger.info("="*60)
        logger.info("开始监听所有微信消息")
        logger.info("="*60)
        logger.info(f"检查间隔: {interval}秒")
        logger.info("监听的消息列表数量:", len(self.message_lists))
        logger.info("按Ctrl+C停止\n")

        try:
            while True:
                try:
                    new_messages = self.check_new_messages()

                    for msg in new_messages:
                        for callback in self.callbacks:
                            try:
                                callback(msg)
                            except Exception as e:
                                logger.error(f"回调执行失败: {e}")

                except Exception as e:
                    logger.error(f"监听循环出错: {e}")

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n停止监听")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("全局聊天监听器")
    print("="*60)
    print("监听范围: 所有微信消息")
    print("="*60 + "\n")

    listener = GlobalChatListener()

    if listener.initialize():
        def on_message(msg):
            print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] 新消息")
            print(f"   来源: {msg.get('source', 'Unknown')}")
            print(f"   发送者: {msg['sender']}")
            print(f"   内容: {msg['content']}")
            print()

        listener.add_callback(on_message)
        listener.start_listening(interval=1.0)
    else:
        print("初始化失败")
