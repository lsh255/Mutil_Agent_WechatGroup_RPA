#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合生产者
结合AT-SPI UI控件和视觉技术的消息获取方案

策略：
1. 主要使用AT-SPI UI控件监听（更稳定、更准确、资源占用更少）
2. 如果AT-SPI不可用或失败，自动降级到视觉方案（作为兜底）
"""

import logging
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProductionMode(Enum):
    """生产模式"""
    ATSPI = "atspi"  # AT-SPI UI控件模式
    VISUAL = "visual"  # 视觉检测模式
    HYBRID = "hybrid"  # 混合模式（AT-SPI优先，失败时降级到视觉）


class HybridProducer:
    """
    混合消息生产者

    架构：
    ┌─────────────────────────────────────────────────────┐
    │              HybridProducer                         │
    ├─────────────────────────────────────────────────────┤
    │                                                     │
    │  ┌──────────────┐      ┌──────────────────┐        │
    │  │ AT-SPI       │──OK──→│  精确消息队列    │        │
    │  │ Observer     │      │  (高效)          │        │
    │  └──────┬───────┘      └──────────────────┘        │
    │         │Failed                                 │
    │         ↓                                       │
    │  ┌──────────────┐      ┌──────────────────┐        │
    │  │ Visual       │──────→│  原始消息队列    │        │
    │  │ Observer     │      │  (兜底)          │        │
    │  └──────────────┘      └──────────────────┘        │
    │         │                                            │
    │         ↓                                            │
    │  ┌──────────────┐                                    │
    │  │ Visual       │──────→│  精确消息队列    │        │
    │  │ Content      │      └──────────────────┘        │
    │  │ Fetcher      │                                    │
    │  └──────────────┘                                    │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        redis_client,
        mode: ProductionMode = ProductionMode.HYBRID,
        raw_queue: str = "wechat:messages:raw",
        precise_queue: str = "wechat:messages:precise",
        save_dir: str = "/host/data"
    ):
        """
        初始化混合生产者

        Args:
            redis_client: Redis客户端
            mode: 生产模式（ATSPI/VISUAL/HYBRID）
            raw_queue: 原始消息队列名（视觉方案使用）
            precise_queue: 精确消息队列名
            save_dir: 文件保存目录（挂载到物理机）
        """
        self.redis = redis_client
        self.mode = mode
        self.raw_queue = raw_queue
        self.precise_queue = precise_queue
        self.save_dir = save_dir

        # AT-SPI观察者
        self.atspi_observer = None

        # 视觉方案已重构为 detector 模块，由 extractor 直接调用
        # 不再需要 visual_observer 和 visual_fetcher

        # 当前活跃模式
        self.active_mode = None

        # 统计信息
        self.stats = {
            'atspi_success': 0,
            'atspi_failed': 0,
            'visual_fallback': 0,
            'total_messages': 0
        }

    def initialize(self) -> bool:
        """
        初始化生产者

        Returns:
            bool: 初始化是否成功
        """
        logger.info(f"正在初始化混合生产者，模式: {self.mode.value}")

        if self.mode in [ProductionMode.ATSPI, ProductionMode.HYBRID]:
            # 尝试初始化AT-SPI观察者
            if self._init_atspi_observer():
                self.active_mode = ProductionMode.ATSPI
                logger.info("✅ 使用AT-SPI UI控件模式")
                return True
            else:
                logger.warning("⚠️ AT-SPI初始化失败")
                if self.mode == ProductionMode.ATSPI:
                    logger.error("AT-SPI模式初始化失败，且不允许降级")
                    return False

        if self.mode == ProductionMode.VISUAL:
            # 视觉模式已重构为 detector 模块，由 extractor 直接调用
            logger.warning("⚠️ 纯视觉模式不可用（已重构为 detector 模块）")
            return False

        return self.active_mode is not None

    def _init_atspi_observer(self) -> bool:
        """
        初始化AT-SPI观察者

        Returns:
            bool: 是否初始化成功
        """
        try:
            from core.atspi.observer import ATSPIObserver

            # 启用通用消息提取，指定保存目录
            self.atspi_observer = ATSPIObserver(
                enable_universal_extraction=True,
                save_dir=self.save_dir
            )

            if self.atspi_observer.initialize():
                # 添加消息处理回调
                self.atspi_observer.add_callback(self._handle_atspi_message)
                return True
            else:
                return False

        except ImportError as e:
            logger.error(f"AT-SPI观察者导入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"AT-SPI观察者初始化失败: {e}")
            return False

    def _init_visual_observer(self) -> bool:
        """
        初始化视觉观察者（兜底方案）

        注意：视觉兜底方案暂时不可用。
        已重构为使用 detector/ 模块，由 extractor 模块直接调用。

        Returns:
            bool: False（视觉方案暂不可用）
        """
        logger.info("视觉兜底方案暂时不可用（已重构为 detector 模块）")
        return False

    def _handle_atspi_message(self, message):
        """
        处理AT-SPI检测到的消息

        Args:
            message: ATSPIMessage对象
        """
        try:
            # 构造精确消息格式
            precise_message = {
                'id': f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'timestamp': message.timestamp,
                'type': message.message_type,
                'sender': message.sender,
                'content': {
                    'type': message.message_type,
                    'text': message.content,
                    'media_path': message.image_path,  # 缩略图路径（如果有）
                    'high_res_media_path': message.high_res_image_path,  # 高清图片路径（仅photo消息）
                    'media_image_base64': None
                },
                'metadata': {
                    'producer': 'hybrid_producer_atspi',
                    'production_mode': 'atspi',
                    'processed_at': datetime.now().isoformat(),
                    'is_photo': message.message_type == 'photo'  # 标记是否为photo消息
                }
            }

            # 推送到精确消息队列
            self._enqueue_precise(precise_message)

            # 更新统计
            self.stats['atspi_success'] += 1
            self.stats['total_messages'] += 1

            logger.info(
                f"✅ AT-SPI消息已推送到精确队列: "
                f"[{message.sender}] {message.content[:30]}"
            )

        except Exception as e:
            logger.error(f"处理AT-SPI消息失败: {e}")
            self.stats['atspi_failed'] += 1

    def _handle_visual_detection(self, detection_result: Dict[str, Any]):
        """
        处理视觉检测到的消息气泡

        Args:
            detection_result: 视觉检测结果
        """
        try:
            # 推送到原始消息队列
            self._enqueue_raw(detection_result)

            # 如果AT-SPI失败，使用ContentFetcher提取内容
            if self.visual_fetcher:
                # 异步处理内容提取
                self.visual_fetcher.process_raw_message(detection_result)

            # 更新统计
            self.stats['visual_fallback'] += 1
            self.stats['total_messages'] += 1

            logger.info("⚠️ 使用视觉方案兜底，已推送到原始队列")

        except Exception as e:
            logger.error(f"处理视觉检测结果失败: {e}")

    def _enqueue_precise(self, message: Dict[str, Any]):
        """
        推送精确消息到队列

        Args:
            message: 精确消息字典
        """
        try:
            # 使用Redis Stream
            stream_id = self.redis.xadd(
                self.precise_queue,
                {k: json.dumps(v) for k, v in message.items()}
            )
            logger.debug(f"消息已推送到精确队列: {stream_id}")
        except Exception as e:
            logger.error(f"推送精确消息失败: {e}")

    def _enqueue_raw(self, detection_result: Dict[str, Any]):
        """
        推送原始检测结果到队列

        Args:
            detection_result: 检测结果字典
        """
        try:
            # 使用Redis Stream
            stream_id = self.redis.xadd(
                self.raw_queue,
                {k: json.dumps(v) for k, v in detection_result.items()}
            )
            logger.debug(f"原始检测已推送到队列: {stream_id}")
        except Exception as e:
            logger.error(f"推送原始检测失败: {e}")

    def start(self):
        """启动生产者"""
        logger.info(f"启动混合生产者，当前模式: {self.active_mode.value}")

        if self.active_mode == ProductionMode.ATSPI and self.atspi_observer:
            # 启动AT-SPI监听
            self.atspi_observer.start_monitoring(interval=0.5)

        elif self.active_mode == ProductionMode.VISUAL:
            # 视觉模式：暂时不可用
            logger.warning("视觉模式暂时不可用（已重构为 detector 模块）")

        elif self.active_mode == ProductionMode.HYBRID:
            # 混合模式：仅启动AT-SPI，视觉方案暂时不可用
            if self.atspi_observer:
                self.atspi_observer.start_monitoring(interval=0.5)

                logger.info("视觉兜底方案暂时不可用，仅使用 AT-SPI 模式")

    def stop(self):
        """停止生产者"""
        logger.info("停止混合生产者")

        if self.atspi_observer:
            self.atspi_observer.stop_monitoring()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取生产者统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            'mode': self.mode.value,
            'active_mode': self.active_mode.value if self.active_mode else None,
            'stats': self.stats,
            'atspi_available': self.atspi_observer is not None,
            'visual_available': False  # 视觉方案已重构为 detector 模块
        }

    def switch_mode(self, new_mode: ProductionMode):
        """
        切换生产模式

        Args:
            new_mode: 新的生产模式
        """
        logger.info(f"切换生产模式: {self.mode.value} -> {new_mode.value}")

        # 停止当前模式
        self.stop()

        # 更新模式
        self.mode = new_mode

        # 重新初始化
        if self.initialize():
            self.start()
        else:
            logger.error(f"切换到{new_mode.value}模式失败")


