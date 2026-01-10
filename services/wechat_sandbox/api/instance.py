"""
实例管理API路由
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from PIL import ImageGrab
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import logger

router = APIRouter()


@router.get("/screenshot")
async def get_screenshot():
    """获取当前屏幕截图"""
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return StreamingResponse(img_byte_arr, media_type="image/png")
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return {"status": "error", "message": "截图失败"}


@router.post("/restart")
async def restart_service():
    """重启服务（需配合 systemd 或 Docker 实现）"""
    logger.info("收到重启请求")
    return {"status": "success", "message": "重启请求已接收（需配置 systemd 或 Docker 重启策略）"}
