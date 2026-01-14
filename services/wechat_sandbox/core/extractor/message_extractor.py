#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用消息提取器 - 通过点击消息判断类型并提取内容

仅处理3种消息类型：文本、图片、视频
其他类型（文件、链接、表情包等）直接保存到物理机，不通过SSE推送

新逻辑：
1. 所有消息先尝试点击
2. 检测是否唤起新窗口
3. 根据窗口标题判断消息类型：
   - 无窗口 → 文本消息
   - "Photos and Videos" → 图片/视频
     - 通过窗口内容变化检测区分（复用 detector/ 模块）
       * 画面不变 → 图片
       * 画面变化 → 视频
   - 其他窗口 → 文件/链接等，保存到物理机

新增功能（v2.1）：
- 窗口内容变化检测：区分图片和视频（复用 detector/ 模块）
"""

import time
import logging
import os
import json
import subprocess
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型（仅3种）"""
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    OTHER = "other"  # 用于内部标记，不通过SSE推送


@dataclass
class ExtractedMessage:
    """提取的消息数据结构"""
    msg_id: str
    timestamp: float
    msg_type: MessageType
    sender: str
    content_text: str
    media_path: Optional[str] = None
    high_res_media_path: Optional[str] = None
    window_detected: bool = False
    window_title: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_sse_json(self) -> str:
        """转换为SSE JSONL格式（仅text/photo/video）"""
        if self.msg_type == MessageType.OTHER:
            # 其他类型不通过SSE推送
            return ""

        sse_data = {
            "id": self.msg_id,
            "timestamp": self.timestamp,
            "type": self.msg_type.value,
            "sender": self.sender,
            "content": {
                "type": self.msg_type.value,
                "text": self.content_text,
                "media_path": self.media_path,
                "high_res_media_path": self.high_res_media_path,
                "media_image_base64": None
            },
            "group_name": "微信群聊",  # TODO: 从配置获取
            "window_detected": self.window_detected,
            "window_title": self.window_title,
            "metadata": self.metadata or {}
        }
        return json.dumps(sse_data, ensure_ascii=False)


