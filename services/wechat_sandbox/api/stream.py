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


def set_queue_manager(qm):
    global queue_manager
    queue_manager = qm


async def message_stream_generator() -> AsyncGenerator[str, None]:
    """
    SSE消息流生成器
    
    从Redis Stream读取消息并流式输出
    """
    last_id = '0-0'
    
    try:
        while True:
            if queue_manager:
                messages = queue_manager.read_precise_for_streaming(count=10)
                
                for message in messages:
                    message_id = message.get('redis_id', 'unknown')
                    
                    if message_id > last_id:
                        last_id = message_id
                        
                        message_json = json.dumps({
                            'id': message.get('id'),
                            'timestamp': message.get('timestamp'),
                            'type': message.get('type'),
                            'position': message.get('position'),
                            'precise_content': message.get('precise_content', {}),
                            'metadata': message.get('metadata', {})
                        }, ensure_ascii=False)
                        
                        yield f"data: {message_json}\n\n"
                        logger.info(f"Streamed message: {message.get('id')}")
            
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
