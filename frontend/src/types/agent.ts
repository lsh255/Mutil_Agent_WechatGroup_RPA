export interface AgentState {
  workflowId: string
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error'
  currentNode: string
  currentStep: string
  startTime: number
  endTime?: number
  error?: string
}

export interface WorkflowNode {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'skipped' | 'error'
  startTime?: number
  endTime?: number
  error?: string
}

export interface WorkflowExecution {
  id: string
  nodes: WorkflowNode[]
  state: AgentState
}
