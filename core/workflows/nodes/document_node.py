from typing import Dict, Any
from ...state import AgentState
from ...schemas import DocumentUpdate
from ...config import settings


class DocumentNode:
    """文档执行节点：调用工具更新Excel和生成报告"""
    
    def __init__(self):
        """初始化文档节点"""
        # 这里可以导入具体的工具类
        # from ...tools.excel_tool import UpdateExcelTool
        # from ...tools.word_tool import GenerateReportTool
        pass
    
    def _prepare_document_updates(self, state: AgentState) -> list[DocumentUpdate]:
        """准备文档更新指令"""
        updates = []
        task_status = state.get("task_status")
        multimodal_analysis = state.get("multimodal_analysis")
        
        if not task_status or not multimodal_analysis:
            return updates
        
        # 准备Excel更新指令
        excel_update = DocumentUpdate(
            update_type="excel_update",
            target_file=settings.tools.excel_template_path,
            data={
                "user": task_status.user,
                "task_id": task_status.task_id,
                "phase": task_status.current_phase,
                "completed": task_status.is_completed,
                "summary": multimodal_analysis.content_summary,
                "extracted_info": multimodal_analysis.extracted_info
            }
        )
        updates.append(excel_update)
        
        # 如果任务完成，准备报告生成指令
        if task_status.is_completed:
            report_update = DocumentUpdate(
                update_type="report_generate",
                target_file=f"{settings.tools.output_dir}/report_{task_status.task_id}.docx",
                data={
                    "user": task_status.user,
                    "task_id": task_status.task_id,
                    "summary": multimodal_analysis.content_summary,
                    "extracted_info": multimodal_analysis.extracted_info
                },
                template_path=settings.tools.report_template_path
            )
            updates.append(report_update)
        
        return updates
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """执行文档更新操作"""
        # 准备更新指令
        document_updates = self._prepare_document_updates(state)
        
        if not document_updates:
            return {
                "messages": [("system", "无需执行文档更新")]
            }
        
        # 执行更新（这里简化处理，实际需要调用工具）
        executed_updates = []
        for update in document_updates:
            # 模拟执行
            executed_updates.append(update)
            print(f"执行文档更新: {update.update_type} -> {update.target_file}")
        
        return {
            "document_updates": executed_updates,
            "messages": [("system", f"已执行 {len(executed_updates)} 个文档更新操作")]
        }


document_node = DocumentNode()
