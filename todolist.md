# 多模态Agent微信群自动化项目 - 开发任务列表

基于架构设计文档v3.md和方案1.md的UFO Constellation DAG架构，本任务列表按开发阶段组织。

---

## 阶段1：基础设施层搭建（优先级：高）

### 1.1 Redis环境配置
- [ ] 安装Redis 7.2+服务器
- [ ] 配置Redis Streams（wechat_sandbox_stream, agent_response_stream, constellation_stream）
- [ ] 配置Redis持久化（RDB + AOF）
- [ ] 验证Redis Checkpointer功能

### 1.2 Docker容器环境
- [ ] 安装Docker和Docker Compose
- [ ] 构建wechat-sandbox:latest镜像
- [ ] 配置容器网络和端口映射规则
- [ ] 编写docker-compose.yml启动脚本

### 1.3 项目依赖安装
- [ ] 安装LangGraph (>=0.0.50)
- [ ] 安装LangChain生态（LangChain >=0.1.0, LangChain-Community >=0.0.10）
- [ ] 安装Ollama服务端和模型（Qwen3-VL-8B, Qwen3-72B, Qwen3-Embedding-8B）
- [ ] 安装ChromaDB向量数据库
- [ ] 安装Python依赖（FastAPI >=0.104.0, Pydantic >=2.5.0, structlog >=23.2.0）
- [ ] 安装前端依赖（React 18.3+, Vite 5.4+, TypeScript 5.5+）

### 1.4 ChromaDB初始化
- [ ] 创建ChromaDB集合（messages, tasks, documents）
- [ ] 编写嵌入模型集成代码
- [ ] 测试向量检索功能

---

## 阶段2：核心数据模型与类型定义（优先级：高）

### 2.1 UFO Constellation状态模型
- [ ] 定义ConstellationState TypedDict
- [ ] 定义UserRequest TypedDict
- [ ] 定义TaskExecution TypedDict
- [ ] 定义TaskStatusState TypedDict

### 2.2 单Agent状态模型
- [ ] 定义AgentState TypedDict
- [ ] 定义WorkflowState TypedDict

### 2.3 沙盒数据模型
- [ ] 定义RawMessage模型
- [ ] 定义MultimodalAnalysis模型
- [ ] 定义TaskStatus模型
- [ ] 定义DocumentUpdate模型

### 2.4 Redis Streams消息格式
- [ ] 定义基础消息格式（user_id, message_type, timestamp, payload）
- [ ] 定义扩展消息格式（interaction_request, interaction_response, dag_task, agent_result）
- [ ] 实现消息序列化/反序列化工具

---

## 阶段3：智能体模块开发（优先级：高）

### 3.1 单Agent模式智能体
- [ ] 实现SandboxMonitorAgent（沙盒监控智能体）
- [ ] 实现MultimodalAnalysisAgent（多模态分析智能体）
- [ ] 实现ReportGenerationAgent（报告生成智能体）
- [ ] 实现OrchestratorAgent（编排智能体）

### 3.2 多Agent模式UFO Constellation智能体
- [ ] 实现IntentParserAgent（意图解析智能体）
- [ ] 实现DAGBuilderAgent（DAG构建智能体）
- [ ] 实现TaskOrchestratorAgent（任务编排智能体）
- [ ] 实现ResultCollectorAgent（结果收集智能体）

### 3.3 辅助智能体
- [ ] 实现SandboxAuthAgent（沙盒认证智能体）
- [ ] 实现UserFeedbackAgent（用户反馈智能体）
- [ ] 实现TrackerAgent（追踪智能体）

### 3.4 智能体基类
- [ ] 实现BaseAgent抽象基类
- [ ] 实现Agent通信接口
- [ ] 实现Agent生命周期管理

---

## 阶段4：工作流编排层开发（优先级：高）

### 4.1 单Agent工作流
- [ ] 实现create_simple_workflow()函数
- [ ] 实现monitor_node节点（监控节点）
- [ ] 实现multimodal_analysis_node节点（多模态分析节点）
- [ ] 实现report_generation_node节点（报告生成节点）
- [ ] 配置工作流条件和边

