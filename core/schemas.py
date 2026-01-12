from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    MIXED = "mixed"
    PHOTO = "photo"  # 微信Photo消息类型（需要点击打开查看高清图）


class TaskType(str, Enum):
    """任务类型枚举"""
    WORK_REPORT = "work_report"
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    OTHER = "other"


class TaskPhase(str, Enum):
    """任务阶段枚举"""
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"
    UNKNOWN = "unknown"


class RawMessage(BaseModel):
    """原始消息模型"""
    msg_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    sender: str
    content: str
    message_type: MessageType
    image_path: Optional[str] = None  # 缩略图路径（普通图片）或预览图路径（photo消息）
    high_res_image_path: Optional[str] = None  # 高清图片路径（仅photo消息使用）
    group_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultimodalAnalysis(BaseModel):
    """多模态分析结果模型"""
    task_type: TaskType
    task_phase: TaskPhase
    user: str
    content_summary: str
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    rag_context: Optional[List[str]] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    user: str
    task_id: str
    current_phase: TaskPhase
    is_completed: bool = False
    last_updated: float = Field(default_factory=lambda: datetime.now().timestamp())
    context: Dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """文档更新指令模型"""
    update_type: str  # "excel_update" 或 "report_generate"
    target_file: str
    data: Dict[str, Any]
    template_path: Optional[str] = None
