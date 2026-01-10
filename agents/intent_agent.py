"""
意图识别 Agent 模块
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from .prompts.intent_prompts import (
    INTENT_RECOGNITION_HUMAN_PROMPT,
    INTENT_RECOGNITION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class IntentAgent:
    """
    意图识别 Agent，用于识别用户消息的意图
    """

    def __init__(
        self,
        model_name: str = "qwen3-72b:latest",
        temperature: float = 0.1,
        max_tokens: int = 100,
        confidence_threshold: float = 0.8,
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        初始化意图识别 Agent

        Args:
            model_name: 使用的模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            confidence_threshold: 置信度阈值
            ollama_base_url: Ollama服务地址
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.confidence_threshold = confidence_threshold
        self.ollama_base_url = ollama_base_url

        self._chain = self._build_chain()
        logger.info(f"意图识别 Agent 初始化完成，模型: {model_name}")

    def _build_chain(self) -> Runnable:
        """
        构建意图识别链

        Returns:
            LangChain Runnable对象
        """
        llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            num_predict=self.max_tokens,
            base_url=self.ollama_base_url,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", INTENT_RECOGNITION_SYSTEM_PROMPT),
                ("human", INTENT_RECOGNITION_HUMAN_PROMPT),
            ]
        )

        json_parser = JsonOutputParser()

        chain = prompt | llm | json_parser
        return chain

    def invoke(
        self, user_message: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行意图识别

        Args:
            user_message: 用户消息
            config: 可选配置参数

        Returns:
            意图识别结果字典
        """
        try:
            logger.debug(f"开始识别意图，用户消息: {user_message[:50]}...")

            result = self._chain.invoke(
                {"user_message": user_message}, config=config or {}
            )

            logger.info(
                f"意图识别完成，结果: intent={result.get('intent')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.error(f"意图识别失败: {e}", exc_info=True)
            return {
                "intent": "other",
                "confidence": 0.0,
                "extracted_data": {},
                "error": str(e),
            }

    async def ainvoke(
        self, user_message: str, config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        异步执行意图识别

        Args:
            user_message: 用户消息
            config: 可选配置参数

        Returns:
            意图识别结果字典
        """
        try:
            logger.debug(f"开始异步识别意图，用户消息: {user_message[:50]}...")

            result = await self._chain.ainvoke(
                {"user_message": user_message}, config=config or {}
            )

            logger.info(
                f"异步意图识别完成，结果: intent={result.get('intent')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.error(f"异步意图识别失败: {e}", exc_info=True)
            return {
                "intent": "other",
                "confidence": 0.0,
                "extracted_data": {},
                "error": str(e),
            }

    def validate_intent(
        self, intent_result: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        验证意图识别结果

        Args:
            intent_result: 意图识别结果

        Returns:
            (是否有效, 错误信息)
        """
        if not intent_result:
            return False, "意图识别结果为空"

        intent = intent_result.get("intent")
        confidence = intent_result.get("confidence", 0.0)

        if intent not in ["task_config", "monitor_group", "other"]:
            return False, f"无效的意图类型: {intent}"

        if confidence < self.confidence_threshold:
            return False, f"置信度过低: {confidence} < {self.confidence_threshold}"

        return True, None


def create_intent_agent(
    model_name: str = "qwen3-72b:latest",
    temperature: float = 0.1,
    max_tokens: int = 100,
    confidence_threshold: float = 0.8,
    ollama_base_url: str = "http://localhost:11434",
) -> IntentAgent:
    """
    工厂函数：创建意图识别 Agent

    Args:
        model_name: 使用的模型名称
        temperature: 温度参数
        max_tokens: 最大生成token数
        confidence_threshold: 置信度阈值
        ollama_base_url: Ollama服务地址

    Returns:
        IntentAgent 实例
    """
    return IntentAgent(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        confidence_threshold=confidence_threshold,
        ollama_base_url=ollama_base_url,
    )
