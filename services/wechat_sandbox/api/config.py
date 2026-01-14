"""
配置管理API路由（v2.0）
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 使用标准 logging，避免依赖问题
logger = logging.getLogger(__name__)

router = APIRouter()

CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"


class ROIModel(BaseModel):
    """ROI 模型（用于测试和 API）"""
    left: int = Field(..., ge=0, description="左边界")
    top: int = Field(..., ge=0, description="上边界")
    right: int = Field(..., gt=0, description="右边界")
    bottom: int = Field(..., gt=0, description="下边界")

    @field_validator('right', 'bottom')
    @classmethod
    def validate_positive(cls, v):
        """验证必须为正数"""
        if v <= 0:
            raise ValueError('必须为正数')
        return v

    @field_validator('left', 'top')
    @classmethod
    def validate_non_negative(cls, v):
        """验证不能为负数"""
        if v < 0:
            raise ValueError('不能为负数')
        return v

    @model_validator(mode='after')
    def validate_coordinates(self):
        """验证坐标顺序"""
        if self.left >= self.right:
            raise ValueError('左边界必须小于右边界')
        if self.top >= self.bottom:
            raise ValueError('上边界必须小于下边界')
        return self


class ROIUpdate(BaseModel):
    """ROI更新请求模型"""
    left: int
    top: int
    right: int
    bottom: int
    preset: Optional[str] = None
    active_preset: Optional[str] = None


class ConfigUpdate(BaseModel):
    """配置更新请求模型"""
    config: Dict[str, Any]


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
    return {}


def save_config(config: Dict[str, Any]) -> bool:
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        logger.info(f"配置已保存到 {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False


@router.get("/")
async def get_config():
    """获取完整配置"""
    config = load_config()
    if config:
        return config
    return {"error": "配置文件不存在或为空"}


@router.post("/")
async def update_config(config: Dict[str, Any]):
    """更新完整配置"""
    if not isinstance(config, dict):
        logger.error(f"无效的配置格式: {type(config)}")
        return {"status": "error", "message": "配置必须是字典格式"}
    
    if save_config(config):
        return {"status": "success", "message": "配置已保存"}
    return {"status": "error", "message": "保存配置失败"}


@router.get("/roi")
async def get_roi():
    """获取当前 ROI 配置"""
    config = load_config()
    if config and 'roi' in config:
        roi_config = config['roi']
        
        # 新格式：multi-preset
        if isinstance(roi_config, dict) and 'presets' in roi_config:
            active_preset = roi_config.get('active_preset', 'receive_area')
            if active_preset in roi_config['presets']:
                coords = roi_config['presets'][active_preset]['coordinates']
                return {
                    "left": coords[0],
                    "top": coords[1],
                    "right": coords[2],
                    "bottom": coords[3],
                    "active_preset": active_preset,
                    "presets": roi_config['presets']
                }
        # 旧格式：flat list
        elif isinstance(roi_config, list) and len(roi_config) == 4:
            return {
                "left": roi_config[0],
                "top": roi_config[1],
                "right": roi_config[2],
                "bottom": roi_config[3],
                "active_preset": "default",
                "presets": {}
            }
    
    return {"left": 0, "top": 0, "right": 0, "bottom": 0, "active_preset": "receive_area", "presets": {}}


@router.post("/roi")
async def update_roi(roi: ROIUpdate):
    """更新 ROI 配置"""
    config = load_config()
    if not config:
        config = {}
    
    if 'roi' not in config:
        config['roi'] = {}
    
    roi_config = config['roi']
    
    # 初始化 multi-preset 结构
    if not isinstance(roi_config, dict) or 'presets' not in roi_config:
        roi_config['presets'] = {
            'receive_area': {'name': '接收区域', 'description': '群消息接收和显示区域', 'coordinates': [0, 0, 0, 0], 'enabled': True},
            'send_area': {'name': '发送区域', 'description': '微信消息输入和发送区域', 'coordinates': [0, 0, 0, 0], 'enabled': True}
        }
        roi_config['active_preset'] = 'receive_area'
    
    # 更新当前激活预设的坐标
    active_preset = roi_config.get('active_preset', 'receive_area')
    if roi.preset and roi.preset in roi_config['presets']:
        active_preset = roi.preset
    
    roi_config['presets'][active_preset]['coordinates'] = [
        roi.left,
        roi.top,
        roi.right,
        roi.bottom
    ]
    
    # 如果提供了 active_preset，更新激活预设
    if roi.active_preset:
        roi_config['active_preset'] = roi.active_preset
    
    config['roi'] = roi_config
    
    if save_config(config):
        logger.info(f"ROI 已更新: {roi}")
        return {"status": "success", "message": "ROI 配置已保存", "roi": roi_config}
    return {"status": "error", "message": "保存 ROI 配置失败"}
