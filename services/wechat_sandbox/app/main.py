from fastapi import FastAPI  # 导入 FastAPI 框架
from fastapi.middleware.cors import CORSMiddleware  # 导入 CORS 中间件
from contextlib import asynccontextmanager  # 导入异步上下文管理器
import redis  # 导入 Redis 客户端
import logging  # 导入日志记录模块

logging.basicConfig(level=logging.INFO)  # 配置日志级别为 INFO
logger = logging.getLogger(__name__)  # 创建日志记录器

redis_client = None  # 全局 Redis 客户端变量

@asynccontextmanager  # 异步上下文管理器装饰器
async def lifespan(app: FastAPI):  # 应用生命周期管理函数
    global redis_client  # 声明使用全局变量
    try:  # 尝试连接 Redis
        redis_host = app.state.env_vars.get("REDIS_HOST", "redis")  # 从环境变量获取 Redis 主机地址，默认为 redis
        redis_port = int(app.state.env_vars.get("REDIS_PORT", 6379))  # 从环境变量获取 Redis 端口，默认为 6379
        redis_db = int(app.state.env_vars.get("REDIS_DB", 0))  # 从环境变量获取 Redis 数据库编号，默认为 0
        
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
