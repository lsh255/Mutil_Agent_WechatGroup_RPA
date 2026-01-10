# 多模态Agent微信群自动化项目 - TODO清单

> 本TODO清单基于旧文档（技术栈文档v1和架构设计文档V2）的历史规划整理而成

---

## 阶段一：基础设施搭建

### 环境配置
- [ ] 安装Python 3.12+
- [ ] 安装Ollama本地服务
- [ ] 下载Qwen3-VL-8B模型
- [ ] 下载Qwen3-72B模型
- [ ] 下载Qwen3-Embedding-8B模型
- [ ] 安装Docker和Docker Compose
- [ ] 安装Redis 7.2+
- [ ] 安装ChromaDB
- [ ] 验证Ollama服务连通性
- [ ] 验证Redis服务连通性
- [ ] 验证ChromaDB服务连通性

### 项目初始化
- [ ] 创建项目目录结构
- [ ] 配置pyproject.toml
- [ ] 配置requirements.txt
- [ ] 配置.env.example文件
- [ ] 配置settings.yaml
- [ ] 配置Black代码格式化
- [ ] 配置Ruff代码检查
- [ ] 配置Mypy类型检查
- [ ] 配置pytest测试框架
- [ ] 配置pytest-asyncio异步测试
- [ ] 配置.gitignore文件

### 基础服务启动
- [ ] 编写Docker Compose配置文件
- [ ] 编写Redis启动脚本
- [ ] 编写ChromaDB启动脚本
- [ ] 编写Ollama启动脚本
- [ ] 测试Redis读写功能
- [ ] 测试ChromaDB添加和检索
- [ ] 测试Ollama模型调用

---

## 阶段二：核心模块开发

### 配置管理模块
- [ ] 实现Settings基类（继承Pydantic BaseSettings）
- [ ] 实现ProjectConfig配置类
- [ ] 实现LangGraphConfig配置类
- [ ] 实现AIConfig配置类
- [ ] 实现OllamaConfig配置类
- [ ] 实现SiliconFlowConfig配置类
- [ ] 实现VectorStoreConfig配置类
- [ ] 实现WeChatSandboxConfig配置类
- [ ] 实现ToolsConfig配置类
- [ ] 实现RedisConfig配置类
- [ ] 实现LoggingConfig配置类
- [ ] 实现多源配置加载（YAML + 环境变量）
- [ ] 实现配置验证逻辑
- [ ] 实现配置默认值处理
- [ ] 实现配置热加载功能
- [ ] 编写配置管理单元测试

### 数据模型定义
- [ ] 定义MessageType枚举（TEXT, IMAGE, MIXED）
- [ ] 定义TaskType枚举（WORK_REPORT, TASK_ASSIGNMENT, STATUS_UPDATE, OTHER）
- [ ] 定义TaskPhase枚举（BEFORE, DURING, AFTER, UNKNOWN）
- [ ] 定义UpdateType枚举（APPEND, UPDATE, DELETE）
- [ ] 定义RawMessage类（sender, content, message_type, image_path等）
- [ ] 定义MultimodalAnalysis类（task_type, task_phase, user, summary等）
- [ ] 定义TaskStatus类（user, task_id, current_phase, is_completed等）
- [ ] 定义DocumentUpdate类（update_type, target_file, data等）
- [ ] 定义AgentState TypedDict（raw_message, multimodal_analysis, task_status等）
- [ ] 编写数据模型单元测试

### 智能体模块开发

#### IntentAgent（意图识别智能体）
- [ ] 编写IntentAgent类定义
- [ ] 实现AGENT_DECISION_SYSTEM_PROMPT
- [ ] 实现AGENT_DECISION_HUMAN_PROMPT
- [ ] 实现LangChain ChatPromptTemplate
- [ ] 集成ChatOllama（Qwen3-72B模型）
- [ ] 实现JsonOutputParser
- [ ] 实现invoke同步方法
- [ ] 实现ainvoke异步方法
- [ ] 实现置信度验证逻辑
- [ ] 实现错误处理和降级
- [ ] 实现create_intent_agent工厂函数
- [ ] 编写IntentAgent单元测试

