"""初始化知识库脚本"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from knowledge_base import VectorStoreManager
from langchain.schema import Document
import structlog

# 配置结构化日志
logger = structlog.get_logger()


def load_sample_documents() -> list[Document]:
    """加载示例文档
    
    Returns:
        文档列表
    """
    sample_docs = [
        Document(
            page_content="作业前需要检查设备状态，确保所有安全装置正常工作",
            metadata={"category": "safety", "phase": "before"}
        ),
        Document(
            page_content="作业中需要实时监控设备运行参数，记录异常情况",
            metadata={"category": "monitoring", "phase": "during"}
        ),
        Document(
            page_content="作业后需要清理现场，填写作业记录表，关闭设备电源",
            metadata={"category": "cleanup", "phase": "after"}
        ),
        Document(
            page_content="每日工作汇报应包含：完成的工作、遇到的问题、明日计划",
            metadata={"category": "report", "phase": "after"}
        ),
        Document(
            page_content="任务分配时需要明确：任务目标、截止时间、负责人",
            metadata={"category": "assignment", "phase": "before"}
        ),
    ]
    return sample_docs


def main():
    """主函数"""
    logger.info("开始初始化知识库")
    
    # 创建向量存储管理器
    vector_store = VectorStoreManager()
    
    # 加载示例文档
    documents = load_sample_documents()
    logger.info(f"加载了 {len(documents)} 个示例文档")
    
    # 添加文档到向量存储
    success = vector_store.add_documents(documents)
    
    if success:
        logger.info("知识库初始化成功")
        
        # 验证文档数量
        count = vector_store.get_collection_count()
        logger.info(f"当前知识库文档数量: {count}")
        
        # 测试搜索
        test_query = "作业前需要做什么"
        results = vector_store.similarity_search(test_query, k=2)
        logger.info(f"测试搜索 '{test_query}' 返回 {len(results)} 个结果")
        
    else:
        logger.error("知识库初始化失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
