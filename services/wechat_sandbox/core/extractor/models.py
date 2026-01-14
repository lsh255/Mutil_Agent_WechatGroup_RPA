#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息数据模型

定义了消息提取过程中使用的数据结构。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


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

        import json

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
