from fastapi import FastAPI  # 导入 FastAPI 框架
from fastapi.middleware.cors import CORSMiddleware  # 导入 CORS 中间件
from fastapi.responses import StreamingResponse  # 导入流式响应
from contextlib import asynccontextmanager  # 导入异步上下文管理器
import redis  # 导入 Redis 客户端
import logging  # 导入日志记录模块
import os  # 导入操作系统接口模块
import yaml  # 导入 YAML 解析库
from pathlib import Path  # 导入路径处理库
from PIL import ImageGrab  # 导入截图库
import io  # 导入内存操作库
from typing import Optional, Dict, Any  # 导入类型注解

logging.basicConfig(level=logging.INFO)  # 配置日志级别为 INFO
logger = logging.getLogger(__name__)  # 创建日志记录器

redis_client = None  # 全局 Redis 客户端变量

CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"  # 配置文件路径

@asynccontextmanager  # 异步上下文管理器装饰器
async def lifespan(app: FastAPI):  # 应用生命周期管理函数
    global redis_client  # 声明使用全局变量
    try:  # 尝试连接 Redis
        redis_host = os.getenv("REDIS_HOST", "redis")  # 从环境变量获取 Redis 主机地址，默认为 redis
        redis_port = int(os.getenv("REDIS_PORT", "6379"))  # 从环境变量获取 Redis 端口，默认为 6379
        redis_db = int(os.getenv("REDIS_DB", "0"))  # 从环境变量获取 Redis 数据库编号，默认为 0
        
        logger.info(f"Connecting to Redis: {redis_host}:{redis_port}/{redis_db}")  # 记录连接日志
        redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)  # 创建 Redis 客户端
        redis_client.ping()  # 测试连接
        logger.info("Redis connection successful")  # 记录连接成功日志
        
        app.state.redis = redis_client  # 将 Redis 客户端存入应用状态
        yield  # 暂停执行，等待应用关闭
    except Exception as e:  # 捕获异常
        logger.error(f"Failed to connect to Redis: {e}")  # 记录错误日志
        app.state.redis = None  # 将 Redis 客户端设为 None
        yield  # 暂停执行，等待应用关闭
    finally:  # 清理资源
        if redis_client:  # 如果 Redis 客户端存在
            redis_client.close()  # 关闭 Redis 连接
            logger.info("Redis connection closed")  # 记录关闭日志

app = FastAPI(title="WeChat Sandbox API", lifespan=lifespan)  # 创建 FastAPI 应用实例

app.add_middleware(  # 添加中间件
    CORSMiddleware,  # CORS 中间件
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,  # 允许携带凭证
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/")  # 根路径路由
async def root():  # 根路径处理函数
    return {"status": "ok", "service": "wechat_sandbox", "message": "WeChat Sandbox API is running"}  # 返回服务状态信息

@app.get("/health")  # 健康检查路由
async def health():  # 健康检查处理函数
    status = {"status": "healthy", "redis": False}  # 初始化状态字典
    if app.state.redis:  # 如果 Redis 客户端存在
        try:  # 尝试测试 Redis 连接
            app.state.redis.ping()  # 测试连接
            status["redis"] = True  # 设置 Redis 连接状态为 True
        except Exception as e:  # 捕获异常
            logger.error(f"Redis health check failed: {e}")  # 记录错误日志
    return status  # 返回状态信息

@app.get("/screenshot")  # 截图路由
async def screenshot():  # 截图处理函数
    return {"message": "Screenshot endpoint (to be implemented)"}  # 返回待实现消息

@app.get("/status")  # 状态路由
async def status():  # 状态处理函数
    return {  # 返回状态信息
        "service": "wechat_sandbox",  # 服务名称
        "status": "running",  # 服务状态
        "redis_connected": app.state.redis is not None  # Redis 连接状态
    }

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

@app.get("/api/config")
async def get_config():
    """获取完整配置"""
    config = load_config()
    if config:
        return config
    return {"error": "配置文件不存在或为空"}

@app.post("/api/config")
async def update_config(config: Dict[str, Any]):
    """更新完整配置"""
    if not isinstance(config, dict):
        logger.error(f"无效的配置格式: {type(config)}")
        return {"status": "error", "message": "配置必须是字典格式"}
    
    if save_config(config):
        return {"status": "success", "message": "配置已保存"}
    return {"status": "error", "message": "保存配置失败"}

@app.get("/api/roi")
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

@app.post("/api/roi")
async def update_roi(roi: Dict[str, Any]):
    """更新 ROI 配置"""
    if not isinstance(roi, dict):
        logger.error(f"无效的 ROI 格式: {type(roi)}")
        return {"status": "error", "message": "ROI 必须是字典格式"}
    
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
    if 'preset' in roi and roi['preset'] in roi_config['presets']:
        active_preset = roi['preset']
    
    roi_config['presets'][active_preset]['coordinates'] = [
        roi.get('left', 0),
        roi.get('top', 0),
        roi.get('right', 0),
        roi.get('bottom', 0)
    ]
    
    # 如果提供了 active_preset，更新激活预设
    if 'active_preset' in roi:
        roi_config['active_preset'] = roi['active_preset']
    
    config['roi'] = roi_config
    
    if save_config(config):
        logger.info(f"ROI 已更新: {roi}")
        return {"status": "success", "message": "ROI 配置已保存", "roi": roi_config}
    return {"status": "error", "message": "保存 ROI 配置失败"}

@app.get("/api/screenshot")
async def get_screenshot():
    """获取当前屏幕截图"""
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return StreamingResponse(img_byte_arr, media_type="image/png")
    except Exception as e:
        logger.error(f"截图失败: {e}")
        return {"status": "error", "message": "截图失败"}

@app.post("/api/restart")
async def restart_service():
    """重启服务（需配合 systemd 或 Docker 实现）"""
    return {"status": "success", "message": "重启请求已接收（需配置 systemd 或 Docker 重启策略）"}

@app.get("/stream")
async def stream_sse():
    """SSE 流式推送监控数据"""
    async def event_generator():
        while True:
            yield "data: {\"status\": \"alive\"}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
