from typing import Dict, Any
from ...state import AgentState


class MonitorNode:
    """监控节点：接收外部消息并载入工作流状态"""
    
    @staticmethod
    def process(state: AgentState) -> Dict[str, Any]:
        """处理原始消息并载入状态"""
        raw_message = state.get("raw_message")
        
        if not raw_message:
            return {
                "messages": [("system", "未收到原始消息")]
            }
        
        # 记录消息接收日志
        message_log = f"收到消息 - 发送者: {raw_message.sender}, 类型: {raw_message.message_type}"
        
        return {
            "messages": [("system", message_log)]
        }


monitor_node = MonitorNode()
