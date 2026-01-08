"""测试工作流功能"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.workflows import create_workflow
from core.state import AgentState
from core.schemas import RawMessage, MessageType
import structlog

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()


def test_workflow():
    """测试工作流执行"""
    logger.info("开始测试工作流")
    
    # 创建工作流
    workflow = create_workflow()
    logger.info("工作流创建成功")
    
    # 创建测试消息
    test_message = RawMessage(
        sender="test_user",
        content="这是一条测试消息，用于验证工作流功能",
        message_type=MessageType.TEXT,
        group_id="test_group"
    )
    
    # 初始化工作流状态
    initial_state: AgentState = {
        "raw_message": test_message,
        "multimodal_analysis": None,
        "task_status": None,
        "document_updates": [],
        "messages": [],
        "context": {}
    }
    
    logger.info("开始执行工作流", sender=test_message.sender)
    
    try:
        # 执行工作流
        final_state = workflow.invoke(initial_state)
        
        logger.info("工作流执行完成")
        
        # 输出结果
        print("\n" + "="*50)
        print("工作流执行结果:")
        print("="*50)
        print(f"原始消息: {final_state.get('raw_message').content}")
        print(f"多模态分析: {final_state.get('multimodal_analysis')}")
        print(f"任务状态: {final_state.get('task_status')}")
        print(f"文档更新数量: {len(final_state.get('document_updates', []))}")
        print(f"消息记录数量: {len(final_state.get('messages', []))}")
        print("="*50 + "\n")
        
        return True
        
    except Exception as e:
        logger.error("工作流执行失败", error=str(e))
        return False


if __name__ == "__main__":
    success = test_workflow()
    sys.exit(0 if success else 1)
