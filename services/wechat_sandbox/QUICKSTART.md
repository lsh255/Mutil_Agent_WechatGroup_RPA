# 微信监控服务快速启动指南

## 单实例部署（推荐用于测试）

### 1. 启动服务

```bash
cd services/wechat_sandbox
docker-compose up -d
```

### 2. 登录微信

- 访问：http://localhost:6080
- 密码：vnc123
- 在VNC界面中操作Linux微信扫码登录

### 3. 配置监控区域

- 访问：http://localhost:8000/api/ui
- 在右侧面板输入ROI坐标（如：left=100, top=200, right=500, bottom=800）
- 点击"更新监控区域"

### 4. 查看服务状态

- 访问：http://localhost:8000/status
- 或使用Web管理界面实时查看

## 多实例部署（推荐用于生产环境）

### 1. 启动多实例服务

```bash
cd services/wechat_sandbox
docker-compose -f docker-compose.multi.yml up -d
```

### 2. 为每个实例登录微信

- 实例1：http://localhost:6081
- 实例2：http://localhost:6082
- 实例3：http://localhost:6083
- 密码：vnc123

### 3. 为每个实例配置监控区域

- 实例1：http://localhost:8001/api/ui
- 实例2：http://localhost:8002/api/ui
- 实例3：http://localhost:8003/api/ui

## 端口说明

### 单实例
- 8000: FastAPI服务
- 6080: noVNC Web界面
- 5900: VNC服务
- 6379: Redis服务

### 多实例
| 实例 | FastAPI | noVNC | VNC |
|------|---------|-------|-----|
| 1 | 8001 | 6081 | 5901 |
| 2 | 8002 | 6082 | 5902 |
| 3 | 8003 | 6083 | 5903 |

## 常见问题

### VNC无法连接
- 检查容器是否启动：`docker ps`
- 查看日志：`docker logs wechat_producer_service`
- 确认端口是否被占用

### 微信无法登录
- 通过VNC手动操作Linux微信
- 确保网络连接正常
- 检查微信二维码是否正常显示

### 消息无法获取
- 检查ROI配置是否正确
- 确认微信窗口位置
- 查看服务日志：`docker logs -f wechat_producer_service`

### 重启服务

```bash
# 重启单个实例
docker-compose restart producer_service

# 重启多实例
docker-compose -f docker-compose.multi.yml restart producer_service_1
```

## API调用示例

### 获取服务状态
```bash
curl http://localhost:8000/status
```

### 更新ROI配置
```bash
curl -X POST http://localhost:8000/api/roi \
  -H "Content-Type: application/json" \
  -d '{"left":100,"top":200,"right":500,"bottom":800}'
```

### 获取屏幕截图
```bash
curl http://localhost:8000/api/screenshot
```

### 消费消息流
```bash
curl -N http://localhost:8000/stream
```

## 性能优化

- 调整 `capture_interval_ms` 降低CPU使用率
- 增加ROI精度减少误检
- 使用Redis集群提升并发性能
- 增加实例数量实现水平扩展
