"""
Agent决策模块
"""

import logging
from typing import Any, Dict, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from .prompts.decision_prompts import (
    AGENT_DECISION_HUMAN_PROMPT,
    AGENT_DECISION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class DecisionAgent:
    """
    Agent决策模块，用于根据消息内容自主决策后续操作
    """

    def __init__(
        self,
        model_name: str = "qwen3-72b:latest",
        temperature: float = 0.3,
        max_tokens: int = 300,
        confidence_threshold: float = 0.7,
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        初始化Agent决策模块

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
        self.supported_actions = ["write_report", "update_ledger", "save_message", "continue"]

        self._chain = self._build_chain()
        logger.info(f"Agent决策模块初始化完成，模型: {model_name}")

    def _build_chain(self) -> Runnable:
        """
        构建Agent决策链

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
                ("system", AGENT_DECISION_SYSTEM_PROMPT),
                ("human", AGENT_DECISION_HUMAN_PROMPT),
            ]
        )

        json_parser = JsonOutputParser()

        chain = prompt | llm | json_parser
        return chain

    def invoke(
        self,
        message_content: str,
        task_name: str,
        location: str,
        personnel: list[str],
        sender: str,
        timestamp: str,
        message_type: str = "text",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行Agent决策

        Args:
            message_content: 消息内容
            task_name: 任务名称
            location: 地点
            personnel: 相关人员列表
            sender: 消息发送者
            timestamp: 消息时间戳
            message_type: 消息类型（text/image/link等）
            config: 可选配置参数

        Returns:
            Agent决策结果字典
        """
        try:
            logger.debug(
                f"开始Agent决策，发送者: {sender}, "
                f"任务: {task_name}, 消息类型: {message_type}"
            )

            result = self._chain.invoke(
                {
                    "message_content": message_content,
                    "task_name": task_name,
                    "location": location,
                    "personnel": ", ".join(personnel) if personnel else "",
                    "sender": sender,
                    "timestamp": timestamp,
                    "message_type": message_type,
                },
                config=config or {},
            )

            logger.info(
                f"Agent决策完成，结果: action={result.get('action')}, "
                f"confidence={result.get('confidence')}, "
                f"reasoning={result.get('reasoning', '')[:50]}..."
            )

            return result

        except Exception as e:
            logger.error(f"Agent决策失败: {e}", exc_info=True)
            return {
                "action": "continue",
                "confidence": 0.0,
                "reasoning": f"决策失败，继续监控: {str(e)}",
                "extracted_data": {},
                "error": str(e),
            }

    async def ainvoke(
        self,
        message_content: str,
        task_name: str,
        location: str,
        personnel: list[str],
        sender: str,
        timestamp: str,
        message_type: str = "text",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        异步执行Agent决策

        Args:
            message_content: 消息内容
            task_name: 任务名称
            location: 地点
            personnel: 相关人员列表
            sender: 消息发送者
            timestamp: 消息时间戳
            message_type: 消息类型（text/image/link等）
            config: 可选配置参数

        Returns:
            Agent决策结果字典
        """
        try:
            logger.debug(
                f"开始异步Agent决策，发送者: {sender}, "
                f"任务: {task_name}, 消息类型: {message_type}"
            )

            result = await self._chain.ainvoke(
                {
                    "message_content": message_content,
                    "task_name": task_name,
                    "location": location,
                    "personnel": ", ".join(personnel) if personnel else "",
                    "sender": sender,
                    "timestamp": timestamp,
                    "message_type": message_type,
                },
                config=config or {},
            )

            logger.info(
                f"异步Agent决策完成，结果: action={result.get('action')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.error(f"异步Agent决策失败: {e}", exc_info=True)
            return {
                "action": "continue",
                "confidence": 0.0,
                "reasoning": f"决策失败，继续监控: {str(e)}",
                "extracted_data": {},
                "error": str(e),
            }

    def validate_decision(
        self, decision_result: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        验证决策结果

        Args:
            decision_result: 决策结果

        Returns:
            (是否有效, 错误信息)
        """
        if not decision_result:
            return False, "决策结果为空"

        action = decision_result.get("action")
        confidence = decision_result.get("confidence", 0.0)

        if action not in self.supported_actions:
            return False, f"无效的操作类型: {action}"

        if confidence < self.confidence_threshold:
            return False, f"置信度过低: {confidence} < {self.confidence_threshold}"

        return True, None

    def should_execute_action(self, decision_result: Dict[str, Any]) -> bool:
        """
        判断是否应该执行操作

        Args:
            decision_result: 决策结果

        Returns:
            是否执行操作
        """
        action = decision_result.get("action")
        confidence = decision_result.get("confidence", 0.0)

        is_valid, _ = self.validate_decision(decision_result)

        if not is_valid:
            return False

        return action != "continue"


def create_decision_agent(
    model_name: str = "qwen3-72b:latest",
    temperature: float = 0.3,
    max_tokens: int = 300,
    confidence_threshold: float = 0.7,
    ollama_base_url: str = "http://localhost:11434",
) -> DecisionAgent:
    """
    工厂函数：创建Agent决策模块

    Args:
        model_name: 使用的模型名称
        temperature: 温度参数
        max_tokens: 最大生成token数
        confidence_threshold: 置信度阈值
        ollama_base_url: Ollama服务地址

    Returns:
        DecisionAgent 实例
    """
    return DecisionAgent(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        confidence_threshold=confidence_threshold,
        ollama_base_url=ollama_base_url,
    )
