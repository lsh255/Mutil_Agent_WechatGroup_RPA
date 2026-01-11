# 任务清单

## 阶段1：基础架构（第1-2周）

### 1.1 ConstellationAgent基础框架
- [ ] 实现ConstellationState状态定义（agents/constellation/state.py）
- [ ] 实现UserRequest数据模型（core/schemas.py）
- [ ] 实现TaskExecution数据模型（core/schemas.py）
- [ ] 实现create_constellation_workflow()工作流（core/workflows/constellation_workflow.py）
- [ ] 集成RedisCheckpointer状态持久化（core/workflows/constellation_workflow.py）

### 1.2 DAGBuilder任务分解逻辑
- [ ] 实现build_from_request()意图解析（agents/constellation/dag_builder.py）
- [ ] 实现_build_login_dag()登录流程DAG（agents/constellation/dag_builder.py）
- [ ] 实现_build_workflow_dag()监控流程DAG（agents/constellation/dag_builder.py）
- [ ] 实现_build_arrangement_dag()工作安排DAG（agents/constellation/dag_builder.py）

### 1.3 TaskOrchestrator任务分发引擎
- [ ] 实现_get_ready_tasks()依赖管理（agents/constellation/task_orchestrator.py）
- [ ] 实现_dispatch_sandbox_auth_task()沙盒认证分发（agents/constellation/task_orchestrator.py）
- [ ] 实现_dispatch_monitor_task()监控任务分发（agents/constellation/task_orchestrator.py）
- [ ] 实现_dispatch_multimodal_task()多模态任务分发（agents/constellation/task_orchestrator.py）

### 1.4 工作流节点实现
- [ ] 实现IntentParserNode意图解析节点（core/workflows/nodes/intent_parser_node.py）
- [ ] 实现DAGBuilderNode DAG构建节点（core/workflows/nodes/dag_builder_node.py）
- [ ] 实现TaskOrchestratorNode任务编排节点（core/workflows/nodes/task_orchestrator_node.py）
- [ ] 实现ResultCollectorNode结果收集节点（core/workflows/nodes/result_collector_node.py）

## 阶段2：新增Agent（第3-4周）

### 2.1 SandboxAuthAgent
- [ ] 实现SandboxManager容器管理器（agents/sandbox/sandbox_manager.py）
- [ ] 实现check_container_status()容器状态检查（agents/sandbox/sandbox_manager.py）
- [ ] 实现start_container()容器启动（agents/sandbox/sandbox_manager.py）
- [ ] 实现check_login_status()登录状态检查（agents/sandbox/sandbox_manager.py）
- [ ] 实现get_vnc_url() VNC地址获取（agents/sandbox/sandbox_manager.py）
- [ ] 实现SandboxAuthNode工作流节点（core/workflows/nodes/sandbox_auth_node.py）

### 2.2 UserFeedbackAgent
- [ ] 实现WebSocketManager WebSocket管理器（agents/user_interaction/websocket_manager.py）
- [ ] 实现request_feedback()用户反馈请求（agents/user_interaction/websocket_manager.py）
- [ ] 实现broadcast_message()消息广播（agents/user_interaction/websocket_manager.py）
- [ ] 实现UserFeedbackNode工作流节点（core/workflows/nodes/user_feedback_node.py）

### 2.3 TrackerAgent
- [ ] 实现TaskStatusState任务状态定义（agents/tracker/task_status.py）
- [ ] 实现RedisClient任务状态持久化（agents/tracker/task_status.py）
- [ ] 实现get_task_status()状态查询（agents/tracker/task_status.py）
- [ ] 实现save_task_status()状态保存（agents/tracker/task_status.py）
- [ ] 实现TrackerNode工作流节点（core/workflows/nodes/tracker_node.py）

## 阶段3：前端交互功能（第5-6周）

### 3.1 WebSocket实时通信
- [ ] 实现前端WebSocket连接管理（frontend/src/hooks/useWebSocket.ts）
- [ ] 实现消息订阅和事件处理（frontend/src/hooks/useWebSocket.ts）
- [ ] 实现用户交互UI组件（frontend/src/components/interaction/ScanQRCode.tsx）

