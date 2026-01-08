from typing import Dict, Any, Literal
from ...state import AgentState
from ...schemas import TaskStatus, TaskPhase


class StateTrackerNode:
    """状态跟踪节点：维护任务状态并决定工作流走向"""
    
    def __init__(self):
        """初始化状态跟踪器"""
        # 这里可以连接Redis或其他持久化存储来维护状态
        self.task_states: Dict[str, TaskStatus] = {}
    
    def _get_task_key(self, user: str, task_id: str) -> str:
        """生成任务唯一标识"""
        return f"{user}:{task_id}"
    
    def _update_task_status(
        self, 
        user: str, 
        task_id: str, 
        current_phase: TaskPhase
    ) -> TaskStatus:
        """更新任务状态"""
        task_key = self._get_task_key(user, task_id)
        
        # 检查是否已有状态记录
        if task_key in self.task_states:
            existing_status = self.task_states[task_key]
            # 状态转换逻辑
            if existing_status.current_phase == TaskPhase.BEFORE and current_phase == TaskPhase.DURING:
                existing_status.current_phase = TaskPhase.DURING
            elif existing_status.current_phase == TaskPhase.DURING and current_phase == TaskPhase.AFTER:
                existing_status.current_phase = TaskPhase.AFTER
                existing_status.is_completed = True
            return existing_status
        else:
            # 创建新任务状态
            new_status = TaskStatus(
                user=user,
                task_id=task_id,
                current_phase=current_phase,
                is_completed=(current_phase == TaskPhase.AFTER)
            )
            self.task_states[task_key] = new_status
            return new_status
    
    def update(self, state: AgentState) -> Dict[str, Any]:
        """更新任务状态"""
        multimodal_analysis = state.get("multimodal_analysis")
        
        if not multimodal_analysis:
            return {
                "messages": [("system", "无多模态分析结果")]
            }
        
        # 生成任务ID（简化处理，实际应根据业务逻辑生成）
        task_id = f"task_{multimodal_analysis.user}_{int(multimodal_analysis.confidence * 100)}"
        
        # 更新任务状态
        task_status = self._update_task_status(
            user=multimodal_analysis.user,
            task_id=task_id,
            current_phase=multimodal_analysis.task_phase
        )
        
        return {
            "task_status": task_status,
            "messages": [("system", f"任务状态更新: {task_status.current_phase}, 完成: {task_status.is_completed}")]
        }
    
    @staticmethod
    def should_generate_document(state: AgentState) -> Literal["yes", "no"]:
        """判断是否应该生成文档"""
        task_status = state.get("task_status")
        
        if not task_status:
            return "no"
        
        # 如果任务完成，则生成文档
        if task_status.is_completed:
            return "yes"
        
        return "no"


state_tracker_node = StateTrackerNode()
