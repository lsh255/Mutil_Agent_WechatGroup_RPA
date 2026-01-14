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
                from core.extractor import UniversalMessageExtractor
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
        从消息项中提取消息内容（仅处理3种类型：文本、图片、视频）

        工作原理：
        - 监听UI控件树，从控件属性中判断消息类型
        - 文本：ROLE_TEXT/ROLE_LABEL控件
        - 图片：ROLE_IMAGE/ROLE_ICON控件，或有图片路径属性
        - 视频：有视频时长、缩略图等属性
        - 其他类型（文件、链接、表情包等）：直接保存到物理机，不推送SSE

        Args:
            item: AT-SPI可访问对象（消息项）

        Returns:
            ATSPIMessage: 提取的消息（仅text/photo/video），如果类型不支持返回None
        """
        try:
            import pyatspi

            sender = ""
            content = ""
            message_type = "text"
            image_path = None
            high_res_image_path = None

            # 用于标记是否需要保存其他类型到物理机
            other_type_data = None

            # 步骤1: 提取消息的所有信息
            def extract_content_recursive(acc, depth: int = 0):
                nonlocal sender, content, message_type, image_path, high_res_image_path, other_type_data

                if depth > 15:
                    return

                try:
                    role = acc.getRole()
                    role_name = acc.getRoleName()
                    name = acc.name or ""

                    # 获取控件属性
                    attributes = {}
                    try:
                        attrs = acc.getAttributes()
                        if attrs:
                            for attr in attrs:
                                if '=' in attr:
                                    key, value = attr.split('=', 1)
                                    attributes[key.lower()] = value
                    except:
                        pass

                    # ===== 1. 文本控件 =====
                    if role == pyatspi.ROLE_TEXT:
                        try:
                            text_iface = acc.queryText()
                            if text_iface:
                                text = text_iface.getText(0, text_iface.characterCount)
                                if text and len(text) > 0:
                                    # 判断是发送者还是消息内容
                                    if len(text) < 20 and '\n' not in text and not sender:
                                        sender = text
                                    else:
                                        content = text
                        except:
                            if name:
                                content = name

                    # ===== 2. 标签控件 =====
                    elif role == pyatspi.ROLE_LABEL:
                        if name:
                            if len(name) < 20 and '\n' not in name and not sender:
                                sender = name
                            elif not content:
                                content = name

                    # ===== 3. 图片/图标控件（photo） =====
                    elif role in [pyatspi.ROLE_IMAGE, pyatspi.ROLE_ICON,
                                  pyatspi.ROLE_GRAPHIC, pyatspi.ROLE_PICTURE]:
                        message_type = "photo"
                        # 尝试获取图片路径
                        if name and ('/' in name or '\\' in name):
                            image_path = name
                        # 从属性中获取路径
                        if 'image-path' in attributes:
                            image_path = attributes['image-path']
                        elif 'src' in attributes:
                            image_path = attributes['src']
                        # 设置描述
                        if not content:
                            content = f"[图片]"

                    # ===== 4. 视频控件 =====
                    elif role == pyatspi.ROLE_VIDEO:
                        message_type = "video"
                        # 尝试获取视频路径
                        if name and ('/' in name or '\\' in name):
                            high_res_image_path = name  # 复用字段存储视频路径
                        # 从属性中获取路径
                        if 'video-path' in attributes:
                            high_res_image_path = attributes['video-path']
                        # 设置描述
                        if not content:
                            duration = attributes.get('duration', '')
                            content = f"[视频{duration}]" if duration else "[视频]"

                    # ===== 5. 文档/文件控件（判断是photo/video/other） =====
                    elif role in [pyatspi.ROLE_DOCUMENT, pyatspi.ROLE_FILE]:
                        # 判断是图片、视频还是其他
                        if any(ext in (name or '').lower() for ext in ['.jpg', '.png', '.gif', '.bmp', '.webp', '.jpeg']):
                            message_type = "photo"
                            high_res_image_path = name
                        elif any(ext in (name or '').lower() for ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm']):
                            message_type = "video"
                            high_res_image_path = name
                            if not content:
                                content = f"[视频]"
                        else:
                            # 其他类型（文件、链接等）：标记为other_type，保存到物理机
                            message_type = "other"
                            other_type_data = {
                                'type': 'file',
                                'name': name,
                                'attributes': attributes
                            }

                    # ===== 6. 链接控件（标记为other_type） =====
                    elif role in [pyatspi.ROLE_LINK, pyatspi.ROLE_HYPERLINK]:
                        message_type = "other"
                        url = name or attributes.get('url', attributes.get('href', ''))
                        other_type_data = {
                            'type': 'link',
                            'url': url,
                            'attributes': attributes
                        }

                    # ===== 7. 通过属性判断消息类型 =====
                    # 检查是否有图片属性
                    if 'image' in attributes or 'thumbnail' in attributes:
                        message_type = "photo"
                        if 'thumbnail' in attributes:
                            image_path = attributes['thumbnail']
                        if 'image-path' in attributes:
                            high_res_image_path = attributes['image-path']

                    # 检查是否有视频属性
                    if 'video' in attributes or 'duration' in attributes:
                        message_type = "video"
                        if 'video-path' in attributes:
                            high_res_image_path = attributes['video-path']
                        if not content:
                            duration = attributes.get('duration', '')
                            content = f"[视频{duration}]" if duration else "[视频]"

                    # 递归处理子节点
                    for i in range(acc.childCount):
                        extract_content_recursive(acc.getChildAtIndex(i), depth + 1)

                except Exception as e:
                    logger.debug(f"提取内容时出错 (depth={depth}): {e}")

            # 提取消息内容
            extract_content_recursive(item)

            # 步骤2: 处理其他类型消息（文件、链接等）
            # 如果是其他类型，直接保存到物理机，不推送SSE
            if message_type == "other" and other_type_data:
                try:
                    self._save_other_type_to_disk(sender, other_type_data)
                    logger.info(f"其他类型消息已保存到物理机: type={other_type_data['type']}, sender={sender}")
                    return None  # 不推送SSE
                except Exception as e:
                    logger.error(f"保存其他类型消息失败: {e}")
                    return None

            # 步骤3: [可选] 如果需要提取高清媒体文件，使用视觉方案
            # 注意：仅对photo/video类型启用视觉提取
            if self.enable_universal_extraction and self.universal_extractor:
                # 仅当需要保存文件时才使用视觉提取
                if message_type in ["photo", "video"] and not high_res_image_path:
                    try:
                        import threading

                        def extract_media_async():
                            try:
                                extracted = self.universal_extractor.extract_message(item, sender or "Unknown")
                                if extracted and extracted.high_res_media_path:
                                    logger.info(
                                        f"媒体文件已保存: type={extracted.msg_type.value}, "
                                        f"path={extracted.high_res_media_path}"
                                    )
                                    # TODO: 可以通过回调或其他方式通知文件保存完成
                            except Exception as e:
                                logger.error(f"异步媒体提取失败: {e}")

                        # 启动后台线程提取媒体文件
                        thread = threading.Thread(target=extract_media_async, daemon=True)
                        thread.start()

                    except Exception as e:
                        logger.error(f"启动媒体提取失败: {e}")

            # 步骤4: 构造消息对象（仅text/photo/video）
            if message_type in ["text", "photo", "video"]:
                message = ATSPIMessage(
                    sender=sender or "Unknown",
                    content=content or f"[{message_type.upper()}]",
                    timestamp=datetime.now().isoformat(),
                    message_type=message_type,
                    image_path=image_path,
                    high_res_image_path=high_res_image_path,
                    raw_object=item
                )
                return message
            else:
                # 不支持的消息类型，不推送SSE
                return None

        except Exception as e:
            logger.error(f"从消息项提取内容失败: {e}", exc_info=True)
            return None

    def _save_other_type_to_disk(self, sender: str, other_type_data: dict):
        """
        将其他类型消息（文件、链接等）保存到物理机

        Args:
            sender: 发送者
            other_type_data: 其他类型数据
        """
        try:
            from pathlib import Path
            import json
            from datetime import datetime

            # 保存目录
            save_dir = Path(self.save_dir) / "others"
            save_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            msg_type = other_type_data.get('type', 'unknown')

            if msg_type == 'link':
                # 保存链接元数据
                filename = f"link_{timestamp}.json"
                filepath = save_dir / filename
                data = {
                    'type': 'link',
                    'sender': sender,
                    'url': other_type_data.get('url', ''),
                    'timestamp': datetime.now().isoformat(),
                    'attributes': other_type_data.get('attributes', {})
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"链接已保存: {filepath}")

            elif msg_type == 'file':
                # 保存文件元数据
                filename = f"file_{timestamp}.json"
                filepath = save_dir / filename
                data = {
                    'type': 'file',
                    'sender': sender,
                    'name': other_type_data.get('name', ''),
                    'timestamp': datetime.now().isoformat(),
                    'attributes': other_type_data.get('attributes', {})
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logger.info(f"文件元数据已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存其他类型消息到磁盘失败: {e}", exc_info=True)

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
