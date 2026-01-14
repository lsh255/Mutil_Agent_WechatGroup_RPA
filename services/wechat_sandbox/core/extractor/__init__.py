#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息提取器模块

提供消息内容提取功能，支持AT-SPI和视觉两种方案。
"""

from .models import MessageType, ExtractedMessage
from .message_extractor import UniversalMessageExtractor

__all__ = [
    'MessageType',
    'ExtractedMessage',
    'UniversalMessageExtractor',
]
