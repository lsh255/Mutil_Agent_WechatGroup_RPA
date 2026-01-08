from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import structlog
from ...core.workflows import create_workflow
from ...core.state import AgentState
from ...core.schemas import RawMessage, MessageType

# 配置结构化日志
logger = structlog.get_logger()

# 创建FastAPI应用
app = FastAPI(
    title="微信工作流Agent协调中心",
    description="基于LangGraph的多模态Agent自动化系统",
    version="0.1.0"
)

# 初始化工作流
workflow = create_workflow()


class WorkflowTriggerRequest(BaseModel):
    """工作流触发请求模型"""
    sender: str
    content: str
    message_type: MessageType
    image_path: Optional[str] = None
    group_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    success: bool
    message: str
    state: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "微信工作流Agent协调中心",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "workflow_loaded": workflow is not None
    }


@app.post("/workflow/trigger", response_model=WorkflowResponse)
async def trigger_workflow(request: WorkflowTriggerRequest):
    """触发工作流执行
    
    Args:
        request: 工作流触发请求
        
    Returns:
        工作流执行结果
    """
    try:
        # 构建原始消息
        raw_message = RawMessage(
            sender=request.sender,
            content=request.content,
            message_type=request.message_type,
            image_path=request.image_path,
            group_id=request.group_id,
            metadata=request.metadata
        )
        
        # 初始化工作流状态
        initial_state: AgentState = {
            "raw_message": raw_message,
            "multimodal_analysis": None,
            "task_status": None,
            "document_updates": [],
            "messages": [],
            "context": {}
        }
        
        # 执行工作流
        logger.info("触发工作流", sender=request.sender, content=request.content[:50])
        final_state = workflow.invoke(initial_state)
        
        # 返回结果
        return WorkflowResponse(
            success=True,
            message="工作流执行成功",
            state={
                "task_status": final_state.get("task_status"),
                "document_updates_count": len(final_state.get("document_updates", [])),
                "messages_count": len(final_state.get("messages", []))
            }
        )
        
    except Exception as e:
        logger.error("工作流执行失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"工作流执行失败: {str(e)}")


@app.get("/workflow/status")
async def get_workflow_status():
    """获取工作流状态"""
    return {
        "status": "ready",
        "nodes": ["monitor", "multimodal", "state_tracker", "document"]
    }


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
