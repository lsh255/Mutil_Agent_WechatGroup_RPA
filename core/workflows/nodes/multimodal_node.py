from typing import Dict, Any, Optional
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from ...state import AgentState
from ...schemas import MultimodalAnalysis, TaskType, TaskPhase
from ...config import settings


class MultimodalNode:
    """多模态分析节点：调用AI模型进行消息理解和分类"""
    
    def __init__(self):
        """初始化多模态节点"""
        self.vision_model = ChatOllama(
            model=settings.ai.ollama.vision_model,
            base_url=settings.ai.ollama.base_url
        )
        self.embeddings = OllamaEmbeddings(
            model=settings.ai.ollama.embedding_model,
            base_url=settings.ai.ollama.base_url
        )
        self.vector_store = Chroma(
            persist_directory=settings.vector_store.persist_directory,
            embedding_function=self.embeddings,
            collection_name=settings.vector_store.collection_name
        )
    
    def _retrieve_rag_context(self, query: str, k: int = 3) -> list:
        """从向量数据库检索相关上下文"""
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"RAG检索失败: {e}")
            return []
    
    def _analyze_with_vision_model(
        self, 
        content: str, 
        image_path: Optional[str] = None,
        rag_context: Optional[list] = None
    ) -> MultimodalAnalysis:
        """使用视觉语言模型分析消息"""
        # 构建提示词
        rag_context_str = "\n".join(rag_context) if rag_context else ""
        prompt = f"""
        请分析以下微信消息，提取关键信息：
        
        消息内容: {content}
        
        相关业务上下文:
        {rag_context_str}
        
        请返回JSON格式的分析结果，包含：
        - task_type: 任务类型（work_report/task_assignment/status_update/other）
        - task_phase: 任务阶段（before/during/after/unknown）
        - user: 用户名
        - content_summary: 内容摘要
        - extracted_info: 提取的关键信息字典
        - confidence: 置信度（0-1）
        """
        
        # 调用模型（这里简化处理，实际需要根据模型API调整）
        # response = self.vision_model.invoke(prompt)
        # analysis_data = json.loads(response.content)
        
        # 临时返回模拟数据
        return MultimodalAnalysis(
            task_type=TaskType.OTHER,
            task_phase=TaskPhase.UNKNOWN,
            user="unknown",
            content_summary=content[:100],
            extracted_info={},
            confidence=0.8,
            rag_context=rag_context
        )
    
    def analyze(self, state: AgentState) -> Dict[str, Any]:
        """分析消息并生成多模态分析结果"""
        raw_message = state.get("raw_message")
        
        if not raw_message:
            return {
                "messages": [("system", "无消息可分析")]
            }
        
        # 执行RAG检索
        rag_context = self._retrieve_rag_context(raw_message.content)
        
        # 调用视觉模型分析
        analysis = self._analyze_with_vision_model(
            content=raw_message.content,
            image_path=raw_message.image_path,
            rag_context=rag_context
        )
        
        return {
            "multimodal_analysis": analysis,
            "messages": [("system", f"多模态分析完成: {analysis.task_type}")]
        }


multimodal_node = MultimodalNode()
