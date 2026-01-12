#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天窗口监听器
能够根据指定的聊天窗口名称查找并持续监听消息
"""

import sys
import time
import logging
from datetime import datetime
from typing import Optional, List, Callable

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatWindowListener:
    """
    聊天窗口监听器

    功能：
    1. 根据聊天窗口名称查找对应的控件
    2. 持续监听该窗口的新消息
    3. 提取消息内容（发送者、文本、时间）
    """

    def __init__(self, chat_name: str):
        """
        初始化监听器

        Args:
            chat_name: 聊天窗口名称（如"File Transfer"）
        """
        self.chat_name = chat_name.lower()
        self.desktop = None
        self.wechat_app = None
        self.chat_window = None
        self.message_list = None
        self.last_message_count = 0
        self.callbacks: List[Callable] = []

    def initialize(self) -> bool:
        """
        初始化AT-SPI连接

        Returns:
            bool: 是否初始化成功
        """
        try:
            import pyatspi

            logger.info("正在连接AT-SPI...")
            self.desktop = pyatspi.Registry.getDesktop(0)

            logger.info(f"AT-SPI已连接，找到 {self.desktop.childCount} 个应用")

            # 查找微信应用
            if not self._find_wechat_app():
                logger.error("未找到微信应用")
                return False

            # 查找聊天窗口
            if not self._find_chat_window():
                logger.warning(f"未找到聊天窗口: {self.chat_name}")
                logger.info("提示：请确保已在微信中打开该聊天窗口")
                return False

            # 查找消息列表
            if not self._find_message_list():
                logger.warning("未找到消息列表")
                return False

            logger.info("✓ 初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            return False

    def _find_wechat_app(self) -> bool:
        """查找微信应用"""
        try:
            import pyatspi

            for i in range(self.desktop.childCount):
                app = self.desktop.getChildAtIndex(i)
                if "wechat" in app.name.lower():
                    self.wechat_app = app
                    logger.info(f"找到微信应用: {app.name}")
                    return True

            return False
        except Exception as e:
            logger.error(f"查找微信应用失败: {e}")
            return False

    def _find_chat_window(self) -> bool:
        """
        查找指定的聊天窗口

        Returns:
            bool: 是否找到
        """
        try:
            logger.info(f"正在查找聊天窗口: {self.chat_name}")

            def search_recursive(acc, depth=0):
                if depth > 20:
                    return None

                try:
                    name = acc.name or ""

                    # 检查是否匹配目标聊天窗口
                    if self.chat_name in name.lower():
                        logger.info(f"✓ 找到聊天窗口: {name}")
                        logger.info(f"  角色: {acc.getRoleName()}")
                        logger.info(f"  层级: {depth}")
                        return acc

                    # 递归搜索
                    for i in range(acc.childCount):
                        result = search_recursive(acc.getChildAtIndex(i), depth + 1)
                        if result:
                            return result

                except Exception as e:
                    pass

                return None

            self.chat_window = search_recursive(self.wechat_app)
            return self.chat_window is not None

        except Exception as e:
            logger.error(f"查找聊天窗口失败: {e}")
            return False

    def _find_message_list(self) -> bool:
        """
        在聊天窗口中查找消息列表控件

        Returns:
            bool: 是否找到
        """
        try:
            import pyatspi

            logger.info("正在查找消息列表控件...")

            def find_list_recursive(acc, depth=0):
                if depth > 25:  # 增加搜索深度
                    return None

                try:
                    role_id = acc.getRole()
                    role_name = acc.getRoleName()
                    child_count = acc.childCount

                    # 扩展查找范围：包括更多可能的控件类型
                    # 只要子项数大于某个阈值，就认为是可能的容器
                    if child_count > 3:
                        parent_name = ""
                        try:
                            if hasattr(acc, 'parent'):
                                parent_name = acc.parent.name or ""
                        except:
                            pass

                        # 记录所有可能的消息容器
                        logger.debug(f"[depth {depth}] {role_name}: {acc.name or ''} ({child_count} children)")

                        # 优先级判断
                        priority = 0
                        if role_id in [pyatspi.ROLE_LIST, pyatspi.ROLE_PANEL, pyatspi.ROLE_PAGE_TAB_LIST]:
                            priority += 2
                        if "panel" in role_name.lower() or "list" in role_name.lower():
                            priority += 1

                        # 如果优先级足够高，就选择这个
                        if priority >= 1:
                            logger.info(f"✓ 找到消息容器: {role_name}")
                            logger.info(f"  名称: {acc.name or '(无)'}")
                            logger.info(f"  子项数: {child_count}")
                            logger.info(f"  层级: {depth}")
                            self.last_message_count = child_count
                            return acc

                    for i in range(acc.childCount):
                        result = find_list_recursive(acc.getChildAtIndex(i), depth + 1)
                        if result:
                            return result

                except Exception as e:
                    logger.debug(f"搜索层级 {depth} 失败: {e}")

                return None

            self.message_list = find_list_recursive(self.chat_window)

            if self.message_list:
                logger.info(f"✓ 消息列表已找到，当前消息数: {self.last_message_count}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"查找消息列表失败: {e}")
            return False

    def extract_message(self, message_item):
        """
        从消息项中提取消息内容

        Args:
            message_item: AT-SPI消息项对象

        Returns:
            dict: 消息内容（sender, content, timestamp）
        """
        try:
            import pyatspi

            sender = ""
            content = ""

            def extract_text_recursive(acc, depth=0):
                nonlocal sender, content

                if depth > 10:
                    return

                try:
                    role = acc.getRole()
                    name = acc.name or ""

                    # 提取文本内容
                    if role == pyatspi.ROLE_TEXT:
                        try:
                            text_iface = acc.queryText()
                            if text_iface:
                                text = text_iface.getText(0, text_iface.characterCount)
                                if text:
                                    content = text
                        except:
                            content = name

                    elif role == pyatspi.ROLE_LABEL:
                        if name and not sender:
                            sender = name

                    # 递归处理子节点
                    for i in range(acc.childCount):
                        extract_text_recursive(acc.getChildAtIndex(i), depth + 1)

                except Exception as e:
                    pass

            extract_text_recursive(message_item)

            return {
                'sender': sender or 'Unknown',
                'content': content,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"提取消息失败: {e}")
            return None

    def check_new_messages(self) -> List[dict]:
        """
        检查是否有新消息

        Returns:
            List[dict]: 新消息列表
        """
        new_messages = []

        try:
            if not self.message_list:
                return new_messages

            current_count = self.message_list.childCount

            # 如果有新消息
            if current_count > self.last_message_count:
                logger.info(f"✓ 检测到新消息: {self.last_message_count} -> {current_count}")

                # 提取新增的消息
                for i in range(self.last_message_count, current_count):
                    try:
                        msg_item = self.message_list.getChildAtIndex(i)
                        msg_data = self.extract_message(msg_item)

                        if msg_data and msg_data.get('content'):
                            new_messages.append(msg_data)
                            logger.info(f"  新消息: [{msg_data['sender']}] {msg_data['content'][:50]}")

                    except Exception as e:
                        logger.error(f"处理消息项{i}失败: {e}")

                self.last_message_count = current_count

            return new_messages

        except Exception as e:
            logger.error(f"检查新消息失败: {e}")
            return new_messages

    def add_callback(self, callback: Callable):
        """
        添加消息回调函数

        Args:
            callback: 回调函数，接收消息字典
        """
        self.callbacks.append(callback)

    def start_listening(self, interval: float = 1.0):
        """
        开始持续监听新消息

        Args:
            interval: 检查间隔（秒）
        """
        logger.info(f"开始监听聊天窗口: {self.chat_name}")
        logger.info(f"检查间隔: {interval}秒")
        logger.info("按Ctrl+C停止监听\n")

        try:
            while True:
                try:
                    new_messages = self.check_new_messages()

                    # 触发所有回调
                    for msg in new_messages:
                        for callback in self.callbacks:
                            try:
                                callback(msg)
                            except Exception as e:
                                logger.error(f"回调函数执行失败: {e}")

                except Exception as e:
                    logger.error(f"监听循环出错: {e}")

                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n停止监听")


# 测试代码
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 chat_window_listener.py <聊天窗口名称>")
        print("示例: python3 chat_window_listener.py 'File Transfer'")
        sys.exit(1)

    chat_name = sys.argv[1]

    print(f"\n{'='*60}")
    print(f"聊天窗口监听器")
    print(f"{'='*60}")
    print(f"目标聊天: {chat_name}")
    print(f"{'='*60}\n")

    listener = ChatWindowListener(chat_name)

    if listener.initialize():
        # 添加回调函数
        def on_new_message(msg):
            print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] 收到新消息!")
            print(f"   发送者: {msg['sender']}")
            print(f"   内容: {msg['content']}")
            print()

        listener.add_callback(on_new_message)

        # 开始监听
        listener.start_listening(interval=1.0)
    else:
        print("初始化失败")
        print("\n提示：")
        print("1. 确保微信已启动")
        print("2. 确保已打开目标聊天窗口")
        print("3. 聊天窗口名称要正确（注意大小写和空格）")
