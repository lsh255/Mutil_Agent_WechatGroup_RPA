"""启动所有服务的脚本"""
import asyncio
import subprocess
import sys
from pathlib import Path
import structlog

# 配置结构化日志
logger = structlog.get_logger()


async def start_orchestrator():
    """启动协调中心服务"""
    logger.info("启动协调中心服务")
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "uvicorn",
            "services.orchestrator.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        )
        return process
    except Exception as e:
        logger.error("启动协调中心失败", error=str(e))
        return None


async def start_monitor_agent():
    """启动监控Agent"""
    logger.info("启动监控Agent")
    try:
        # 这里需要实现监控Agent的启动逻辑
        # 目前只是示例
        await asyncio.sleep(1)
        logger.info("监控Agent已启动（模拟）")
        return None
    except Exception as e:
        logger.error("启动监控Agent失败", error=str(e))
        return None


async def main():
    """主函数"""
    logger.info("启动所有服务")
    
    # 启动协调中心
    orchestrator_process = await start_orchestrator()
    
    # 启动监控Agent
    monitor_agent = await start_monitor_agent()
    
    logger.info("所有服务已启动，按Ctrl+C停止")
    
    try:
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        # 清理资源
        if orchestrator_process:
            orchestrator_process.terminate()
            logger.info("协调中心已停止")
        
        logger.info("所有服务已停止")


if __name__ == "__main__":
    asyncio.run(main())
