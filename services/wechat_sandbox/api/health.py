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
producer = None


def set_components(qm, p1, p2):
    """设置组件（向后兼容）"""
    global queue_manager, producer
    queue_manager = qm
    producer = qm  # HybridProducer 取代了旧的 producer1 + producer2


@router.get("/")
async def health_check():
    """健康检查"""
    try:
        status = {"status": "healthy", "redis": False}

        if queue_manager:
            try:
                # HybridProducer 有 redis 属性
                redis_client = getattr(queue_manager, 'redis', None)
                if redis_client:
                    redis_client.ping()
                    status["redis"] = True
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                status["redis_error"] = str(e)

        if producer:
            status["producer_running"] = True
            stats = producer.get_stats() if hasattr(producer, 'get_stats') else {}
            status.update(stats)

        return status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "reason": str(e)}


@router.get("/status")
async def get_status():
    """获取服务状态"""
    try:
        result = {
            "producer": "initialized" if producer else "not_initialized"
        }

        if producer and hasattr(producer, 'get_stats'):
            result["stats"] = producer.get_stats()

        return result

    except Exception as e:
        logger.error(f"Get status failed: {e}")
        return {"error": str(e)}
