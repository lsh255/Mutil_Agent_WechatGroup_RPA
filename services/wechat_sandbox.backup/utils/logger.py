"""  # 模块文档字符串，说明这是工具包的初始化文件
日志工具模块
"""

import logging  # Python标准日志库
import os  # 操作系统接口（未使用，保留用于未来扩展）

def setup_logger(name: str = "wechat_producer", level: int = logging.INFO):
    """
    配置日志记录器，设置日志级别和输出格式

    输入:
        name: 日志记录器名称，默认"wechat_producer"
        level: 日志级别，默认logging.INFO
    返回:
        logging.Logger: 配置好的日志记录器实例
    """
    logger = logging.getLogger(name)  # 获取或创建日志记录器
    logger.setLevel(level)  # 设置日志级别

    if not logger.handlers:  # 检查是否已有处理器（避免重复添加）
        handler = logging.StreamHandler()  # 创建控制台输出处理器
        formatter = logging.Formatter(  # 创建日志格式化器
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # 格式：时间 - 记录器名 - 级别 - 消息
        )
        handler.setFormatter(formatter)  # 设置处理器格式
        logger.addHandler(handler)  # 添加处理器到日志记录器

    return logger  # 返回配置好的日志记录器

logger = setup_logger()  # 创建全局日志记录器实例