### 3.2 工作流可视化页面
- [ ] 实现DAG任务图可视化组件（frontend/src/components/workflow/DAGVisualization.tsx）
- [ ] 实现任务状态监控面板（frontend/src/components/workflow/TaskMonitor.tsx）
- [ ] 实现沙盒容器管理界面（frontend/src/components/workflow/SandboxManager.tsx）

### 3.3 用户配置界面
- [ ] 实现工作安排配置表单（frontend/src/pages/workflow/WorkArrangement.tsx）
- [ ] 实现群聊监控配置表单（frontend/src/pages/workflow/GroupMonitor.tsx）
- [ ] 实现扫码登录引导流程（frontend/src/pages/dashboard/Dashboard.tsx）

## 阶段4：集成测试（第7周）

### 4.1 单Agent模式测试
- [ ] 验证原有工作流功能（tests/integration/test_single_agent_workflow.py）
- [ ] 验证向后兼容性（tests/integration/test_single_agent_workflow.py）
- [ ] 性能基准测试（tests/performance/test_response_time.py）

### 4.2 多Agent模式测试
- [ ] 测试沙盒登录流程（tests/integration/test_multi_agent_workflow.py）
- [ ] 测试用户交互反馈（tests/integration/test_multi_agent_workflow.py）
- [ ] 测试任务动态分解（tests/integration/test_multi_agent_workflow.py）
- [ ] 测试DAG执行和演化（tests/integration/test_multi_agent_workflow.py）

### 4.3 混合模式测试
- [ ] 测试单/多模式切换（tests/integration/test_hybrid_mode.py）
- [ ] 测试状态共享机制（tests/integration/test_hybrid_mode.py）
- [ ] 测试资源隔离（tests/integration/test_hybrid_mode.py）

### 4.4 性能测试和优化
- [ ] 响应时间测试（tests/performance/test_response_time.py）
- [ ] 并发能力测试（tests/performance/test_concurrency.py）
- [ ] 资源占用测试（tests/performance/test_response_time.py）
- [ ] 优化热点路径（根据测试结果）

## 阶段5：文档与部署（第8周）

### 5.1 文档完善
- [ ] 完善API文档（docs/api.md）
- [ ] 完善部署文档（docs/deployment.md）
- [ ] 完善用户手册（docs/user_manual.md）

### 5.2 部署配置
- [ ] Docker镜像构建（Dockerfile）
- [ ] Docker Compose配置（config/docker-compose.yml）
- [ ] 环境变量配置（config/.env.example）

## 其他任务

### 配置文件
- [ ] 扩展settings.py配置项（config/settings.py）
- [ ] 添加Redis Checkpointer配置（config/settings.py）
- [ ] 添加WebSocket配置（config/settings.py）

### 依赖管理
- [ ] 更新requirements.txt依赖列表
- [ ] 更新frontend/package.json依赖列表

### 日志与监控
- [ ] 添加ConstellationAgent日志（agents/constellation/constellation_agent.py）
- [ ] 添加DAGBuilder日志（agents/constellation/dag_builder.py）
- [ ] 添加TaskOrchestrator日志（agents/constellation/task_orchestrator.py）
- [ ] 添加SandboxAuthAgent日志（agents/sandbox/sandbox_auth_agent.py）
- [ ] 添加UserFeedbackAgent日志（agents/user_interaction/user_feedback_agent.py）
- [ ] 添加TrackerAgent日志（agents/tracker/tracker_agent.py）
- [ ] 添加Prometheus指标收集

### 代码规范
- [ ] 代码风格检查（flake8/black）
- [ ] 类型检查（mypy）
- [ ] 安全扫描（bandit）

## 里程碑检查

### M1: 基础架构完成（第2周）
- [ ] ConstellationAgent框架完成
- [ ] DAGBuilder完成
- [ ] TaskOrchestrator完成

### M2: 新增Agent完成（第4周）
- [ ] SandboxAuthAgent完成
- [ ] UserFeedbackAgent完成
- [ ] TrackerAgent完成

### M3: 前端交互完成（第6周）
- [ ] WebSocket完成
- [ ] 工作流可视化完成
- [ ] 配置界面完成

### M4: 测试完成（第7周）
- [ ] 单Agent模式测试通过
- [ ] 多Agent模式测试通过
- [ ] 混合模式测试通过
- [ ] 性能测试通过

### M5: 上线准备（第8周）
- [ ] 文档完成
- [ ] 部署配置完成
- [ ] Docker镜像构建完成