### 4.2 多Agent Constellation工作流
- [ ] 实现create_constellation_workflow()函数
- [ ] 实现intent_parser_node节点
- [ ] 实现dag_builder_node节点
- [ ] 实现task_orchestrator_node节点
- [ ] 实现result_collector_node节点
- [ ] 配置动态DAG执行逻辑
- [ ] 集成Redis Checkpointer

### 4.3 工作流执行引擎
- [ ] 实现工作流启动/停止控制
- [ ] 实现工作流状态查询
- [ ] 实现工作流异常处理和重试

---

## 阶段5：微信沙盒服务层开发（优先级：高）

### 5.1 沙盒管理器
- [ ] 实现SandboxManager类
- [ ] 实现check_container_status()方法
- [ ] 实现start_container()方法
- [ ] 实现stop_container()方法
- [ ] 实现restart_container()方法
- [ ] 实现get_container_logs()方法

### 5.2 WebSocket管理器
- [ ] 实现WebSocketManager类
- [ ] 实现connect()方法
- [ ] 实现disconnect()方法
- [ ] 实现broadcast_message()方法
- [ ] 实现request_feedback()方法
- [ ] 实现send_message()方法

### 5.3 SSE消费与转发器
- [ ] 实现agent_consumer.py（SSE消费者）
- [ ] 实现消息转发到Redis Streams
- [ ] 实现消息格式转换
- [ ] 实现错误处理和重连机制

### 5.4 数据采集模块
- [ ] 实现群消息采集（文本/图片/视频）
- [ ] 实现消息元数据提取（时间、发送者、类型）
- [ ] 实现OCR图片文字识别
- [ ] 实现多模态数据融合

---

## 阶段6：API服务层开发（优先级：中）

### 6.1 FastAPI应用
- [ ] 创建FastAPI应用实例
- [ ] 配置CORS中间件
- [ ] 配置日志中间件（structlog）
- [ ] 配置Prometheus监控端点

### 6.2 RESTful API端点
- [ ] POST /api/workflows/start（启动工作流）
- [ ] GET /api/workflows/{workflow_id}/status（查询工作流状态）
- [ ] POST /api/workflows/{workflow_id}/stop（停止工作流）
- [ ] GET /api/agents/{agent_id}/status（查询智能体状态）
- [ ] GET /api/sandbox/{user_id}/status（查询沙盒状态）
- [ ] POST /api/sandbox/{user_id}/start（启动沙盒）
- [ ] POST /api/sandbox/{user_id}/stop（停止沙盒）
- [ ] GET /api/tasks/{task_id}/status（查询任务状态）
- [ ] POST /api/tasks/execute（执行任务）
- [ ] GET /api/reports/daily/{date}（获取日报）
- [ ] GET /api/reports/ledger/{date}（获取台账）

### 6.3 WebSocket端点
- [ ] WS /ws/{user_id}（WebSocket连接端点）
- [ ] 实现心跳机制
- [ ] 实现消息ACK确认
- [ ] 实现断线重连

### 6.4 请求/响应模型
- [ ] 定义所有Pydantic请求模型
- [ ] 定义所有Pydantic响应模型
- [ ] 实现数据验证逻辑
- [ ] 实现错误响应格式

---

## 阶段7：前端开发（优先级：中）

### 7.1 项目初始化
- [ ] 创建React + Vite项目
- [ ] 配置TypeScript
- [ ] 配置Tailwind CSS
- [ ] 配置React Router
- [ ] 配置Zustand状态管理

### 7.2 核心页面
- [ ] 首页/工作台页面
- [ ] 沙盒监控页面
- [ ] 工作流监控页面
- [ ] 任务管理页面
- [ ] 报告查看页面

### 7.3 WebSocket通信
- [ ] 实现WebSocket客户端封装
- [ ] 实现消息处理逻辑
- [ ] 实现重连机制
- [ ] 实现交互反馈UI（二维码展示、操作确认等）

### 7.4 数据可视化
- [ ] 集成Recharts图表库
- [ ] 实现沙盒状态监控图表
- [ ] 实现工作流执行进度图
- [ ] 实现任务状态统计图

---

## 阶段8：数据持久化层（优先级：中）

