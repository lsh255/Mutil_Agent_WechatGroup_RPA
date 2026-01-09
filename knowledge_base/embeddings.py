from langchain_openai import OpenAIEmbeddings
from ...config import settings


class EmbeddingManager:
    """嵌入模型管理器：负责文本向量化"""
    
    def __init__(self):
        """初始化嵌入模型管理器"""
        self.embeddings = OpenAIEmbeddings(
            model=settings.ai.siliconflow.embedding_model,
            openai_api_key=settings.ai.siliconflow.api_key,
            openai_api_base=settings.ai.siliconflow.base_url
        )
    
    def embed_text(self, text: str) -> list[float]:
        """将文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            print(f"文本嵌入失败: {e}")
            return []
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量将文本转换为向量
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量列表的列表
        """
        try:
            return self.embeddings.embed_documents(texts)
        except Exception as e:
            print(f"批量文本嵌入失败: {e}")
            return []
