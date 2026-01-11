from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import structlog
import asyncio
from ...agents.sandbox_manager_agent import SandboxManagerAgent

logger = structlog.get_logger()

app = FastAPI(
    title="微信沙盒管理服务",
    description="管理微信沙盒Docker容器的生命周期和状态",
    version="0.1.0"
)

sandbox_manager = SandboxManagerAgent()


class ContainerInfo(BaseModel):
    """容器信息模型"""
    id: str
    name: str
    status: str
    vnc_port: int
    created_at: Optional[str] = None
    last_health_check: Optional[str] = None


class ContainerStatusResponse(BaseModel):
    """容器状态响应"""
    status: str
    container_name: str
    is_running: bool
    health_status: Optional[str] = None
    uptime: Optional[str] = None
    memory_usage: Optional[Dict[str, Any]] = None
    cpu_usage: Optional[float] = None


class ContainerOperationResponse(BaseModel):
    """容器操作响应"""
    success: bool
    message: str
    container_name: str
    operation: str
    details: Optional[Dict[str, Any]] = None


class LogEntry(BaseModel):
    """日志条目模型"""
    timestamp: int
    level: str
    message: str


class ROIConfig(BaseModel):
    """ROI配置模型"""
    left: int
    top: int
    right: int
    bottom: int


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "微信沙盒管理服务",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    docker_available = sandbox_manager.docker_client is not None
    return {
        "status": "healthy",
        "docker_available": docker_available
    }


@app.get("/instances", response_model=List[ContainerInfo])
async def get_instances():
    """获取所有沙盒实例列表"""
    try:
        instances = []
        containers = sandbox_manager.docker_client.containers.list(
            all=True,
            filters={"name": sandbox_manager.default_container_name}
        )
        
        for container in containers:
            status = container.status
            if container.name.startswith("wechat_sandbox_"):
                parts = container.name.split("_")
                if len(parts) >= 3:
                    user_id = parts[2]
                else:
                    user_id = "default"
            else:
                user_id = "default"
            
            vnc_port = 6080
            if container.attrs.get("NetworkSettings"):
                ports = container.attrs["NetworkSettings"].get("Ports", {})
                if "6080/tcp" in ports and ports["6080/tcp"]:
                    vnc_port = int(ports["6080/tcp"][0]["HostPort"])
            
            instances.append({
                "id": container.id[:12],
                "name": container.name,
                "status": status,
                "vnc_port": vnc_port,
                "created_at": container.attrs.get("Created"),
                "last_health_check": None
            })
        
        logger.info("获取沙盒实例列表", count=len(instances))
        return instances
        
    except Exception as e:
        logger.error("获取沙盒实例列表失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取沙盒实例列表失败: {str(e)}")


@app.get("/status/{user_id}", response_model=ContainerStatusResponse)
async def get_container_status(user_id: str = None):
    """获取指定容器状态
    
    Args:
        user_id: 用户ID，用于标识容器
        
    Returns:
        容器状态信息
    """
    try:
        result = await sandbox_manager.get_container_status(user_id)
        return ContainerStatusResponse(
            status=result.get("status", "unknown"),
            container_name=result.get("container_name", ""),
            is_running=result.get("is_running", False),
            health_status=result.get("health_status"),
            uptime=result.get("uptime"),
            memory_usage=result.get("memory_usage"),
            cpu_usage=result.get("cpu_usage")
        )
    except Exception as e:
        logger.error("获取容器状态失败", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"获取容器状态失败: {str(e)}")


@app.post("/start/{user_id}", response_model=ContainerOperationResponse)
async def start_container(user_id: str = None):
    """启动容器
    
    Args:
        user_id: 用户ID，用于标识容器
        
    Returns:
        启动操作结果
    """
    try:
        result = await sandbox_manager.start_container(user_id, recreate=False)
        
        if result.get("success"):
            logger.info("容器启动成功", user_id=user_id, container_name=result.get("container_name"))
            return ContainerOperationResponse(
                success=True,
                message="容器启动成功",
                container_name=result.get("container_name", ""),
                operation="start",
                details=result
            )
        else:
            logger.warn("容器启动失败", user_id=user_id, reason=result.get("error"))
            return ContainerOperationResponse(
                success=False,
                message=result.get("error", "容器启动失败"),
                container_name=result.get("container_name", ""),
                operation="start",
                details=result
            )
            
    except Exception as e:
        logger.error("启动容器失败", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"启动容器失败: {str(e)}")


