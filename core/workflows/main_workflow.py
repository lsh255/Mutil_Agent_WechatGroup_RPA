from langgraph.graph import StateGraph, END
from ..state import AgentState
from .nodes import monitor_node, multimodal_node, state_tracker_node, document_node


def create_workflow():
    """创建并编译主处理工作流"""
    workflow = StateGraph(AgentState)
    
    # 添加节点（对应原Agent的核心功能）
    workflow.add_node("monitor", monitor_node.process)
    workflow.add_node("multimodal", multimodal_node.analyze)
    workflow.add_node("state_tracker", state_tracker_node.update)
    workflow.add_node("document", document_node.execute)
    
    # 设置边（定义流程逻辑）
    workflow.set_entry_point("monitor")
    workflow.add_edge("monitor", "multimodal")
    workflow.add_edge("multimodal", "state_tracker")
    
    # 状态节点决定下一步：若任务完成则生成文档，否则等待
    workflow.add_conditional_edges(
        "state_tracker",
        state_tracker_node.should_generate_document,
        {"yes": "document", "no": END}
    )
    workflow.add_edge("document", END)
    
    return workflow.compile()
