#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AT-SPI消息监听器
通过UI控件树监听微信消息，比纯视觉方案更稳定可靠
"""

import time
import logging
import threading
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ATSPIMessage:
    """AT-SPI检测到的消息"""
    sender: str  # 发送者
    content: str  # 消息内容
    timestamp: str  # 时间戳
    message_type: str  # 消息类型（text/image/video/photo）
    image_path: Optional[str] = None  # 图片路径（普通图片）或缩略图（photo消息）
    high_res_image_path: Optional[str] = None  # 高清图片路径（仅photo消息）
    raw_object: Optional[object] = None  # 原始AT-SPI对象


class ATSPIObserver:
    """
    AT-SPI消息观察者

    功能：
    1. 监听微信窗口的UI控件树变化
    2. 识别新消息并提取内容
    3. 触发回调函数处理消息

    优势：
    - 不依赖视觉定位，界面变化不影响
    - 直接访问UI控件树，获取文本内容更准确
    - 资源占用更少（不需要截图和图像处理）

    兜底策略：
    - 如果AT-SPI失败，自动切换到视觉方案
    """

    def __init__(self, enable_universal_extraction: bool = True, save_dir: str = "/host/data"):
        """
        初始化AT-SPI观察者

        Args:
            enable_universal_extraction: 是否启用通用消息提取（点击所有消息判断类型）
            save_dir: 文件保存目录（挂载到物理机）
        """
        self.registry = None
        self.desktop = None
        self.wechat_window = None
        self.message_list = None
        self.last_message_count = 0
        self.is_running = False
        self.callbacks: List[Callable] = []
        self.enable_universal_extraction = enable_universal_extraction
        self.universal_extractor = None
        self.save_dir = save_dir

        # 延迟初始化通用消息提取器
        if enable_universal_extraction:
            try:
                from core.message.extractor import UniversalMessageExtractor
                self.universal_extractor = UniversalMessageExtractor(save_dir=save_dir)
                logger.info("通用消息提取器已启用")
            except ImportError as e:
                logger.warning(f"无法导入UniversalMessageExtractor: {e}")
                self.enable_universal_extraction = False

    def initialize(self) -> bool:
        """
        初始化AT-SPI连接

        Returns:
            bool: 初始化是否成功
        """
        try:
            import pyatspi

            logger.info("正在初始化AT-SPI连接...")

            # 获取Registry
            self.registry = pyatspi.Registry

            # 获取桌面
            self.desktop = pyatspi.Registry.getDesktop(0)
            logger.info(f"AT-SPI已连接，找到 {self.desktop.childCount} 个应用")

            # 查找微信窗口
            if not self._find_wechat_window():
                logger.warning("未找到微信窗口，请确保微信已启动并设置了QT_ACCESSIBILITY=1")
                return False

            # 查找消息列表控件
            if not self._find_message_list():
                logger.warning("未找到消息列表控件，可能需要调整控件查找逻辑")
                return False

            # 初始化通用消息提取器
            if self.enable_universal_extraction and self.universal_extractor:
                if not self.universal_extractor.initialize():
                    logger.warning("通用消息提取器初始化失败，提取功能将被禁用")
                    self.enable_universal_extraction = False

            logger.info("AT-SPI初始化成功")
            return True

        except ImportError as e:
            logger.error(f"pyatspi库未安装: {e}")
            return False
        except Exception as e:
            logger.error(f"AT-SPI初始化失败: {e}", exc_info=True)
            return False

    def _find_wechat_window(self) -> bool:
        """
        查找微信窗口

        Returns:
            bool: 是否找到微信窗口
        """
        try:
            import pyatspi

            logger.info("正在搜索微信窗口...")

            # 方法1：遍历所有应用
            apps = pyatspi.Registry.getDesktop(0) or pyatspi.Registry.getDesktop()

            # 尝试获取应用列表
            if hasattr(apps, 'childCount') and apps.childCount > 0:
                logger.info(f"AT-SPI找到 {apps.childCount} 个应用")
            else:
                logger.warning("AT-SPI desktop childCount为0或无法获取")
                # 尝试直接枚举所有窗口
                logger.info("尝试直接枚举窗口...")

            # 遍历所有应用
            for i in range(getattr(apps, 'childCount', 0)):
                try:
                    app = apps.getChildAtIndex(i)
                    app_name = app.name or ""

                    logger.debug(f"应用{i}: {app_name}")

                    # 查找微信应用（可能的名字：wechat, WeChat, 微信）
                    if any(name in app_name.lower() for name in ['wechat', '微信']):
                        logger.info(f"找到微信应用: {app_name}")

                        # 获取应用的主窗口（可能是WINDOW或FRAME）
                        for j in range(app.childCount):
                            child = app.getChildAtIndex(j)
                            role = child.getRole()
                            # 微信的窗口可能是ROLE_WINDOW或ROLE_FRAME
                            if role in [pyatspi.ROLE_WINDOW, pyatspi.ROLE_FRAME]:
                                self.wechat_window = child
                                logger.info(f"找到微信窗口: {child.name} (角色: {child.getRoleName()})")
                                return True
                except Exception as e:
                    logger.debug(f"遍历应用{i}时出错: {e}")
                    continue

            logger.warning("未找到微信窗口")
            logger.info("提示：请确保微信已启动并设置了QT_ACCESSIBILITY=1")
            return False

        except Exception as e:
            logger.error(f"查找微信窗口失败: {e}", exc_info=True)
            return False

    def _find_message_list(self) -> bool:
        """
        查找消息列表控件

        Returns:
            bool: 是否找到消息列表控件
        """
        try:
            import pyatspi

            def find_list_recursive(acc, depth: int = 0) -> bool:
                """递归查找消息列表控件"""
                if depth > 20:  # 防止无限递归
                    return False

                try:
                    role = acc.getRole()
                    role_name = acc.getRoleName()
                    name = acc.name or ""

                    # 查找列表/表格/面板等可能包含消息的控件
                    # 微信的消息列表通常是：LIST, TABLE, PANEL, TREE等
                    if role in [
                        pyatspi.ROLE_LIST,
                        pyatspi.ROLE_TABLE,
                        pyatspi.ROLE_TREE,
                        pyatspi.ROLE_PANEL
                    ]:
                        # 检查是否包含多个子项（消息项）
                        child_count = acc.childCount
                        if child_count > 0:
                            logger.info(f"找到可能的消息列表: {name} (角色: {role_name}, 子项数: {child_count})")

                            # 打印前几个子项的信息用于调试
                            for k in range(min(3, child_count)):
                                child = acc.getChildAtIndex(k)
                                logger.debug(f"  子项{k}: {child.name} ({child.getRoleName()})")

                            self.message_list = acc
                            self.last_message_count = child_count
                            return True

                    # 递归搜索子节点
                    for i in range(acc.childCount):
                        if find_list_recursive(acc.getChildAtIndex(i), depth + 1):
                            return True

                except Exception as e:
                    logger.debug(f"遍历控件时出错: {e}")

                return False

            # 从微信窗口开始搜索
            if self.wechat_window:
                return find_list_recursive(self.wechat_window)
            else:
                return False

        except Exception as e:
            logger.error(f"查找消息列表失败: {e}")
            return False

    def _extract_message_from_item(self, item) -> Optional[ATSPIMessage]:
        """
        从消息项中提取消息内容（新逻辑：点击所有消息判断类型）

        Args:
            item: AT-SPI可访问对象（消息项）

        Returns:
            ATSPIMessage: 提取的消息，如果提取失败返回None
        """
        try:
            import pyatspi

            sender = ""
            content = ""
            message_type = "text"
            image_path = None
            high_res_image_path = None

            # 步骤1: 提取发送者和基本文本内容
            def extract_text_recursive(acc, depth: int = 0):
                nonlocal sender, content

                if depth > 15:
                    return

                try:
                    role = acc.getRole()
                    name = acc.name or ""
                    text = ""

                    # 如果是文本控件，获取文本内容
                    if role == pyatspi.ROLE_TEXT:
                        try:
                            text_iface = acc.queryText()
                            if text_iface:
                                text = text_iface.getText(0, text_iface.characterCount)
                        except:
                            text = acc.name or ""

                    elif role == pyatspi.ROLE_LABEL:
                        text = acc.name or ""

                    # 根据角色和内容判断是发送者还是消息内容
                    if text:
                        if len(text) < 20 and '\n' not in text and not sender:
                            sender = text
                        elif len(text) > 0:
                            content = text

                    # 递归处理子节点
                    for i in range(acc.childCount):
                        extract_text_recursive(acc.getChildAtIndex(i), depth + 1)

                except Exception as e:
                    logger.debug(f"提取文本时出错: {e}")

            # 提取基本文本信息
            extract_text_recursive(item)

            # 步骤2: 如果启用了通用提取器，使用新逻辑
            if self.enable_universal_extraction and self.universal_extractor:
                try:
                    # 异步提取（避免阻塞消息流）
                    import threading

                    def extract_async():
                        try:
                            extracted = self.universal_extractor.extract_message(item, sender or "Unknown")
                            if extracted:
                                logger.info(
                                    f"通用提取: type={extracted.msg_type.value}, "
                                    f"window={extracted.window_title}, "
                                    f"path={extracted.high_res_media_path}"
                                )
                                # 可以通过回调或其他方式通知提取完成
                        except Exception as e:
                            logger.error(f"异步提取失败: {e}")

                    # 启动后台线程
                    thread = threading.Thread(target=extract_async, daemon=True)
                    thread.start()

                    # 先返回基本信息，后续可以更新
                    message_type = "text"  # 初始类型，异步提取后会更新
                    if "[Photo]" in content or "[Image]" in content:
                        message_type = "photo"

                except Exception as e:
                    logger.error(f"通用提取失败: {e}")

            # 步骤3: 构造消息对象
            if content:
                message = ATSPIMessage(
                    sender=sender or "Unknown",
                    content=content,
                    timestamp=datetime.now().isoformat(),
                    message_type=message_type,
                    image_path=image_path,
                    high_res_image_path=high_res_image_path,
                    raw_object=item
                )
                return message
            else:
                return None

        except Exception as e:
            logger.error(f"从消息项提取内容失败: {e}")
            return None

    def check_new_messages(self) -> List[ATSPIMessage]:
        """
        检查是否有新消息

        Returns:
            List[ATSPIMessage]: 新消息列表
        """
        new_messages = []

        try:
            if not self.message_list:
                return new_messages

            current_count = self.message_list.childCount

            # 如果消息数量增加了，说明有新消息
            if current_count > self.last_message_count:
                logger.info(f"检测到新消息: {self.last_message_count} -> {current_count}")

                # 提取新增的消息
                for i in range(self.last_message_count, current_count):
                    try:
                        item = self.message_list.getChildAtIndex(i)
                        message = self._extract_message_from_item(item)

                        if message:
                            logger.info(f"提取到消息: 发送者={message.sender}, 内容={message.content[:50]}")
                            new_messages.append(message)
                        else:
                            logger.warning(f"消息项{i}提取失败")

                    except Exception as e:
                        logger.error(f"处理消息项{i}失败: {e}")

                # 更新消息计数
                self.last_message_count = current_count

            return new_messages

        except Exception as e:
            logger.error(f"检查新消息失败: {e}")
            return new_messages

    def add_callback(self, callback: Callable[[ATSPIMessage], None]):
        """
        添加消息回调函数

        Args:
            callback: 回调函数，接收ATSPIMessage参数
        """
        self.callbacks.append(callback)

    def start_monitoring(self, interval: float = 0.5):
        """
        开始监听新消息

        Args:
            interval: 检查间隔（秒）
        """
        self.is_running = True

        def monitoring_loop():
            while self.is_running:
                try:
                    new_messages = self.check_new_messages()

                    # 触发所有回调
                    for message in new_messages:
                        for callback in self.callbacks:
                            try:
                                callback(message)
                            except Exception as e:
                                logger.error(f"回调函数执行失败: {e}")

                except Exception as e:
                    logger.error(f"监听循环出错: {e}")

                time.sleep(interval)

        # 在后台线程中运行监听循环
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info(f"开始监听新消息，检查间隔: {interval}秒")

    def stop_monitoring(self):
        """停止监听"""
        self.is_running = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=2)
        logger.info("已停止监听")

    def get_message_list_snapshot(self) -> List[Dict]:
        """
        获取当前消息列表快照

        Returns:
            List[Dict]: 消息列表
        """
        messages = []

        try:
            if not self.message_list:
                return messages

            for i in range(self.message_list.childCount):
                try:
                    item = self.message_list.getChildAtIndex(i)
                    message = self._extract_message_from_item(item)

                    if message:
                        messages.append({
                            'sender': message.sender,
                            'content': message.content,
                            'timestamp': message.timestamp,
                            'type': message.message_type
                        })

                except Exception as e:
                    logger.debug(f"获取消息{i}失败: {e}")

            return messages

        except Exception as e:
            logger.error(f"获取消息列表快照失败: {e}")
            return messages

    def debug_print_tree(self, acc=None, indent: int = 0, max_depth: int = 10):
        """
        打印UI控件树（用于调试）

        Args:
            acc: 起始节点，默认为微信窗口
            indent: 缩进级别
            max_depth: 最大深度
        """
        try:
            import pyatspi

            if acc is None:
                acc = self.wechat_window

            if acc is None or indent > max_depth:
                return

            try:
                role = acc.getRole()
                role_name = acc.getRoleName()
                name = acc.name or ""
                child_count = acc.childCount

                print(f"{'  ' * indent}[{role_name}] {name} (children: {child_count})")

                # 递归打印子节点
                for i in range(child_count):
                    self.debug_print_tree(acc.getChildAtIndex(i), indent + 1, max_depth)

            except Exception as e:
                logger.debug(f"打印控件树时出错: {e}")

        except Exception as e:
            logger.error(f"调试打印失败: {e}")


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    observer = ATSPIObserver()

    if observer.initialize():
        # 打印UI控件树
        print("\n=== 微信UI控件树 ===")
        observer.debug_print_tree(max_depth=5)

        # 获取当前消息列表
        print("\n=== 当前消息列表 ===")
        messages = observer.get_message_list_snapshot()
        for i, msg in enumerate(messages):
            print(f"{i + 1}. [{msg['sender']}] {msg['content'][:50]}")

        # 添加回调函数
        def on_new_message(message: ATSPIMessage):
            print(f"\n📨 新消息！")
            print(f"   发送者: {message.sender}")
            print(f"   内容: {message.content}")
            print(f"   时间: {message.timestamp}")

        observer.add_callback(on_new_message)

        # 开始监听
        print("\n=== 开始监听新消息 ===")
        observer.start_monitoring(interval=1.0)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止监听")
            observer.stop_monitoring()
    else:
        print("AT-SPI初始化失败，请检查：")
        print("1. 微信是否已启动")
        print("2. 是否设置了QT_ACCESSIBILITY=1")
        print("3. AT-SPI服务是否正常运行")
