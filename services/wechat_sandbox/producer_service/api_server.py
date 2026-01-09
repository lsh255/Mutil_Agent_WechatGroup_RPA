"""
FastAPI服务器
职责：
1. 提供HTTP API接口
2. 实现SSE流式输出端点
3. 提供健康检查和状态查询接口
"""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
import uvicorn
import os
import sys
import cv2
import base64

from .queue_manager import RedisQueueManager
from .producer1_observer import Producer1Observer
from .producer2_content_fetcher import Producer2ContentFetcher
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger
from utils.config import config

queue_manager = None
producer1 = None
producer2 = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global queue_manager, producer1, producer2
    
    try:
        logger.info("Starting Producer Service...")
        
        queue_manager = RedisQueueManager()
        producer1 = Producer1Observer(queue_manager)
        producer2 = Producer2ContentFetcher(queue_manager)
        
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
        logger.info("Producer Service stopped")

app = FastAPI(title="WeChat Message Producer Service", lifespan=lifespan)

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "WeChat Message Producer Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        if queue_manager:
            stream_info = queue_manager.get_stream_info()
            return {
                "status": "healthy",
                "streams": stream_info,
                "producer1_running": producer1.running if producer1 else False,
                "producer2_running": producer2.running if producer2 else False
            }
        else:
            return {"status": "unhealthy", "reason": "Queue manager not initialized"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "reason": str(e)}

@app.get("/status")
async def get_status():
    """获取服务状态"""
    try:
        if queue_manager:
            stream_info = queue_manager.get_stream_info()
            return {
                "queue_manager": "initialized",
                "streams": stream_info,
                "producer1": {
                    "running": producer1.running if producer1 else False,
                    "type": "observer"
                },
                "producer2": {
                    "running": producer2.running if producer2 else False,
                    "type": "content_fetcher"
                }
            }
        else:
            return {"queue_manager": "not initialized"}
    except Exception as e:
        logger.error(f"Get status failed: {e}")
        return {"error": str(e)}

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
                        logger.debug(f"Streamed message: {message.get('id')}")
            
            await asyncio.sleep(0.5)
            
    except Exception as e:
        logger.error(f"Message stream generator error: {e}")
        raise

@app.get("/stream")
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

class ROIModel(BaseModel):
    """ROI配置模型"""
    left: int
    top: int
    right: int
    bottom: int

@app.get("/api/ui")
async def web_interface():
    """返回Web管理界面"""
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    index_path = os.path.join(static_dir, 'index.html')
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return {"error": "Web interface not found"}

@app.post("/api/roi")
async def update_roi(roi: ROIModel):
    """更新ROI监控区域"""
    try:
        logger.info(f"更新ROI配置: {roi}")
        
        # 更新Producer1的ROI配置
        if producer1:
            producer1.monitor.set_roi(roi.left, roi.top, roi.right, roi.bottom)
        
        return {
            "status": "success",
            "message": "ROI配置已更新",
            "roi": {
                "left": roi.left,
                "top": roi.top,
                "right": roi.right,
                "bottom": roi.bottom
            }
        }
    except Exception as e:
        logger.error(f"更新ROI失败: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/screenshot")
async def screenshot():
    """截取当前屏幕"""
    try:
        if producer1:
            screenshot = producer1.monitor.capture_screen()
            
            # 转换为base64
            _, buffer = cv2.imencode('.png', screenshot)
            img_str = base64.b64encode(buffer).decode()
            
            return HTMLResponse(
                content=f'<img src="data:image/png;base64,{img_str}" style="max-width:100%;">'
            )
        else:
            return {"error": "Producer1未运行"}
    except Exception as e:
        logger.error(f"截屏失败: {e}")
        return {"error": str(e)}

@app.post("/api/restart")
async def restart_service():
    """重启生产者服务"""
    try:
        logger.info("正在重启服务...")
        
        # 停止生产者
        if producer1:
            producer1.stop()
        if producer2:
            producer2.stop()
        
        # 等待停止
        await asyncio.sleep(2)
        
        # 重新启动生产者
        if producer1:
            producer1.start()
        if producer2:
            producer2.start()
        
        logger.info("服务重启成功")
        
        return {
            "status": "success",
            "message": "服务重启成功"
        }
    except Exception as e:
        logger.error(f"重启服务失败: {e}")
        return {"status": "error", "message": str(e)}

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """
    启动FastAPI服务器
    
    输入:
        host: 监听地址
        port: 监听端口
    """
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    start_api_server()
