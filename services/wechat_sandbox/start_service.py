"""
双生产者服务启动脚本（FastAPI + Redis + Linux微信）
"""

import sys
import signal
import time
from utils.logger import logger
from producer_service.api_server import start_api_server

class ProducerService:
    """
    双生产者服务
    
    管理生产者1、生产者2和FastAPI服务器
    """
    
    def __init__(self):
        """初始化服务"""
        self.running = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """
        信号处理函数（优雅关闭）
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """启动所有组件"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("Starting Producer Service...")
        
        try:
            # 启动FastAPI服务器（会自动启动生产者1和2）
            self.running = True
            logger.info("Producer Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """停止所有组件"""
        if not self.running:
            return
        
        logger.info("Stopping Producer Service...")
        
        try:
            self.running = False
            logger.info("Producer Service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("WeChat Group Message Producer Service")
    logger.info("=" * 60)
    
    try:
        # 启动FastAPI服务器
        host = "0.0.0.0"
        port = 8000
        logger.info(f"Starting API server on {host}:{port}")
        
        start_api_server(host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
