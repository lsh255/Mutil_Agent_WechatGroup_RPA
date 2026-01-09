"""
日志工具模块
"""

import logging
import os

def setup_logger(name: str = "wechat_producer", level: int = logging.INFO):
    """
    配置日志记录器
    
    输入:
        name: 日志记录器名称
        level: 日志级别
    返回:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

logger = setup_logger()
