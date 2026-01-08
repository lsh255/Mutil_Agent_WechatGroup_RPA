import asyncio
import httpx
from typing import Optional, Callable
import structlog
from docker import DockerClient, from_env
from docker.errors import DockerException
from ...config import settings

# 配置结构化日志
logger = structlog.get_logger()


class MonitorAgent:
    """监控Agent：管理微信沙盒容器并触发工作流"""
    
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        """初始化监控Agent
        
        Args:
            orchestrator_url: 协调中心URL
        """
        self.orchestrator_url = orchestrator_url
        self.docker_client: Optional[DockerClient] = None
        self.container_name = "wechat-sandbox"
        self.is_running = False
        self.message_callback: Optional[Callable] = None
    
    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            self.docker_client = from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error("Docker客户端初始化失败", error=str(e))
            raise
    
    def start_container(self) -> bool:
        """启动微信沙盒容器
        
        Returns:
            是否启动成功
        """
        try:
            if not self.docker_client:
                self._init_docker_client()
            
            # 检查容器是否已存在
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": self.container_name}
            )
            
            if containers:
                container = containers[0]
                if container.status != "running":
                    container.start()
                    logger.info("容器已启动", container=self.container_name)
                else:
                    logger.info("容器已在运行", container=self.container_name)
            else:
                # 创建并启动新容器
                self.docker_client.containers.run(
                    image=settings.wechat_sandbox.docker_image,
                    name=self.container_name,
                    detach=True,
                    ports={
                        "5800/tcp": 5800,  # noVNC
                        "5900/tcp": 5900,  # VNC
                        "6789/tcp": 6789   # 生产者服务
                    },
                    volumes={
                        settings.wechat_sandbox.data_volume: {
                            "bind": "/config",
                            "mode": "rw"
                        }
                    }
                )
                logger.info("容器已创建并启动", container=self.container_name)
            
            return True
            
        except DockerException as e:
            logger.error("启动容器失败", error=str(e))
            return False
    
    def stop_container(self) -> bool:
        """停止微信沙盒容器
        
        Returns:
            是否停止成功
        """
        try:
            if not self.docker_client:
                return False
            
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": self.container_name}
            )
            
            if containers:
                container = containers[0]
                container.stop()
                logger.info("容器已停止", container=self.container_name)
                return True
            
            return False
            
        except DockerException as e:
            logger.error("停止容器失败", error=str(e))
            return False
    
    async def _consume_message_stream(self):
        """消费微信消息流"""
        stream_url = f"{settings.wechat_sandbox.producer_service_url}/stream"
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream("GET", stream_url, timeout=None) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # 移除 "data: " 前缀
                                await self._process_message(data)
                    else:
                        logger.error("连接消息流失败", status_code=response.status_code)
                        
            except Exception as e:
                logger.error("消费消息流异常", error=str(e))
    
    async def _process_message(self, message_data: str):
        """处理接收到的消息
        
        Args:
            message_data: 消息数据（JSON字符串）
        """
        try:
            import json
            message = json.loads(message_data)
            
            logger.info("收到消息", sender=message.get("sender"), content=message.get("content")[:50])
            
            # 触发工作流
            await self._trigger_workflow(message)
            
            # 调用回调函数（如果设置）
            if self.message_callback:
                await self.message_callback(message)
                
        except Exception as e:
            logger.error("处理消息失败", error=str(e))
    
    async def _trigger_workflow(self, message: dict):
        """触发工作流执行
        
        Args:
            message: 消息数据
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/workflow/trigger",
                    json=message,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("工作流触发成功")
                else:
                    logger.error("工作流触发失败", status_code=response.status_code)
                    
        except Exception as e:
            logger.error("触发工作流异常", error=str(e))
    
    def set_message_callback(self, callback: Callable):
        """设置消息回调函数
        
        Args:
            callback: 回调函数
        """
        self.message_callback = callback
    
    async def start(self):
        """启动监控Agent"""
        logger.info("启动监控Agent")
        
        # 启动容器
        if not self.start_container():
            logger.error("启动容器失败，无法继续")
            return
        
        self.is_running = True
        
        # 开始消费消息流
        while self.is_running:
            try:
                await self._consume_message_stream()
            except Exception as e:
                logger.error("消息流异常，5秒后重试", error=str(e))
                await asyncio.sleep(5)
    
    def stop(self):
        """停止监控Agent"""
        logger.info("停止监控Agent")
        self.is_running = False
        self.stop_container()
