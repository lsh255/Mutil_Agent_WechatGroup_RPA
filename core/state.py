from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from .schemas import RawMessage, MultimodalAnalysis, TaskStatus, DocumentUpdate


class AgentState(TypedDict):
    """LangGraph工作流的状态定义，贯穿整个处理流程"""
    
    # 输入
    raw_message: Optional[RawMessage]  # 来自微信的原始消息
    
    # 处理中间状态
    multimodal_analysis: Optional[MultimodalAnalysis]  # 多模态分析结果
    task_status: Optional[TaskStatus]  # 任务状态
    
    # 输出
    document_updates: List[DocumentUpdate]  # 需要执行的文档更新指令
    
    # 用于串联对话的消息记录
    messages: Annotated[list, add_messages]
    
    # 其他上下文信息
    context: Dict[str, Any]  # 额外的上下文信息
