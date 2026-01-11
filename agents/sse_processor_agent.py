import asyncio
from typing import Optional, Callable, AsyncGenerator, Dict, Any, List
import httpx
import structlog
from datetime import datetime

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'wechat_sandbox'))
from producer_service.agent_consumer import get_consumer
from config import settings

logger = structlog.get_logger()


class SSEProcessorAgent:
    """SSE信息流处理智能体
    
    职责:
        - 连接到wechat_sandbox的SSE流
        - 验证消息格式和内容（消息接收、验证）
        - 消费消息并进行处理（消息消费）
        - 转发消息给Orchestrator工作流（消息转发）
        - 支持消息过滤、路由和转换
        - 提供消息统计和监控
        - 支持自定义消息处理回调
    
    特性:
        - 与SandboxManagerAgent解耦，专注于消息流处理
        - 复用AgentConsumer的SSE连接和消息转换功能
        - 支持多用户多容器消息路由
        - 提供消息重试和错误处理机制
        - 支持消息去重和限流
    """
    
    def __init__(
        self,
        producer_service_url: Optional[str] = None,
        orchestrator_url: Optional[str] = None
    ):
        """初始化SSE处理智能体
        
        Args:
            producer_service_url: Producer服务URL（SSE流地址）
            orchestrator_url: Orchestrator服务URL（工作流触发地址）
        """
        producer_url = producer_service_url or getattr(
            settings.wechat_sandbox,
            'producer_service_url',
            'http://localhost:6789'
        )
        self.orchestrator_url = orchestrator_url or "http://localhost:8000"
        
        self.agent_consumer = get_consumer(
            producer_service_url=producer_url,
            orchestrator_url=self.orchestrator_url
        )
        
        self.is_running = False
        self.message_callback: Optional[Callable] = None
        self.filter_rules: List[Callable[[Dict[str, Any]], bool]] = []
        self.transform_rules: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
        
        self.message_count = 0
        self.success_count = 0
        self.error_count = 0
        self.start_time: Optional[datetime] = None
        
        self.processed_ids: set[str] = set()
        self.max_id_cache = 1000
        
        logger.info(
            "SSEProcessorAgent initialized",
            producer_url=producer_url,
            orchestrator_url=self.orchestrator_url
        )
    
    def add_filter_rule(self, rule: Callable[[Dict[str, Any]], bool]):
        """添加消息过滤规则
        
        Args:
            rule: 过滤规则函数，返回True表示保留消息
        """
        self.filter_rules.append(rule)
        logger.info("消息过滤规则已添加", rule_count=len(self.filter_rules))
    
    def add_transform_rule(self, rule: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """添加消息转换规则
        
        Args:
            rule: 转换规则函数，返回转换后的消息
        """
        self.transform_rules.append(rule)
        logger.info("消息转换规则已添加", rule_count=len(self.transform_rules))
    
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        """设置消息处理回调函数
        
        Args:
            callback: 回调函数，接收消息数据
        """
        self.message_callback = callback
        logger.info("消息回调函数已设置")
    
    async def _validate_message(self, message: Dict[str, Any]) -> bool:
        """验证消息格式和内容
        
        Args:
            message: 原始消息数据
        
        Returns:
            是否通过验证
        """
        if not message:
            logger.warn("收到空消息")
            return False
        
        required_fields = ["id", "sender", "content", "type"]
        for field in required_fields:
            if field not in message:
                logger.warn("消息缺少必需字段", field=field, message_id=message.get("id"))
                return False
        
        message_id = message.get("id")
        if not message_id:
            logger.warn("消息ID为空")
            return False
        
        if message_id in self.processed_ids:
            logger.debug("消息重复，已跳过", message_id=message_id)
            return False
        
        return True
    
    async def _apply_filters(self, message: Dict[str, Any]) -> bool:
        """应用过滤规则
        
        Args:
            message: 消息数据
        
        Returns:
            是否保留消息
        """
        for rule in self.filter_rules:
            try:
                if not rule(message):
                    logger.debug("消息被过滤规则拦截", rule=rule.__name__, message_id=message.get("id"))
                    return False
            except Exception as e:
                logger.error("过滤规则执行失败", rule=rule.__name__, error=str(e))
        
        return True
    
    async def _apply_transforms(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """应用转换规则
        
        Args:
            message: 原始消息数据
        
        Returns:
            转换后的消息数据
        """
        transformed = message.copy()
        
        for rule in self.transform_rules:
            try:
                transformed = rule(transformed)
            except Exception as e:
                logger.error("转换规则执行失败", rule=rule.__name__, error=str(e))
        
        return transformed
    
    async def _deduplicate(self, message_id: str):
        """消息去重缓存管理
        
        Args:
            message_id: 消息ID
        """
        self.processed_ids.add(message_id)
        
        if len(self.processed_ids) > self.max_id_cache:
            self.processed_ids.pop()
    
    async def _forward_to_orchestrator(self, message: Dict[str, Any]) -> bool:
        """转发消息到Orchestrator工作流
        
        Args:
            message: 消息数据
        
        Returns:
            是否转发成功
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/workflow/trigger",
                    json=message,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(
                        "消息已转发到Orchestrator",
                        message_id=message.get("id"),
                        sender=message.get("sender")
                    )
                    return True
                else:
                    logger.error(
                        "转发消息到Orchestrator失败",
                        status_code=response.status_code,
                        response_text=response.text[:200],
                        message_id=message.get("id")
                    )
                    return False
                    
        except httpx.RequestError as e:
            logger.error("转发请求失败", error=str(e), message_id=message.get("id"))
            return False
        except Exception as e:
            logger.error("转发消息异常", error=str(e), message_id=message.get("id"))
            return False
    
    async def _process_message(self, message: Dict[str, Any]):
        """处理单条消息
        
        Args:
            message: 消息数据
        """
        self.message_count += 1
        message_id = message.get("id")
        
        try:
            logger.debug(
                "开始处理消息",
                message_id=message_id,
                sender=message.get("sender"),
                content_type=message.get("type")
            )
            
            if not await self._validate_message(message):
                self.error_count += 1
                return
            
            await self._deduplicate(message_id)
            
            if not await self._apply_filters(message):
                return
            
            transformed_message = await self._apply_transforms(message)
            
            if await self._forward_to_orchestrator(transformed_message):
                self.success_count += 1
            
            if self.message_callback:
                try:
                    await self.message_callback(transformed_message)
                except Exception as e:
                    logger.error("消息回调执行失败", error=str(e), message_id=message_id)
                    
        except Exception as e:
            self.error_count += 1
            logger.error("处理消息失败", error=str(e), message_id=message_id)
    
    async def _consume_loop(self):
        """消费消息循环"""
        while self.is_running:
            try:
                async for message in self.agent_consumer._consume_stream():
                    if not self.is_running:
                        break
                    
                    await self._process_message(message)
                    
            except httpx.RequestError as e:
                logger.error("SSE连接异常，5秒后重试", error=str(e))
                self.error_count += 1
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("消费循环异常，5秒后重试", error=str(e))
                self.error_count += 1
                await asyncio.sleep(5)
    
    async def start(self, auto_forward: bool = True):
        """启动SSE处理智能体
        
        Args:
            auto_forward: 是否自动转发消息到Orchestrator
        """
        if self.is_running:
            logger.warn("SSEProcessorAgent已在运行")
            return
        
        logger.info("启动SSEProcessorAgent", auto_forward=auto_forward)
        
        self.is_running = True
        self.start_time = datetime.now()
        self.message_count = 0
        self.success_count = 0
        self.error_count = 0
        
        if auto_forward:
            asyncio.create_task(self._consume_loop())
        else:
            self.agent_consumer.is_running = True
            asyncio.create_task(self._consume_loop())
    
    def stop(self):
        """停止SSE处理智能体"""
        if not self.is_running:
            return
        
        logger.info("停止SSEProcessorAgent")
        
        self.is_running = False
        self.agent_consumer.stop()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取消息处理统计信息
        
        Returns:
            统计信息字典
        """
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime,
            "message_count": self.message_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": f"{(self.success_count / max(self.message_count, 1) * 100):.2f}%"
        }
    
    async def consume_once(self) -> Optional[Dict[str, Any]]:
        """消费单条消息（用于测试）
        
        Returns:
            消息数据，如果没有消息则返回None
        """
        try:
            async for message in self.agent_consumer._consume_stream():
                await self._process_message(message)
                return message
        except Exception as e:
            logger.error("consume_once失败", error=str(e))
            return None


_processor: Optional[SSEProcessorAgent] = None


def get_processor(
    producer_service_url: Optional[str] = None,
    orchestrator_url: Optional[str] = None
) -> SSEProcessorAgent:
    """获取SSEProcessorAgent单例
    
    Args:
        producer_service_url: Producer服务URL
        orchestrator_url: Orchestrator服务URL
    
    Returns:
        SSEProcessorAgent实例
    """
    global _processor
    if _processor is None:
        _processor = SSEProcessorAgent(producer_service_url, orchestrator_url)
    return _processor
