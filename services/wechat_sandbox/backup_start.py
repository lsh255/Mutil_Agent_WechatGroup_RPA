"""
备用启动脚本

当 main.py 出现问题时可以使用此脚本启动服务
此脚本专注于启动 FastAPI 服务器，不处理微信和 VNC
"""

import sys
import signal
import uvicorn
from api import app
from utils.logger import logger

def signal_handler(signum, frame):
    """
    信号处理函数
    """
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """
    主函数
    """
    logger.info("=" * 60)
    logger.info("WeChat Sandbox API - Backup Start Script")
    logger.info("=" * 60)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        host = "0.0.0.0"
        port = 8000
        
        logger.info(f"Starting FastAPI server on {host}:{port}")
        logger.info("API Documentation: http://localhost:8000/docs")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