#### VisualAgent（视觉定位智能体）
- [ ] 编写VisualAgent类定义
- [ ] 实现VISUAL_LOCATOR_SYSTEM_PROMPT
- [ ] 实现VISUAL_LOCATOR_HUMAN_PROMPT
- [ ] 实现Base64图像编码方法
- [ ] 集成ChatOllama（Qwen3-VL-8B模型）
- [ ] 实现多模态HumanMessage构建
- [ ] 实现invoke同步方法
- [ ] 实现ainvoke异步方法
- [ ] 实现区域坐标验证逻辑
- [ ] 实现错误处理和降级
- [ ] 实现create_visual_agent工厂函数
- [ ] 编写VisualAgent单元测试

#### DecisionAgent（决策智能体）
- [ ] 编写DecisionAgent类定义
- [ ] 实现决策提示词模板
- [ ] 集成ChatOllama（Qwen3-72B模型）
- [ ] 实现决策参数传递（message_content, task_name, location等）
- [ ] 实现invoke同步方法
- [ ] 实现ainvoke异步方法
- [ ] 实现决策结果验证逻辑
- [ ] 实现should_execute_action方法
- [ ] 实现错误处理和降级
- [ ] 实现create_decision_agent工厂函数
- [ ] 编写DecisionAgent单元测试

#### MonitorAgent（监控智能体）
- [ ] 编写MonitorAgent类定义
- [ ] 实现微信沙盒监控管理逻辑
- [ ] 实现数据触发至工作流逻辑
- [ ] 编写MonitorAgent单元测试

### LangGraph工作流开发

#### 工作流节点实现
- [ ] 实现MonitorNode.process方法
- [ ] 实现MultimodalNode.analyze方法
- [ ] 实现StateTrackerNode.update方法
- [ ] 实现StateTrackerNode.should_generate_document方法
- [ ] 实现DocumentNode.execute方法
- [ ] 实现节点间数据传递逻辑
- [ ] 编写工作流节点单元测试

#### 工作流图构建
- [ ] 创建StateGraph实例（AgentState）
- [ ] 添加monitor节点
- [ ] 添加multimodal节点
- [ ] 添加state_tracker节点
- [ ] 添加document节点
- [ ] 设置入口点（monitor）
- [ ] 添加monitor→multimodal边
- [ ] 添加multimodal→state_tracker边
- [ ] 实现条件分支（state_tracker→document/END）
- [ ] 编译工作流
- [ ] 编写工作流图构建测试

#### 检查点集成
- [ ] 实现RedisCheckpoint
- [ ] 配置Redis检查点连接
- [ ] 绑定检查点到工作流
- [ ] 实现工作流状态保存
- [ ] 实现工作流状态恢复
- [ ] 编写检查点集成测试

---

## 阶段三：微信沙盒开发

### 双生产者架构

#### Producer1: Observer（消息观察者）
- [ ] 实现Observer类定义
- [ ] 实现微信窗口定位逻辑（win32gui）
- [ ] 实现定时截图功能
- [ ] 实现dHash变化检测算法
- [ ] 实现消息气泡检测逻辑
- [ ] 实现消息区域小截图
- [ ] 实现原始消息队列推送
- [ ] 实现Observer线程管理
- [ ] 实现Observer启停控制
- [ ] 编写Observer单元测试

#### Producer2: ContentFetcher（内容获取者）
- [ ] 实现ContentFetcher类定义
- [ ] 实现原始队列消费逻辑
- [ ] 实现消息气泡精确定位
- [ ] 集成OCR文本提取（Pytesseract）
- [ ] 实现媒体类型识别（图片/文件）
- [ ] 实现发送者信息提取
- [ ] 实现精确消息队列推送
- [ ] 实现ContentFetcher线程管理
- [ ] 实现ContentFetcher启停控制
- [ ] 编写ContentFetcher单元测试

### 核心功能模块

#### Monitor模块
- [ ] 实现Monitor类定义
- [ ] 实现微信窗口定位
- [ ] 实现窗口截图功能
- [ ] 实现窗口尺寸检测
- [ ] 实现跨平台适配（Windows/Mac）
- [ ] 编写Monitor模块测试

#### Detector模块
- [ ] 实现Detector类定义
- [ ] 实现dHash变化检测
- [ ] 实现Hamming距离计算
- [ ] 实现变化阈值配置
- [ ] 实现消息气泡检测
- [ ] 实现气泡区域定位
- [ ] 编写Detector模块测试

#### Extractor模块
- [ ] 实现Extractor类定义
- [ ] 集成Pytesseract OCR
- [ ] 实现文本内容提取
- [ ] 实现媒体文件路径提取
- [ ] 实现发送者头像提取
- [ ] 实现提取结果验证
- [ ] 编写Extractor模块测试

