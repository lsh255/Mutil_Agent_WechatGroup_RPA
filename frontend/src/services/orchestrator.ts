import api from './api'
import { API_ENDPOINTS } from '@/constants/api'

export interface WorkflowTriggerRequest {
  userMessage: string
  userId?: string
}

export interface WorkflowStatusResponse {
  workflowId: string
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error'
  currentNode: string
  startTime: number
  endTime?: number
}

export async function triggerWorkflow(request: WorkflowTriggerRequest): Promise<WorkflowStatusResponse> {
  const response = await api.post(API_ENDPOINTS.orchestrator.trigger, request)
  return response.data
}

export async function getWorkflowStatus(workflowId: string): Promise<WorkflowStatusResponse> {
  const response = await api.get(`${API_ENDPOINTS.orchestrator.status}/${workflowId}`)
  return response.data
}

export function createWorkflowWebSocket(workflowId: string): WebSocket {
  return new WebSocket(`${API_ENDPOINTS.orchestrator.stream}/${workflowId}`)
}
