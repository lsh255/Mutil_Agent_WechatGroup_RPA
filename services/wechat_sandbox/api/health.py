"""
健康检查API路由
"""

from fastapi import APIRouter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger

router = APIRouter()

queue_manager = None
producer1 = None
producer2 = None


def set_components(qm, p1, p2):
    global queue_manager, producer1, producer2
    queue_manager = qm
    producer1 = p1
    producer2 = p2


@router.get("/")
async def health_check():
    """健康检查"""
    try:
        status = {"status": "healthy", "redis": False}
        
        if queue_manager:
            try:
                queue_manager.redis_client.ping()
                status["redis"] = True
                stream_info = queue_manager.get_stream_info()
                status["streams"] = stream_info
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                status["redis_error"] = str(e)
        
        if producer1:
            status["producer1_running"] = producer1.running if hasattr(producer1, 'running') else False
        
        if producer2:
            status["producer2_running"] = producer2.running if hasattr(producer2, 'running') else False
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "reason": str(e)}


@router.get("/status")
async def get_status():
    """获取服务状态"""
    try:
        result = {
            "queue_manager": "initialized" if queue_manager else "not_initialized"
        }
        
        if queue_manager:
            result["streams"] = queue_manager.get_stream_info()
        
        if producer1:
            result["producer1"] = {
                "running": producer1.running if hasattr(producer1, 'running') else False,
                "type": "observer"
            }
        
        if producer2:
            result["producer2"] = {
                "running": producer2.running if hasattr(producer2, 'running') else False,
                "type": "content_fetcher"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        return {"error": str(e)}