@app.post("/stop/{user_id}", response_model=ContainerOperationResponse)
async def stop_container(user_id: str = None):
    """停止容器
    
    Args:
        user_id: 用户ID，用于标识容器
        
    Returns:
        停止操作结果
    """
    try:
        result = await sandbox_manager.stop_container(user_id)
        
        if result.get("success"):
            logger.info("容器停止成功", user_id=user_id, container_name=result.get("container_name"))
            return ContainerOperationResponse(
                success=True,
                message="容器停止成功",
                container_name=result.get("container_name", ""),
                operation="stop",
                details=result
            )
        else:
            logger.warn("容器停止失败", user_id=user_id, reason=result.get("error"))
            return ContainerOperationResponse(
                success=False,
                message=result.get("error", "容器停止失败"),
                container_name=result.get("container_name", ""),
                operation="stop",
                details=result
            )
            
    except Exception as e:
        logger.error("停止容器失败", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"停止容器失败: {str(e)}")


@app.post("/restart/{user_id}", response_model=ContainerOperationResponse)
async def restart_container(user_id: str = None):
    """重启容器
    
    Args:
        user_id: 用户ID，用于标识容器
        
    Returns:
        重启操作结果
    """
    try:
        stop_result = await sandbox_manager.stop_container(user_id)
        if not stop_result.get("success"):
            return ContainerOperationResponse(
                success=False,
                message=f"停止容器失败: {stop_result.get('error')}",
                container_name=stop_result.get("container_name", ""),
                operation="restart",
                details=stop_result
            )
        
        await asyncio.sleep(2)
        
        start_result = await sandbox_manager.start_container(user_id, recreate=False)
        
        if start_result.get("success"):
            logger.info("容器重启成功", user_id=user_id, container_name=start_result.get("container_name"))
            return ContainerOperationResponse(
                success=True,
                message="容器重启成功",
                container_name=start_result.get("container_name", ""),
                operation="restart",
                details=start_result
            )
        else:
            logger.warn("容器重启失败", user_id=user_id, reason=start_result.get("error"))
            return ContainerOperationResponse(
                success=False,
                message=start_result.get("error", "容器重启失败"),
                container_name=start_result.get("container_name", ""),
                operation="restart",
                details=start_result
            )
            
    except Exception as e:
        logger.error("重启容器失败", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"重启容器失败: {str(e)}")


@app.get("/logs", response_model=List[LogEntry])
async def get_logs(limit: int = 100):
    """获取沙盒服务日志
    
    Args:
        limit: 返回的日志条数
        
    Returns:
        日志列表
    """
    try:
        logs = []
        if sandbox_manager.docker_client:
            containers = sandbox_manager.docker_client.containers.list(
                all=True,
                filters={"name": sandbox_manager.default_container_name}
            )
            
            for container in containers:
                try:
                    container_logs = container.logs(tail=limit, timestamps=True).decode('utf-8')
                    for line in container_logs.split('\n'):
                        if line.strip():
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                timestamp_str, message = parts[0], parts[1]
                                try:
                                    from datetime import datetime
                                    timestamp = int(datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp())
                                except:
                                    timestamp = int(asyncio.get_event_loop().time())
                                
                                level = 'info'
                                if 'error' in message.lower() or 'failed' in message.lower():
                                    level = 'error'
                                elif 'warn' in message.lower():
                                    level = 'warn'
                                
                                logs.append(LogEntry(
                                    timestamp=timestamp,
                                    level=level,
                                    message=message
                                ))
                except Exception as e:
                    logger.warn("获取容器日志失败", container=container.name, error=str(e))
        
        logs = logs[-limit:] if len(logs) > limit else logs
        logger.info("获取沙盒服务日志", count=len(logs))
        return logs
        
    except Exception as e:
        logger.error("获取日志失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")


@app.post("/roi")
async def update_roi_config(config: ROIConfig):
    """更新监控区域(ROI)配置
    
    Args:
        config: ROI配置
        
    Returns:
        更新结果
    """
    try:
        logger.info("更新ROI配置", config=config.dict())
        
        return {
            "success": True,
            "message": "ROI配置已更新",
            "config": config.dict()
        }
        
    except Exception as e:
        logger.error("更新ROI配置失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"更新ROI配置失败: {str(e)}")


@app.get("/screenshot")
async def capture_screenshot():
    """截取沙盒屏幕
    
    Returns:
        截图图片数据
    """
    try:
        if not sandbox_manager.docker_client:
            raise HTTPException(status_code=503, detail="Docker服务不可用")
        
        container = sandbox_manager.docker_client.containers.get(sandbox_manager.default_container_name)
        if not container or container.status != "running":
            raise HTTPException(status_code=404, detail="容器未运行")
        
        exit_code, output = container.exec_run("import -window root /tmp/screenshot.png")
        
        if exit_code != 0:
            raise HTTPException(status_code=500, detail="截图命令执行失败")
        
        bits, stat = container.get_archive("/tmp/screenshot.png")
        
        from fastapi.responses import StreamingResponse
        import io
        
        def iterfile():
            with io.BytesIO() as f:
                for chunk in bits:
                    f.write(chunk)
                f.seek(0)
                yield from f
        
        logger.info("截图成功")
        return StreamingResponse(iterfile(), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("截图失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"截图失败: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error("未处理的异常", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": f"内部服务器错误: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
