#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理模块

提供消息提取和处理的工具：
- Extractor: 通用消息提取器
- Classifier: 消息分类器
"""

from .extractor import UniversalMessageExtractor, ExtractedMessage, MessageType

__all__ = ['UniversalMessageExtractor', 'ExtractedMessage', 'MessageType']