#### Classifier模块
- [ ] 实现Classifier类定义
- [ ] 实现消息类型分类（TEXT/IMAGE/MIXED）
- [ ] 实现分类规则引擎
- [ ] 编写Classifier模块测试

#### Platform模块
- [ ] 定义Platform抽象基类
- [ ] 实现Windows平台适配
- [ ] 实现Mac平台适配
- [ ] 实现平台检测逻辑
- [ ] 编写Platform模块测试

#### Queue模块
- [ ] 实现QueueManager类定义
- [ ] 实现Redis Streams连接
- [ ] 实现原始消息队列管理
- [ ] 实现精确消息队列管理
- [ ] 实现消息推送方法
- [ ] 实现消息消费方法
- [ ] 实现队列重试机制
- [ ] 编写Queue模块测试

### API接口开发
- [ ] 实现GET /stream SSE流式接口
- [ ] 实现POST /config配置管理接口
- [ ] 实现POST /instance服务实例管理接口
- [ ] 实现GET /health健康检查接口
- [ ] 实现API参数验证
- [ ] 实现API错误处理
- [ ] 编写API接口测试

---

## 阶段四：知识库与RAG

### ChromaDB集成
- [ ] 实现VectorStore类定义
- [ ] 实现ChromaDB初始化
- [ ] 实现Collection创建
- [ ] 集成OpenAIEmbeddings（兼容硅基流动）
- [ ] 实现Qwen3-Embedding-8B集成
- [ ] 实现add_documents方法
- [ ] 实现delete方法
- [ ] 实现similarity_search方法
- [ ] 实现批量操作优化
- [ ] 编写VectorStore单元测试

### RAG检索实现
- [ ] 实现query向量化
- [ ] 实现similarity_search_by_vector
- [ ] 实现检索结果过滤
- [ ] 实现上下文拼接
- [ ] 实现检索结果排序
- [ ] 集成到MultimodalNode
- [ ] 编写RAG检索测试

### 知识库初始化脚本
- [ ] 编写init_knowledge_base.py脚本
- [ ] 实现文档加载逻辑
- [ ] 实现文档分块逻辑
- [ ] 实现批量添加到ChromaDB
- [ ] 编写知识库初始化测试

---

## 阶段五：Orchestrator服务开发

### FastAPI服务
- [ ] 实现根路径接口
- [ ] 实现GET /health健康检查接口
- [ ] 实现POST /workflow/trigger工作流触发接口
- [ ] 实现GET /workflow/status工作流状态查询接口
- [ ] 实现SSE流式消息推送接口
- [ ] 实现CORS配置
- [ ] 实现API文档自动生成
- [ ] 编写FastAPI服务测试

### 工作流编排
- [ ] 实现工作流触发逻辑
- [ ] 实现工作流参数验证
- [ ] 实现工作流异步执行
- [ ] 实现工作流状态查询
- [ ] 实现工作流恢复机制
- [ ] 实现工作流取消机制
- [ ] 实现工作流错误处理
- [ ] 实现工作流降级策略
- [ ] 编写工作流编排测试

### Redis集成
- [ ] 实现Redis连接池
- [ ] 实现Redis健康检查
- [ ] 实现消息队列生产者
- [ ] 实现消息队列消费者
- [ ] 实现Redis检查点
- [ ] 实现Redis状态存储
- [ ] 编写Redis集成测试

---

## 阶段六：前端开发

### 项目初始化
- [ ] 创建React + Vite项目
- [ ] 配置TypeScript
- [ ] 配置Tailwind CSS
- [ ] 配置React Router
- [ ] 配置Zustand状态管理
- [ ] 配置Axios HTTP客户端
- [ ] 配置ESLint和Prettier
- [ ] 配置Vite构建配置

### 核心页面开发
- [ ] 实现首页/仪表盘页面
- [ ] 实现对话页面（聊天界面）
- [ ] 实现管理页面（配置管理）
- [ ] 实现实例管理页面
- [ ] 实现工作流监控页面
- [ ] 实现文档查看页面

### API集成
- [ ] 封装Axios HTTP客户端
- [ ] 实现API请求拦截器
- [ ] 实现API响应拦截器
- [ ] 实现错误处理和重试
- [ ] 实现Token管理