### 8.1 Redis Streams实现
- [ ] 实现消息生产者
- [ ] 实现消息消费者
- [ ] 实现消费者组管理
- [ ] 实现消息确认机制

### 8.2 ChromaDB集成
- [ ] 实现消息向量存储
- [ ] 实现RAG检索接口
- [ ] 实现向量索引优化

### 8.3 文件存储
- [ ] 设计本地文件目录结构
- [ ] 实现图片/视频存储
- [ ] 实现报告文档存储
- [ ] 实现日志文件管理

### 8.4 Redis Checkpointer
- [ ] 实现工作流状态持久化
- [ ] 实现状态恢复逻辑
- [ ] 实现状态版本管理

---

## 阶段9：业务逻辑实现（优先级：高）

### 9.1 用户工作安排管理
- [ ] 实现工作安排录入接口
- [ ] 实现工作安排存储
- [ ] 实现工作安排查询
- [ ] 实现工作安排与消息关联

### 9.2 群聊监控与消息分析
- [ ] 实现群聊消息实时监控
- [ ] 实现图文视频混合消息处理
- [ ] 实现消息时间地点逻辑关联
- [ ] 实现多人协作消息识别

### 9.3 作业逻辑关联
- [ ] 实现作业前-作业中-作业后状态识别
- [ ] 实现作业与消息的关联
- [ ] 实现多人协作作业识别
- [ ] 实现作业状态更新

### 9.4 日报生成
- [ ] 实现基于事项的日报生成逻辑
- [ ] 实现日报模板引擎（Jinja2）
- [ ] 实现日报数据汇总
- [ ] 实现日报导出（Word/PDF）

### 9.5 台账生成
- [ ] 实现基于作业的台账生成逻辑
- [ ] 实现台账模板引擎
- [ ] 实现台账数据汇总
- [ ] 实现台账导出（Excel）

---

## 阶段10：测试与部署（优先级：中）

### 10.1 单元测试
- [ ] 智能体单元测试
- [ ] 工作流节点单元测试
- [ ] API端点单元测试
- [ ] 数据模型单元测试

### 10.2 集成测试
- [ ] 工作流端到端测试
- [ ] Redis Streams集成测试
- [ ] WebSocket通信测试
- [ ] 沙盒容器管理测试

### 10.3 性能测试
- [ ] 工作流执行性能测试
- [ ] Redis吞吐量测试
- [ ] 前端渲染性能测试
- [ ] AI模型响应时间测试

### 10.4 部署准备
- [ ] 编写部署文档
- [ ] 编写环境变量配置模板
- [ ] 编写启动脚本
- [ ] 配置生产环境监控（Prometheus + Grafana）

---

## 阶段11：文档与培训（优先级：低）

### 11.1 技术文档
- [ ] API接口文档（Swagger）
- [ ] 数据库设计文档
- [ ] 部署运维文档
- [ ] 故障排查指南

### 11.2 用户手册
- [ ] 用户操作手册
- [ ] 管理员操作手册
- [ ] 常见问题解答

### 11.3 开发规范
- [ ] 代码规范文档
- [ ] Git提交规范
- [ ] 代码审查流程

---

## 任务依赖关系

```
阶段1（基础设施层）
  └─> 阶段2（数据模型）
      └─> 阶段3（智能体）
          └─> 阶段4（工作流编排）
              └─> 阶段6（API服务）
                  └─> 阶段7（前端开发）
                  
阶段1（基础设施层）
  └─> 阶段5（微信沙盒服务）
      └─> 阶段8（数据持久化）
          └─> 阶段9（业务逻辑）
              └─> 阶段10（测试与部署）
                  └─> 阶段11（文档与培训）
```

---

## 优先级说明

- **高优先级**：核心功能，影响项目可用性，优先完成
- **中优先级**：重要功能，提升用户体验，按计划完成
- **低优先级**：辅助功能，时间允许时完成

---

## 预计工期

- 阶段1：2天
- 阶段2：1天
- 阶段3：5天
- 阶段4：4天
- 阶段5：3天
- 阶段6：3天
- 阶段7：5天
- 阶段8：2天
- 阶段9：7天
- 阶段10：4天
- 阶段11：2天

**总计：约38个工作日**

---

*最后更新：2026-01-11*
