import os  # 操作系统接口模块
import subprocess  # 子进程管理模块
import asyncio  # 异步 I/O 模块
from api import app  # 导入 FastAPI 应用实例
from utils.config import config  # 配置模块
from utils.logger import logger  # 日志记录模块
import uvicorn  # ASGI 服务器

async def start_wechat():  # 启动微信进程的异步函数
    try:  # 尝试启动微信
        logger.info("Starting WeChat...")  # 记录启动日志
        wechat_process = await asyncio.create_subprocess_exec(  # 创建微信子进程
            "/opt/wechat/wechat",  # 微信可执行文件路径
            stdout=asyncio.subprocess.PIPE,  # 标准输出管道
            stderr=asyncio.subprocess.PIPE  # 标准错误管道
        )
        logger.info("WeChat started successfully")  # 记录启动成功日志
        return wechat_process  # 返回微信进程对象
    except Exception as e:  # 捕获异常
        logger.error(f"Failed to start WeChat: {e}")  # 记录错误日志
        return None  # 返回 None 表示启动失败

async def start_vnc():  # 启动 VNC 服务器的异步函数
    try:  # 尝试启动 VNC
        vnc_password = os.getenv("VNC_PASSWORD", "wechat123")  # 从环境变量获取 VNC 密码，默认为 wechat123
        logger.info("Starting VNC server...")  # 记录启动日志
        subprocess.run(["x11vnc", "-display", ":99", "-forever", "-shared", "-rfbport", "5900", "-passwd", vnc_password], check=True)  # 启动 x11vnc 服务器
    except Exception as e:  # 捕获异常
        logger.error(f"Failed to start VNC: {e}")  # 记录错误日志

async def start_fastapi():  # 启动 FastAPI 服务器的异步函数
    try:  # 尝试启动 FastAPI
        logger.info("Starting FastAPI server...")  # 记录启动日志
        config = uvicorn.Config(  # 配置 uvicorn 服务器
            app,  # FastAPI 应用实例
            host="0.0.0.0",  # 监听所有网络接口
            port=8000,  # 监听端口 8000
            log_level="info"  # 日志级别为 info
        )
        server = uvicorn.Server(config)  # 创建服务器实例
        await server.serve()  # 启动服务器
    except Exception as e:  # 捕获异常
        logger.error(f"Failed to start FastAPI: {e}")  # 记录错误日志

async def main():  # 主异步函数
    wechat_process = None  # 初始化微信进程变量
    try:  # 尝试启动所有服务
        wechat_process = await start_wechat()  # 启动微信进程
        
        vnc_task = asyncio.create_task(start_vnc())  # 创建 VNC 启动任务
        fastapi_task = asyncio.create_task(start_fastapi())  # 创建 FastAPI 启动任务
        
        await fastapi_task  # 等待 FastAPI 任务完成（主线程阻塞）
        
    except KeyboardInterrupt:  # 捕获键盘中断
        logger.info("Shutting down...")  # 记录关闭日志
    except Exception as e:  # 捕获其他异常
        logger.error(f"Error: {e}")  # 记录错误日志
    finally:  # 清理资源
        if wechat_process:  # 如果微信进程存在
            wechat_process.terminate()  # 终止微信进程
            await wechat_process.wait()  # 等待微信进程结束

if __name__ == "__main__":  # 当作为主程序运行时
    asyncio.run(main())  # 运行主异步函数
