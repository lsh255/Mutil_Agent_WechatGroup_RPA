# WeChat AI Agent Frontend

基于 React 的微信群自动化 AI Agent 系统前端应用。

## 技术栈

- **框架**: React 18.3+
- **构建工具**: Vite 5.4+
- **语言**: TypeScript 5.5+
- **路由**: React Router 6.26+
- **状态管理**: Zustand 4.5+
- **UI 组件**: shadcn/ui + Tailwind CSS 3.4+
- **图表**: Recharts 2.12+
- **通信**: WebSocket

## 项目结构

```
frontend/
├── src/
│   ├── pages/              # 页面组件
│   │   ├── chat/           # 对话式 Web UI（面向用户）
│   │   │   ├── ChatPage.tsx
│   │   │   ├── components/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageInput.tsx
│   │   │   │   ├── TaskStatusCard.tsx
│   │   │   │   ├── AgentDecisionDisplay.tsx
│   │   │   │   └── hooks/
│   │   │   │       └── useWebSocket.ts
│   │   ├── admin/          # 系统管理界面（面向管理员）
│   │   │   ├── AdminPage.tsx
│   │   │   └── components/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── SandboxMonitor.tsx
│   │   │       ├── AgentMonitor.tsx
│   │   │       ├── WorkflowMonitor.tsx
│   │   │       ├── InstanceList.tsx
│   │   │       ├── SystemMetrics.tsx
│   │   │       └── LogViewer.tsx
│   │   └── NotFound.tsx
│   ├── components/         # 共享组件
│   ├── services/           # API 服务
│   ├── types/              # TypeScript 类型定义
│   ├── store/              # 状态管理
│   ├── utils/              # 工具函数
│   ├── constants/          # 常量
│   ├── router/             # 路由配置
│   ├── assets/             # 静态资源
│   ├── App.tsx             # 根组件
│   └── main.tsx            # 应用入口
├── public/                 # 公共静态文件
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── nginx.conf
```

## 开发

### 安装依赖

```bash
npm install
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

## 页面说明

### 对话式 Web UI (`/chat`)

面向用户的简单对话界面，提供：
- 消息发送与接收
- 任务配置状态显示
- Agent 决策结果展示
- 实时 WebSocket 通信

### 系统管理界面 (`/admin`)

面向管理员的管理控制台，提供：
- 系统概览 Dashboard
- 沙盒实例监控与管理
- Agent 状态监控
- 工作流监控
- 实例列表管理
- 系统指标可视化
- 实时日志查看器

## Docker 部署

### 构建镜像

```bash
docker build -t wechat-ai-agent-frontend .
```

### 运行容器

```bash
docker run -p 80:80 wechat-ai-agent-frontend
```
