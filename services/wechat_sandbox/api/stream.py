"""
SSE流API路由
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger

router = APIRouter()

queue_manager = None
redis_client = None
precise_queue = "wechat:messages:precise"


def set_queue_manager(qm):
    """设置队列管理器（向后兼容）"""
    global queue_manager
    queue_manager = qm
    # 如果传入的是 HybridProducer，提取其 Redis 客户端
    if hasattr(qm, 'redis'):
        global redis_client
        redis_client = qm.redis


async def message_stream_generator() -> AsyncGenerator[str, None]:
    """
    SSE消息流生成器

    从Redis Stream读取消息并流式输出
    """
    last_id = '0-0'

    try:
        while True:
            if redis_client:
                # 从 Redis Stream 读取消息
                messages = redis_client.xrange(
                    precise_queue,
                    min=last_id,
                    count=10
                )
                
                for message_id, fields in messages:
                    # 更新 last_id
                    if message_id > last_id:
                        last_id = message_id

                        # 解析消息字段（Redis Stream 字段需要从 JSON 解析）
                        parsed_message = {}
                        for key, value in fields.items():
                            try:
                                parsed_message[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                parsed_message[key] = value

                        # 构造 SSE 消息
                        message_json = json.dumps(parsed_message, ensure_ascii=False)

                        yield f"data: {message_json}\n\n"
                        logger.info(f"Streamed message: {message_id}")
            
            await asyncio.sleep(0.5)
            
    except Exception as e:
        logger.error(f"Message stream generator error: {e}")
        raise


@router.get("/messages")
async def stream_messages():
    """
    SSE流式输出端点
    
    返回微信消息流，供monitor_agent.py消费
    """
    try:
        return StreamingResponse(
            message_stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Stream messages failed: {e}")
        return {"error": str(e)}


@router.get("/status")
async def stream_status():
    """
    SSE状态流
    """
    async def event_generator():
        while True:
            status = {"status": "alive"}
            if queue_manager:
                status["queue_info"] = queue_manager.get_stream_info()
            yield f"data: {json.dumps(status)}\n\n"
            await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
