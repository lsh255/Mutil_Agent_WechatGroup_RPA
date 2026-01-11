import asyncio
from typing import Optional, Dict, Any
import structlog
from docker import DockerClient, from_env
from docker.errors import DockerException, NotFound, APIError
from config import settings

logger = structlog.get_logger()


class SandboxManagerAgent:
    """沙盒容器管理智能体
    
    职责:
        - 管理微信沙盒Docker容器的生命周期（创建、启动、停止、删除）
        - 监控容器健康状态
        - 提供容器状态查询接口
        - 管理容器端口映射和数据卷
        - 支持多用户多容器模式（按user_id区分）
    
    特性:
        - 与AgentConsumer解耦，专注于容器管理
        - 支持多容器并行管理
        - 提供容器健康检查和自动重启
        - 支持容器状态持久化（Redis）
    """
    
    def __init__(self, redis_client=None):
        """初始化沙盒管理智能体
        
        Args:
            redis_client: Redis客户端（可选，用于状态持久化）
        """
        self.docker_client: Optional[DockerClient] = None
        self.redis_client = redis_client
        self.default_container_name = "wechat-sandbox"
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        self._init_docker_client()
    
    def _init_docker_client(self):
        """初始化Docker客户端"""
        try:
            self.docker_client = from_env()
            logger.info("Docker客户端初始化成功")
        except DockerException as e:
            logger.error("Docker客户端初始化失败", error=str(e))
            raise
    
    def _get_container_name(self, user_id: Optional[str] = None) -> str:
        """获取容器名称
        
        Args:
            user_id: 用户ID（可选，用于多容器模式）
        
        Returns:
            容器名称
        """
        if user_id:
            return f"wechat-sandbox-{user_id}"
        return self.default_container_name
    
    def _get_port_mapping(self, user_id: Optional[str] = None) -> Dict[str, int]:
        """获取端口映射配置
        
        Args:
            user_id: 用户ID（可选，用于多容器端口分配）
        
        Returns:
            端口映射字典
        """
        base_novnc = 5800
        base_vnc = 5900
        base_producer = 6789
        
        if user_id:
            user_hash = hash(user_id) % 1000
            return {
                "5800/tcp": base_novnc + user_hash,
                "5900/tcp": base_vnc + user_hash,
                "6789/tcp": base_producer + user_hash
            }
        
        return {
            "5800/tcp": 5800,
            "5900/tcp": 5900,
            "6789/tcp": 6789
        }
    
    async def start_container(
        self,
        user_id: Optional[str] = None,
        recreate: bool = False
    ) -> Dict[str, Any]:
        """启动微信沙盒容器
        
        Args:
            user_id: 用户ID（可选，用于多容器模式）
            recreate: 是否强制重新创建容器
        
        Returns:
            操作结果字典
        """
        container_name = self._get_container_name(user_id)
        result = {
            "success": False,
            "container_name": container_name,
            "message": ""
        }
        
        try:
            if not self.docker_client:
                self._init_docker_client()
            
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": container_name}
            )
            
            if containers:
                container = containers[0]
                
                if recreate:
                    logger.info("删除旧容器并重新创建", container=container_name)
                    container.remove(force=True)
                elif container.status == "running":
                    result["success"] = True
                    result["message"] = "容器已在运行"
                    logger.info("容器已在运行", container=container_name)
                    return result
                else:
                    container.start()
                    result["success"] = True
                    result["message"] = "容器已启动"
                    logger.info("容器已启动", container=container_name)
                    return result
            
            port_mapping = self._get_port_mapping(user_id)
            volume = settings.wechat_sandbox.data_volume
            
            self.docker_client.containers.run(
                image=settings.wechat_sandbox.docker_image,
                name=container_name,
                detach=True,
                ports=port_mapping,
                volumes={
                    volume: {
                        "bind": "/config",
                        "mode": "rw"
                    }
                }
            )
            
            result["success"] = True
            result["message"] = "容器已创建并启动"
            result["ports"] = port_mapping
            logger.info(
                "容器已创建并启动",
                container=container_name,
                ports=port_mapping
            )
            
            if self.redis_client:
                await self._save_container_status(container_name, "running", user_id)
            
            return result
            
        except DockerException as e:
            result["message"] = f"启动容器失败: {str(e)}"
            logger.error("启动容器失败", error=str(e), container=container_name)
            return result
        except Exception as e:
            result["message"] = f"未知错误: {str(e)}"
            logger.error("启动容器异常", error=str(e), container=container_name)
            return result
    
    async def stop_container(
        self,
        user_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """停止微信沙盒容器
        
        Args:
            user_id: 用户ID（可选）
            force: 是否强制停止
        
        Returns:
            操作结果字典
        """
        container_name = self._get_container_name(user_id)
        result = {
            "success": False,
            "container_name": container_name,
            "message": ""
        }
        
        try:
            if not self.docker_client:
                result["message"] = "Docker客户端未初始化"
                return result
            
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": container_name}
            )
            
            if containers:
                container = containers[0]
                
                if force:
                    container.kill()
                    result["message"] = "容器已强制停止"
                else:
                    container.stop()
                    result["message"] = "容器已停止"
                
                result["success"] = True
                logger.info("容器已停止", container=container_name)
                
                if self.redis_client:
                    await self._save_container_status(container_name, "stopped", user_id)
                
                return result
            else:
                result["message"] = "容器不存在"
                return result
                
        except DockerException as e:
            result["message"] = f"停止容器失败: {str(e)}"
            logger.error("停止容器失败", error=str(e), container=container_name)
            return result
    
    async def remove_container(
        self,
        user_id: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """删除微信沙盒容器
        
        Args:
            user_id: 用户ID（可选）
            force: 是否强制删除
        
        Returns:
            操作结果字典
        """
        container_name = self._get_container_name(user_id)
        result = {
            "success": False,
            "container_name": container_name,
            "message": ""
        }
        
        try:
            if not self.docker_client:
                result["message"] = "Docker客户端未初始化"
                return result
            
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": container_name}
            )
            
            if containers:
                container = containers[0]
                container.remove(force=force)
                
                result["success"] = True
                result["message"] = "容器已删除"
                logger.info("容器已删除", container=container_name)
                
                if self.redis_client:
                    await self._save_container_status(container_name, "removed", user_id)
                
                return result
            else:
                result["message"] = "容器不存在"
                return result
                
        except DockerException as e:
            result["message"] = f"删除容器失败: {str(e)}"
            logger.error("删除容器失败", error=str(e), container=container_name)
            return result
    
    async def get_container_status(
        self,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取容器状态
        
        Args:
            user_id: 用户ID（可选）
        
        Returns:
            容器状态字典
        """
        container_name = self._get_container_name(user_id)
        result = {
            "container_name": container_name,
            "status": "not_found",
            "details": {}
        }
        
        try:
            if not self.docker_client:
                return result
            
            container = self.docker_client.containers.get(container_name)
            container.reload()
            
            result["status"] = container.status
            result["details"] = {
                "id": container.id[:12],
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs.get("Created"),
                "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {}),
                "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "healthy")
            }
            
            logger.debug("容器状态查询成功", container=container_name, status=container.status)
            
        except NotFound:
            logger.debug("容器不存在", container=container_name)
        except APIError as e:
            logger.error("查询容器状态失败", error=str(e), container=container_name)
        except Exception as e:
            logger.error("查询容器状态异常", error=str(e), container=container_name)
        
        return result
    
    async def list_all_containers(self) -> list[Dict[str, Any]]:
        """列出所有微信沙盒容器
        
        Returns:
            容器列表
        """
        containers_info = []
        
        try:
            if not self.docker_client:
                return containers_info
            
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": "wechat-sandbox"}
            )
            
            for container in containers:
                container.reload()
                containers_info.append({
                    "name": container.name,
                    "id": container.id[:12],
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {})
                })
            
            logger.info("容器列表查询成功", count=len(containers_info))
            
        except Exception as e:
            logger.error("列出容器失败", error=str(e))
        
        return containers_info
    
    async def _save_container_status(
        self,
        container_name: str,
        status: str,
        user_id: Optional[str] = None
    ):
        """保存容器状态到Redis
        
        Args:
            container_name: 容器名称
            status: 容器状态
            user_id: 用户ID（可选）
        """
        if not self.redis_client:
            return
        
        try:
            key = f"sandbox:container:{container_name}"
            data = {
                "status": status,
                "user_id": user_id,
                "updated_at": asyncio.get_event_loop().time()
            }
            
            self.redis_client.hset(key, mapping=data)
            self.redis_client.expire(key, 86400)
            
            logger.debug("容器状态已保存", container=container_name, status=status)
            
        except Exception as e:
            logger.error("保存容器状态失败", error=str(e), container=container_name)
    
    async def start_health_monitoring(
        self,
        interval: int = 30,
        auto_restart: bool = True
    ):
        """启动容器健康监控
        
        Args:
            interval: 检查间隔（秒）
            auto_restart: 是否自动重启异常容器
        """
        if self.is_monitoring:
            logger.warn("健康监控已在运行")
            return
        
        self.is_monitoring = True
        logger.info("启动容器健康监控", interval=interval, auto_restart=auto_restart)
        
        self._monitor_task = asyncio.create_task(
            self._health_monitor_loop(interval, auto_restart)
        )
    
    async def _health_monitor_loop(
        self,
        interval: int,
        auto_restart: bool
    ):
        """健康监控循环"""
        while self.is_monitoring:
            try:
                containers = await self.list_all_containers()
                
                for container_info in containers:
                    if container_info["status"] == "running":
                        logger.debug(
                            "容器运行正常",
                            name=container_info["name"],
                            id=container_info["id"]
                        )
                    elif auto_restart and container_info["status"] in ["exited", "dead"]:
                        logger.warn(
                            "容器异常，尝试重启",
                            name=container_info["name"],
                            status=container_info["status"]
                        )
                        
                        user_id = container_info["name"].replace("wechat-sandbox-", "")
                        user_id = user_id if user_id != "wechat-sandbox" else None
                        
                        await self.start_container(user_id, recreate=False)
                
            except Exception as e:
                logger.error("健康监控异常", error=str(e))
            
            await asyncio.sleep(interval)
    
    def stop_health_monitoring(self):
        """停止容器健康监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        logger.info("容器健康监控已停止")
