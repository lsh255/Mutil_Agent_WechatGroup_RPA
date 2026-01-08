from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from typing import Optional


class ProjectConfig(BaseModel):
    """项目基础配置"""
    name: str = "wechat-workflow-agent"
    env: str = "development"


class LangGraphConfig(BaseModel):
    """LangGraph工作流配置"""
    state_store: str = "redis://localhost:6379/0"
    checkpoint_enabled: bool = True


class OllamaConfig(BaseModel):
    """Ollama AI模型服务配置"""
    base_url: str = "http://localhost:11434"
    vision_model: str = "qwen3-vl-8b:latest"
    embedding_model: str = "qwen3-embedding-4b"


class AIConfig(BaseModel):
    """AI相关配置"""
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


class VectorStoreConfig(BaseModel):
    """向量数据库配置"""
    type: str = "chroma"
    persist_directory: str = "./data/chroma_db"
    collection_name: str = "work_knowledge_base"


class WeChatSandboxConfig(BaseModel):
    """微信沙盒配置"""
    docker_image: str = "wechat-sandbox:latest"
    producer_service_url: str = "http://localhost:6789"
    data_volume: str = "./data/wechat_profile"


class ToolsConfig(BaseModel):
    """工具配置"""
    excel_template_path: str = "./templates/task_log.xlsx"
    report_template_path: str = "./templates/daily_report.j2"
    output_dir: str = "./output"


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    lock_db: int = 1


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "json"


class Settings(BaseSettings):
    """全局配置类"""
    model_config = SettingsConfigDict(
        yaml_file="config/settings.yaml",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    langgraph: LangGraphConfig = Field(default_factory=LangGraphConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    wechat_sandbox: WeChatSandboxConfig = Field(default_factory=WeChatSandboxConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


settings = Settings()
