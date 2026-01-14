"""
API模块
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

from api.config import router as config_router
from api.instance import router as instance_router
from api.stream import router as stream_router, set_queue_manager
from api.health import router as health_router, set_components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger
from config.config import config

queue_manager = None
producer1 = None
producer2 = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue_manager, producer1, producer2
    
    try:
        from core.queue.manager import QueueManager
        from core.producer.observer import Observer
        from core.producer.content_fetcher import ContentFetcher
        
        logger.info("Starting Producer Service...")
        
        queue_manager = QueueManager(config.to_dict())
        producer1 = Observer(queue_manager)
        producer2 = ContentFetcher(queue_manager)
        
        set_queue_manager(queue_manager)
        set_components(queue_manager, producer1, producer2)
        
        producer1.start()
        producer2.start()
        
        logger.info("Producer Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Producer Service: {e}")
        raise
    finally:
        logger.info("Shutting down Producer Service...")
        if producer1:
            producer1.stop()
        if producer2:
            producer2.stop()
        if queue_manager:
            queue_manager.close()
        logger.info("Producer Service stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="WeChat Sandbox API",
        version="2.0.0",
        description="WeChat Sandbox API v2.0 - Unified producer service with SSE streaming",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(config_router, prefix="/api/config", tags=["config"])
    app.include_router(instance_router, prefix="/api/instance", tags=["instance"])
    app.include_router(stream_router, prefix="/api/stream", tags=["stream"])
    app.include_router(health_router, prefix="/api/health", tags=["health"])
    
    @app.get("/")
    async def root():
        return {
            "service": "wechat_sandbox",
            "version": "2.0.0",
            "status": "running",
            "message": "WeChat Sandbox API v2.0 is running"
        }
    
    @app.get("/stream")
    async def stream_sse():
        from fastapi.responses import StreamingResponse
        from api.stream import message_stream_generator
        
        return StreamingResponse(
            message_stream_generator(),
            media_type="text/event-stream"
        )
    
    return app


app = create_app()