class UniversalMessageExtractor:
    """
    通用消息提取器

    工作流程：
    1. 点击消息
    2. 检测是否有新窗口打开
    3. 根据窗口标题判断消息类型
    4. 提取内容并保存（如需要）
    5. 关闭窗口
    """

    def __init__(self, save_dir: str = "/host/data"):
        """
        初始化提取器

        Args:
            save_dir: 保存目录（挂载到物理机）
        """
        self.registry = None
        self.desktop = None
        self.wechat_window = None
        self.current_window = None

        # 保存目录结构（仅photos/videos/others）
        self.save_dir = Path(save_dir)
        self.photos_dir = self.save_dir / "photos"
        self.videos_dir = self.save_dir / "videos"
        self.others_dir = self.save_dir / "others"

        # 创建目录
        for dir_path in [self.photos_dir, self.videos_dir, self.others_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 初始化 detector 模块
        from core.detector.visual_monitor import VisualMonitor
        from core.detector.change_detector import ChangeDetector

        self.visual_monitor = VisualMonitor()
        self.change_detector = ChangeDetector()

        logger.info(f"消息提取器初始化，保存目录: {self.save_dir}")

    def initialize(self) -> bool:
        """
        初始化AT-SPI连接

        Returns:
            bool: 初始化是否成功
        """
        try:
            import pyatspi

            logger.info("正在初始化AT-SPI连接...")

            self.registry = pyatspi.Registry
            self.desktop = pyatspi.Registry.getDesktop(0)

            if not self._find_wechat_window():
                logger.warning("未找到微信窗口")
                return False

            logger.info("消息提取器初始化成功")
            return True

        except ImportError as e:
            logger.error(f"pyatspi库未安装: {e}")
            return False
        except Exception as e:
            logger.error(f"初始化失败: {e}", exc_info=True)
            return False

    def _find_wechat_window(self) -> bool:
        """查找微信窗口"""
        try:
            import pyatspi

            for i in range(self.desktop.childCount):
                try:
                    app = self.desktop.getChildAtIndex(i)
                    if any(name in (app.name or "").lower() for name in ['wechat', '微信']):
                        for j in range(app.childCount):
                            child = app.getChildAtIndex(j)
                            if child.getRole() in [pyatspi.ROLE_WINDOW, pyatspi.ROLE_FRAME]:
                                self.wechat_window = child
                                logger.info(f"找到微信窗口: {child.name}")
                                return True
                except:
                    continue
            return False

        except Exception as e:
            logger.error(f"查找微信窗口失败: {e}")
            return False

    def get_all_windows(self) -> List[Dict]:
        """
        获取所有当前打开的窗口

        Returns:
            List[Dict]: 窗口列表，包含name, role, obj
        """
        windows = []
        try:
            import pyatspi

            for i in range(self.desktop.childCount):
                try:
                    app = self.desktop.getChildAtIndex(i)
                    for j in range(app.childCount):
                        window = app.getChildAtIndex(j)
                        windows.append({
                            'name': window.name or "",
                            'role': window.getRoleName(),
                            'obj': window
                        })
                except:
                    continue

            return windows

        except Exception as e:
            logger.error(f"获取窗口列表失败: {e}")
            return []

    def get_message_bounds(self, message_item) -> Optional[Dict[str, int]]:
        """
        获取消息项的屏幕坐标

        Args:
            message_item: AT-SPI消息项对象

        Returns:
            Dict: {x, y, width, height}
        """
        try:
            import pyatspi

            # 尝试获取组件接口
            component = message_item.queryComponent()
            if component:
                bbox = component.getExtents(pyatspi.DESKTOP_COORDS)
                return {
                    'x': bbox.x,
                    'y': bbox.y,
                    'width': bbox.width,
                    'height': bbox.height
                }

            # 递归查找父级
            def find_component(acc, depth=0):
                if depth > 10:
                    return None
                try:
                    comp = acc.queryComponent()
                    if comp:
                        bbox = comp.getExtents(pyatspi.DESKTOP_COORDS)
                        return {
                            'x': bbox.x, 'y': bbox.y,
                            'width': bbox.width, 'height': bbox.height
                        }
                except:
                    pass
                try:
                    if acc.parent:
                        return find_component(acc.parent, depth + 1)
                except:
                    pass
                return None

            return find_component(message_item)

        except Exception as e:
            logger.error(f"获取消息坐标失败: {e}")
            return None

    def click_message(self, bounds: Dict[str, int]) -> bool:
        """
        点击消息

        Args:
            bounds: 屏幕坐标

        Returns:
            bool: 是否成功
        """
        try:
            center_x = bounds['x'] + bounds['width'] // 2
            center_y = bounds['y'] + bounds['height'] // 2

            logger.debug(f"点击坐标: ({center_x}, {center_y})")

            # 使用xdotool点击
            result = subprocess.run(
                ['xdotool', 'mousemove', str(center_x), str(center_y), 'click', '1'],
                capture_output=True,
                timeout=5
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"点击失败: {e}")
            return False

    def wait_for_new_window(self, timeout: float = 2.0) -> Optional[Dict]:
        """
        等待并检测新窗口

        Args:
            timeout: 超时时间（秒）

        Returns:
            Dict: 新窗口信息 {name, role, obj}，如果没有新窗口返回None
        """
        try:
            # 记录点击前的窗口
            before_windows = set(w['name'] for w in self.get_all_windows())

            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(0.1)

                current_windows = self.get_all_windows()
                current_names = set(w['name'] for w in current_windows)

                # 检测新增的窗口
                new_names = current_names - before_windows
                if new_names:
                    # 找到新窗口
                    for window in current_windows:
                        if window['name'] in new_names:
                            logger.info(f"检测到新窗口: {window['name']}")
                            return window

            return None

        except Exception as e:
            logger.error(f"等待新窗口失败: {e}")
            return None

    def determine_message_type_by_content(self, window_info: Dict) -> MessageType:
        """
        通过窗口内容变化判断是图片还是视频（复用 detector 模块）

        Args:
            window_info: 窗口信息

        Returns:
            MessageType: PHOTO 或 VIDEO
        """
        try:
            # 获取窗口坐标
            window_bounds = self.get_message_bounds(window_info['obj'])
            if not window_bounds:
                logger.warning("无法获取窗口坐标，默认为图片")
                return MessageType.PHOTO

            logger.info("开始窗口内容变化检测（复用 detector 模块）...")

            # 采样配置
            num_samples = 3
            sample_interval = 0.5  # 秒

            screenshots = []

            # 多次采样（使用 VisualMonitor）
            for i in range(num_samples):
                time.sleep(sample_interval)
                screenshot = self.visual_monitor.capture_window_area(window_bounds)
                if screenshot is not None:
                    screenshots.append(screenshot)
                    logger.debug(f"已采集第 {i+1} 张截图")
                else:
                    logger.warning(f"第 {i+1} 次截图失败")

            # 如果采样不足，默认为图片
            if len(screenshots) < 2:
                logger.warning("采样数量不足，默认为图片")
                return MessageType.PHOTO

            # 对比相邻截图（使用 ChangeDetector）
            changes = []
            for i in range(len(screenshots) - 1):
                is_changed = self.change_detector.detect_image_change(screenshots[i], screenshots[i+1])
                changes.append(is_changed)
                logger.debug(f"截图 {i+1} -> {i+2} 变化: {is_changed}")

            # 判断结果
            has_change = any(changes)

            if has_change:
                logger.info("✅ 检测到窗口内容变化 → 判断为视频")
                return MessageType.VIDEO
            else:
                logger.info("✅ 窗口内容无变化 → 判断为图片")
                return MessageType.PHOTO

        except Exception as e:
            logger.error(f"窗口内容变化检测失败: {e}，默认为图片")
            return MessageType.PHOTO

    def determine_message_type(self, window_title: str, window_info: Optional[Dict] = None) -> MessageType:
        """
        根据窗口标题判断消息类型（仅text/photo/video）

        Args:
            window_title: 窗口标题
            window_info: 窗口信息（用于内容变化检测）

        Returns:
            MessageType: 消息类型（text/photo/video/other）
        """
        if not window_title:
            return MessageType.TEXT

        title_lower = window_title.lower()

        # Photos and Videos窗口 → 通过内容变化判断是 photo 还是 video
        if any(keyword in title_lower for keyword in ['photos and videos', 'photos', 'videos']):
            if window_info:
                # 使用窗口内容变化检测
                logger.info("检测到 'Photos and Videos' 窗口，启用内容变化检测...")
                return self.determine_message_type_by_content(window_info)
            else:
                # 如果没有窗口信息，默认为图片（向后兼容）
                logger.warning("缺少窗口信息，默认为图片")
                return MessageType.PHOTO

        # 其他窗口 → 标记为OTHER，保存到物理机
        # 包括：File Transfer、Browser等
        return MessageType.OTHER

    def extract_media_from_window(self, window_info: Dict, msg_type: MessageType) -> Optional[str]:
        """
        从窗口提取媒体文件

        Args:
            window_info: 窗口信息
            msg_type: 消息类型

        Returns:
            str: 保存的文件路径
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            window_obj = window_info['obj']

            # 生成文件名（仅photo/video）
            if msg_type == MessageType.PHOTO:
                ext = '.png'
                save_path = self.photos_dir / f"photo_{timestamp}{ext}"
            elif msg_type == MessageType.VIDEO:
                ext = '.mp4'
                save_path = self.videos_dir / f"video_{timestamp}{ext}"
            else:
                # 其他类型保存到others目录
                ext = '.dat'
                save_path = self.others_dir / f"other_{timestamp}{ext}"

            # 方法1: 查找文件路径
            file_path = self._find_file_path_in_window(window_obj)
            if file_path:
                logger.info(f"找到文件路径: {file_path}")
                return self._save_file(file_path, save_path)

            # 方法2: 截图
            logger.info("未找到文件路径，尝试截图...")
            return self._screenshot_window(window_obj, str(save_path))

        except Exception as e:
            logger.error(f"提取媒体失败: {e}")
            return None

    def _find_file_path_in_window(self, window_obj) -> Optional[str]:
        """在窗口中查找文件路径"""
        try:
            import pyatspi

            def find_recursive(acc, depth=0) -> Optional[str]:
                if depth > 20:
                    return None

                try:
                    name = acc.name or ""
                    role = acc.getRoleName().lower()

                    # 检查是否包含路径
                    if name and ('/' in name or '\\' in name):
                        return name

                    # 检查属性
                    try:
                        attrs = acc.getAttributes()
                        if attrs:
                            for attr in attrs:
                                if 'path' in attr.lower() or 'url' in attr.lower():
                                    if '=' in attr:
                                        return attr.split('=', 1)[1]
                    except:
                        pass

                    for i in range(acc.childCount):
                        result = find_recursive(acc.getChildAtIndex(i), depth + 1)
                        if result:
                            return result

                except:
                    pass

                return None

            return find_recursive(window_obj)

        except Exception as e:
            logger.error(f"查找文件路径失败: {e}")
            return None

    def _save_file(self, source_path: str, dest_path: Path) -> Optional[str]:
        """保存文件"""
        try:
            if os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, dest_path)
                logger.info(f"文件已保存: {dest_path}")
                return str(dest_path)

            # 如果是URL，下载
            if source_path.startswith('http'):
                result = subprocess.run(
                    ['wget', '-O', str(dest_path), source_path],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    logger.info(f"文件已下载: {dest_path}")
                    return str(dest_path)

            return None

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return None

    def _screenshot_window(self, window_obj, save_path: str) -> Optional[str]:
        """截图窗口"""
        try:
            # 获取窗口坐标
            bounds = self.get_message_bounds(window_obj)
            if not bounds:
                return None

            # 使用scrot截图
            result = subprocess.run([
                'scrot',
                f'{bounds["x"]},{bounds["y"]},{bounds["x"] + bounds["width"]},{bounds["y"] + bounds["height"]}',
                '-o', str(save_path)
            ], capture_output=True, timeout=5)

            if result.returncode == 0:
                logger.info(f"截图已保存: {save_path}")
                return save_path

            return None

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def close_window(self, window_obj) -> bool:
        """关闭窗口"""
        try:
            import pyatspi

            # 方法1: AT-SPI关闭
            try:
                action = window_obj.queryAction()
                if action:
                    for i in range(action.nActions):
                        if 'close' in action.getName(i).lower():
                            action.doAction(i)
                            return True
            except:
                pass

            # 方法2: 快捷键
            subprocess.run(['xdotool', 'key', 'Alt+F4'], capture_output=True, timeout=2)
            return True

        except Exception as e:
            logger.error(f"关闭窗口失败: {e}")
            return False

    def extract_message(self, message_item, sender: str = "Unknown") -> Optional[ExtractedMessage]:
        """
        完整的消息提取流程

        Args:
            message_item: AT-SPI消息项对象
            sender: 发送者

        Returns:
            ExtractedMessage: 提取的消息
        """
        try:
            msg_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            timestamp = datetime.now().timestamp()
            processed_at = datetime.now().isoformat()

            # 步骤1: 获取消息坐标
            bounds = self.get_message_bounds(message_item)
            if not bounds:
                # 无法获取坐标，可能是文本消息
                return self._create_text_message(msg_id, timestamp, sender, processed_at)

            # 步骤2: 点击消息
            if not self.click_message(bounds):
                # 点击失败，可能是文本消息
                return self._create_text_message(msg_id, timestamp, sender, processed_at)

            # 步骤3: 等待新窗口
            new_window = self.wait_for_new_window(timeout=2.0)

            if not new_window:
                # 没有新窗口 → 文本消息
                return self._create_text_message(msg_id, timestamp, sender, processed_at)

            # 步骤4: 根据窗口标题和内容判断类型
            window_title = new_window['name']
            msg_type = self.determine_message_type(window_title, window_info=new_window)

            logger.info(f"窗口标题: {window_title}, 消息类型: {msg_type.value}")

            # 步骤5: 处理不同类型的消息
            high_res_path = None
            extracted_at = datetime.now().isoformat()

            if msg_type == MessageType.OTHER:
                # 其他类型：保存到物理机，不返回消息对象
                self._save_other_type_to_disk(window_title, sender, new_window)
                self.close_window(new_window['obj'])
                return None

            elif msg_type in [MessageType.PHOTO, MessageType.VIDEO]:
                # photo/video：提取媒体文件
                high_res_path = self.extract_media_from_window(new_window, msg_type)

            # 步骤6: 关闭窗口
            self.close_window(new_window['obj'])

            # 步骤7: 构造消息对象（仅text/photo/video）
            if msg_type in [MessageType.TEXT, MessageType.PHOTO, MessageType.VIDEO]:
                metadata = {
                    "producer": "universal_extractor",
                    "production_mode": "visual",
                    "processed_at": processed_at,
                    "extracted_at": extracted_at,
                    "window_opened": True
                }

                if high_res_path:
                    metadata["save_path"] = high_res_path

                content_text = f"[{msg_type.value.upper()}]"

                return ExtractedMessage(
                    msg_id=msg_id,
                    timestamp=timestamp,
                    msg_type=msg_type,
                    sender=sender,
                    content_text=content_text,
                    high_res_media_path=high_res_path,
                    window_detected=True,
                    window_title=window_title,
                    metadata=metadata
                )
            else:
                # 不支持的消息类型
                return None

        except Exception as e:
            logger.error(f"提取消息失败: {e}", exc_info=True)
            return None

    def _create_text_message(self, msg_id: str, timestamp: float, sender: str,
                            processed_at: str) -> ExtractedMessage:
        """创建文本消息对象"""
        return ExtractedMessage(
            msg_id=msg_id,
            timestamp=timestamp,
            msg_type=MessageType.TEXT,
            sender=sender,
            content_text="",  # 需要从消息项提取
            window_detected=False,
            window_title=None,
            metadata={
                "producer": "universal_extractor",
                "production_mode": "visual",
                "processed_at": processed_at,
                "window_opened": False
            }
        )

    def _save_other_type_to_disk(self, window_title: str, sender: str, window_info: Dict):
        """
        将其他类型消息（文件、链接等）保存到物理机

        Args:
            window_title: 窗口标题
            sender: 发送者
            window_info: 窗口信息
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            save_path = self.others_dir / f"other_{timestamp}.json"

            # 判断类型
            msg_type = "unknown"
            if "file" in window_title.lower():
                msg_type = "file"
            elif "browser" in window_title.lower() or "link" in window_title.lower():
                msg_type = "link"

            # 尝试提取更多信息
            file_path = self._find_file_path_in_window(window_info['obj'])

            # 保存元数据
            data = {
                'type': msg_type,
                'sender': sender,
                'window_title': window_title,
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"其他类型消息已保存到物理机: type={msg_type}, path={save_path}")

        except Exception as e:
            logger.error(f"保存其他类型消息到磁盘失败: {e}", exc_info=True)


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    extractor = UniversalMessageExtractor(save_dir="/tmp/host_data")

    if extractor.initialize():
        logger.info("通用消息提取器已就绪")
    else:
        logger.error("初始化失败")