### WebSocket集成
- [ ] 实现WebSocket连接管理
- [ ] 实现WebSocket消息接收
- [ ] 实现WebSocket消息发送
- [ ] 实现WebSocket重连机制
- [ ] 实现WebSocket心跳检测

### UI组件开发
- [ ] 实现消息列表组件
- [ ] 实现状态监控组件
- [ ] 实现配置表单组件
- [ ] 实现实例管理组件
- [ ] 实现图表组件（Recharts）
- [ ] 实现加载和错误提示组件

### Zustand状态管理
- [ ] 创建全局store
- [ ] 实现消息状态管理
- [ ] 实现配置状态管理
- [ ] 实现实例状态管理
- [ ] 实现工作流状态管理

---

## 阶段七：文档生成功能

### Excel文档操作
- [ ] 实现Excel模板创建脚本
- [ ] 实现Excel文件读取
- [ ] 实现Excel文件写入
- [ ] 实现Excel单元格更新
- [ ] 实现Excel样式设置
- [ ] 实现Excel表格格式化
- [ ] 编写Excel操作测试

### Word文档操作
- [ ] 实现Word模板创建
- [ ] 实现Word文档生成
- [ ] 集成Jinja2模板引擎
- [ ] 实现模板渲染逻辑
- [ ] 实现Word样式设置
- [ ] 实现Word表格插入
- [ ] 编写Word操作测试

### 集成到工作流
- [ ] 在DocumentNode中调用Excel操作
- [ ] 在DocumentNode中调用Word操作
- [ ] 实现文档生成触发条件
- [ ] 实现文档生成结果验证
- [ ] 实现文档生成错误处理

---

## 阶段八：测试与优化

### 单元测试
- [ ] 编写智能体模块测试
- [ ] 编写工作流节点测试
- [ ] 编写工作流编排测试
- [ ] 编写微信沙盒模块测试
- [ ] 编写VectorStore测试
- [ ] 编写配置管理测试
- [ ] 编写数据模型测试

### 集成测试
- [ ] 编写端到端工作流测试
- [ ] 编写微信沙盒与Orchestrator集成测试
- [ ] 编写前端与后端集成测试
- [ ] 编写SSE流式通信测试

### 性能优化
- [ ] 优化向量数据库检索性能
- [ ] 优化Redis连接池配置
- [ ] 优化AI模型调用
- [ ] 优化前端渲染性能
- [ ] 实现缓存策略

### 安全加固
- [ ] 实现敏感信息脱敏
- [ ] 增强输入验证
- [ ] 实现API鉴权
- [ ] 实现日志脱敏处理
- [ ] 实现HTTPS支持

---

## 阶段九：部署与运维

### Docker化
- [ ] 编写Orchestrator Dockerfile
- [ ] 编写WeChat Sandbox Dockerfile
- [ ] 编写Frontend Dockerfile
- [ ] 编写Docker Compose配置
- [ ] 编写Nginx配置
- [ ] 测试Docker镜像构建

### 部署脚本
- [ ] 编写start_all.py启动脚本
- [ ] 编写停止脚本
- [ ] 编写健康检查脚本
- [ ] 编写日志收集脚本
- [ ] 编写备份脚本

### 监控告警
- [ ] 集成Prometheus客户端
- [ ] 实现结构化日志（structlog）
- [ ] 实现关键指标暴露
- [ ] 实现告警规则
- [ ] 配置日志收集

---

## 代码质量优化

- [ ] 运行Black代码格式化
- [ ] 运行Ruff代码检查
- [ ] 运行Mypy类型检查
- [ ] 修复所有类型检查错误
- [ ] 优化代码注释
- [ ] 重构冗余代码

---

## 文档编写

- [ ] 编写API文档
- [ ] 编写部署文档
- [ ] 编写用户手册
- [ ] 编写开发者指南
- [ ] 编写故障排查指南

---

## 待确认事项

- [ ] 确认AI模型选择和性能要求
- [ ] 确认微信群捕获方案（UI自动化 vs API）
- [ ] 确认部署环境（本地/云服务器）
- [ ] 确认团队分工和资源分配
- [ ] 确认项目时间表和里程碑

---

## 备注

- 本TODO清单基于旧文档（技术栈文档v1和架构设计文档V2）的历史规划整理
- 部分任务可能需要根据实际情况调整优先级
- 建议使用项目管理工具（如GitHub Projects、Jira）跟踪任务进度
- 每个任务完成后及时更新TODO清单状态
