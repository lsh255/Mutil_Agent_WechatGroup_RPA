"""
视觉定位 Agent 模块
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from .prompts.visual_prompts import (
    VISUAL_LOCATOR_HUMAN_PROMPT,
    VISUAL_LOCATOR_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class VisualAgent:
    """
    视觉定位 Agent，用于识别微信界面中的关键区域
    """

    def __init__(
        self,
        model_name: str = "qwen3-vl-8b:latest",
        temperature: float = 0.1,
        max_tokens: int = 200,
        confidence_threshold: float = 0.7,
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        初始化视觉定位 Agent

        Args:
            model_name: 使用的视觉模型名称
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

        self._llm = self._build_llm()
        logger.info(f"视觉定位 Agent 初始化完成，模型: {model_name}")

    def _build_llm(self) -> ChatOllama:
        """
        构建LLM

        Returns:
            ChatOllama实例
        """
        llm = ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            num_predict=self.max_tokens,
            base_url=self.ollama_base_url,
        )
        return llm

    def _encode_image(self, image_path: str) -> str:
        """
        将图片编码为base64字符串

        Args:
            image_path: 图片路径

        Returns:
            base64编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def invoke(
        self,
        screenshot_path: str,
        target_group_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行视觉定位

        Args:
            screenshot_path: 截图文件路径
            target_group_name: 目标群聊名称（可选）
            config: 可选配置参数

        Returns:
            视觉定位结果字典
        """
        try:
            logger.debug(
                f"开始视觉定位，截图: {screenshot_path}, "
                f"目标群聊: {target_group_name}"
            )

            if not Path(screenshot_path).exists():
                raise FileNotFoundError(f"截图文件不存在: {screenshot_path}")

            image_base64 = self._encode_image(screenshot_path)

            human_message = VISUAL_LOCATOR_HUMAN_PROMPT.format(
                target_group_name=target_group_name or "未指定"
            )

            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": human_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                    ]
                )
            ]

            response = self._llm.invoke(messages, config=config or {})

            json_parser = JsonOutputParser()
            result = json_parser.parse(response.content)

            logger.info(
                f"视觉定位完成，结果: group_name={result.get('detected_group_name')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.error(f"视觉定位失败: {e}", exc_info=True)
            return {
                "group_name_region": None,
                "message_receive_region": None,
                "message_send_region": None,
                "detected_group_name": None,
                "confidence": 0.0,
                "error": str(e),
            }

    async def ainvoke(
        self,
        screenshot_path: str,
        target_group_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        异步执行视觉定位

        Args:
            screenshot_path: 截图文件路径
            target_group_name: 目标群聊名称（可选）
            config: 可选配置参数

        Returns:
            视觉定位结果字典
        """
        try:
            logger.debug(
                f"开始异步视觉定位，截图: {screenshot_path}, "
                f"目标群聊: {target_group_name}"
            )

            if not Path(screenshot_path).exists():
                raise FileNotFoundError(f"截图文件不存在: {screenshot_path}")

            image_base64 = self._encode_image(screenshot_path)

            human_message = VISUAL_LOCATOR_HUMAN_PROMPT.format(
                target_group_name=target_group_name or "未指定"
            )

            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": human_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                    ]
                )
            ]

            response = await self._llm.ainvoke(messages, config=config or {})

            json_parser = JsonOutputParser()
            result = json_parser.parse(response.content)

            logger.info(
                f"异步视觉定位完成，结果: group_name={result.get('detected_group_name')}, "
                f"confidence={result.get('confidence')}"
            )

            return result

        except Exception as e:
            logger.error(f"异步视觉定位失败: {e}", exc_info=True)
            return {
                "group_name_region": None,
                "message_receive_region": None,
                "message_send_region": None,
                "detected_group_name": None,
                "confidence": 0.0,
                "error": str(e),
            }

    def validate_region(
        self, region: Optional[Dict[str, Any]], region_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        验证区域定位结果

        Args:
            region: 区域定位结果
            region_name: 区域名称

        Returns:
            (是否有效, 错误信息)
        """
        if not region:
            return False, f"{region_name}区域为空"

        required_keys = ["x", "y", "width", "height"]
        for key in required_keys:
            if key not in region:
                return False, f"{region_name}区域缺少字段: {key}"

        if not all(isinstance(v, int) for v in region.values()):
            return False, f"{region_name}区域坐标必须为整数"

        if region["x"] < 0 or region["y"] < 0:
            return False, f"{region_name}区域坐标不能为负数"

        if region["width"] <= 0 or region["height"] <= 0:
            return False, f"{region_name}区域尺寸必须为正数"

        return True, None


def create_visual_agent(
    model_name: str = "qwen3-vl-8b:latest",
    temperature: float = 0.1,
    max_tokens: int = 200,
    confidence_threshold: float = 0.7,
    ollama_base_url: str = "http://localhost:11434",
) -> VisualAgent:
    """
    工厂函数：创建视觉定位 Agent

    Args:
        model_name: 使用的视觉模型名称
        temperature: 温度参数
        max_tokens: 最大生成token数
        confidence_threshold: 置信度阈值
        ollama_base_url: Ollama服务地址

    Returns:
        VisualAgent 实例
    """
    return VisualAgent(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        confidence_threshold=confidence_threshold,
        ollama_base_url=ollama_base_url,
    )
