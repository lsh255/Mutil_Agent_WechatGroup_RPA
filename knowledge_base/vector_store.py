from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
from typing import List, Optional
from pathlib import Path
from ...config import settings


class VectorStoreManager:
    """向量存储管理器：负责向量数据库的CRUD操作"""
    
    def __init__(self):
        """初始化向量存储管理器"""
        self.embeddings = OllamaEmbeddings(
            model=settings.ai.ollama.embedding_model,
            base_url=settings.ai.ollama.base_url
        )
        
        # 确保持久化目录存在
        persist_dir = Path(settings.vector_store.persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化向量存储
        self.vector_store = Chroma(
            persist_directory=str(persist_dir),
            embedding_function=self.embeddings,
            collection_name=settings.vector_store.collection_name
        )
    
    def add_documents(self, documents: List[Document]) -> bool:
        """添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            是否添加成功
        """
        try:
            self.vector_store.add_documents(documents)
            return True
        except Exception as e:
            print(f"添加文档失败: {e}")
            return False
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> bool:
        """添加文本到向量存储
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            
        Returns:
            是否添加成功
        """
        try:
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            return True
        except Exception as e:
            print(f"添加文本失败: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            文档列表
        """
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"相似度搜索失败: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple[Document, float]]:
        """带分数的相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            (文档, 分数)元组列表
        """
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            print(f"带分数的相似度搜索失败: {e}")
            return []
    
    def delete_collection(self) -> bool:
        """删除整个集合
        
        Returns:
            是否删除成功
        """
        try:
            self.vector_store.delete_collection()
            return True
        except Exception as e:
            print(f"删除集合失败: {e}")
            return False
    
    def get_collection_count(self) -> int:
        """获取集合中文档数量
        
        Returns:
            文档数量
        """
        try:
            return self.vector_store._collection.count()
        except Exception as e:
            print(f"获取集合数量失败: {e}")
            return 0
