"""
Agent消费者模块
负责从SSE流消费消息并转发给统一智能体系统
"""

import asyncio
import json
from typing import AsyncGenerator, Optional, Dict, Any
import httpx
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.logger import logger
from config.config import config


class AgentConsumer:
    """
    Agent消费者
    
    职责:
        - 连接到 wechat_sandbox 的 SSE 流
        - 转换消息格式为统一智能体系统期望的格式
        - 将消息转发给 Orchestrator-Worker 工作流
    """
    
    def __init__(
        self,
        producer_service_url: Optional[str] = None,
        orchestrator_url: Optional[str] = None
    ):
        self.producer_service_url = producer_service_url or config.get(
            'producer_service', {}
        ).get('url', 'http://localhost:6789')
        self.orchestrator_url = orchestrator_url or config.get(
            'orchestrator', {}
        ).get('url', 'http://localhost:8000')
        self.stream_url = f"{self.producer_service_url}/stream"
        self.is_running = False
        self.last_id = '0-0'
        
        logger.info(
            "AgentConsumer initialized",
            stream_url=self.stream_url,
            orchestrator_url=self.orchestrator_url
        )
    
    def _convert_message_format(
        self, 
        original_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            precise_content = original_message.get('precise_content', {})
            metadata = original_message.get('metadata', {})
            
            converted = {
                'id': original_message.get('id'),
                'sender': metadata.get('sender', 'unknown'),
                'content': precise_content.get('text') or precise_content.get('content'),
                'type': original_message.get('type', 'text'),
                'timestamp': original_message.get('timestamp'),
                'position': original_message.get('position'),
                'metadata': metadata
            }
            
            logger.debug(
                "Message converted",
                original_id=original_message.get('id'),
                sender=converted['sender'],
                content_type=converted['type']
            )
            
            return converted
            
        except Exception as e:
            logger.error(
                "Message conversion failed",
                error=str(e),
                original_message=original_message
            )
            return original_message
    
    async def _consume_stream(self) -> AsyncGenerator[Dict[str, Any], None]:
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream(
                    "GET",
                    self.stream_url,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache"
                    }
                ) as response:
                    if response.status_code == 200:
                        logger.info("Connected to SSE stream")
                        
                        async for line in response.aiter_lines():
                            if not self.is_running:
                                break
                            
                            if line.startswith("data: "):
                                data = line[6:]
                                try:
                                    original_message = json.loads(data)
                                    
                                    converted_message = self._convert_message_format(
                                        original_message
                                    )
                                    
                                    yield converted_message
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(
                                        "Failed to parse message JSON",
                                        error=str(e),
                                        data=data[:100]
                                    )
                                    continue
                    else:
                        logger.error(
                            "Failed to connect to SSE stream",
                            status_code=response.status_code
                        )
                        
            except httpx.RequestError as e:
                logger.error("Request error while consuming stream", error=str(e))
            except Exception as e:
                logger.error("Unexpected error while consuming stream", error=str(e))
    
    async def _forward_to_orchestrator(self, message: Dict[str, Any]) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/workflow/trigger",
                    json=message,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(
                        "Message forwarded to orchestrator",
                        message_id=message.get('id'),
                        sender=message.get('sender')
                    )
                    return True
                else:
                    logger.error(
                        "Failed to forward message to orchestrator",
                        status_code=response.status_code,
                        response_text=response.text[:200]
                    )
                    return False
                    
        except httpx.RequestError as e:
            logger.error("Request error while forwarding to orchestrator", error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error while forwarding to orchestrator", error=str(e))
            return False
    
    async def start(self, auto_forward: bool = True):
        self.is_running = True
        logger.info("AgentConsumer started")
        
        while self.is_running:
            try:
                async for message in self._consume_stream():
                    if not self.is_running:
                        break
                    
                    if auto_forward:
                        await self._forward_to_orchestrator(message)
                    
            except Exception as e:
                logger.error("Error in consumer loop, retrying in 5 seconds", error=str(e))
                await asyncio.sleep(5)
    
    def stop(self):
        logger.info("Stopping AgentConsumer")
        self.is_running = False
    
    async def consume_once(self) -> Optional[Dict[str, Any]]:
        try:
            async for message in self._consume_stream():
                return message
        except Exception as e:
            logger.error("Error in consume_once", error=str(e))
            return None


_consumer: Optional[AgentConsumer] = None


def get_consumer(
    producer_service_url: Optional[str] = None,
    orchestrator_url: Optional[str] = None
) -> AgentConsumer:
    global _consumer
    if _consumer is None:
        _consumer = AgentConsumer(producer_service_url, orchestrator_url)
    return _consumer
