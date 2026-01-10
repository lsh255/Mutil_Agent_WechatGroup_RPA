export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export interface Task {
  id: string
  type: 'config' | 'monitor' | 'report' | 'ledger'
  status: 'pending' | 'running' | 'completed' | 'error'
  content: string
  result?: any
  error?: string
  createdAt: number
  updatedAt: number
}

export interface AgentDecision {
  id: string
  taskId: string
  action: string
  reasoning: string
  timestamp: number
}

export interface WorkflowNode {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'error' | 'skipped'
  startTime?: number
  endTime?: number
  error?: string
}

export interface SandboxInstance {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error' | 'initializing'
  port: number
  vncPort: number
  containerId?: string
  resources: {
    cpu: number
    memory: number
  }
  createdAt: number
}

export interface AgentState {
  workflowId?: string
  status: 'running' | 'paused' | 'completed' | 'error' | 'idle'
  currentNode?: string
  currentStep?: string
  error?: string
}

export interface SystemMetrics {
  timestamp: number
  cpu: number
  memory: number
  disk: number
  network: number
}