# 测试代码
if __name__ == "__main__":
    import redis

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建Redis客户端
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)

    # 创建混合生产者
    producer = HybridProducer(
        redis_client=redis_client,
        mode=ProductionMode.HYBRID
    )

    # 初始化
    if producer.initialize():
        print(f"\n✅ 生产者初始化成功")
        print(f"   模式: {producer.active_mode.value}")

        # 启动生产者
        producer.start()

        try:
            print("\n🔄 生产者正在运行...")
            print("   按 Ctrl+C 停止\n")

            # 定期打印统计信息
            while True:
                time.sleep(10)

                stats = producer.get_stats()
                print(f"\n📊 统计信息:")
                print(f"   总消息数: {stats['stats']['total_messages']}")
                print(f"   AT-SPI成功: {stats['stats']['atspi_success']}")
                print(f"   AT-SPI失败: {stats['stats']['atspi_failed']}")
                print(f"   视觉兜底: {stats['stats']['visual_fallback']}")
                print(f"   当前模式: {stats['active_mode']}")

        except KeyboardInterrupt:
            print("\n\n🛑 停止生产者...")
            producer.stop()

            # 打印最终统计
            stats = producer.get_stats()
            print(f"\n📊 最终统计:")
            print(f"   总消息数: {stats['stats']['total_messages']}")
            print(f"   AT-SPI成功: {stats['stats']['atspi_success']}")
            print(f"   AT-SPI失败: {stats['stats']['atspi_failed']}")
            print(f"   视觉兜底: {stats['stats']['visual_fallback']}")

    else:
        print("❌ 生产者初始化失败")
