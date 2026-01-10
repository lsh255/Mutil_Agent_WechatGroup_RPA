import api from './api'
import type {
  AgentStatus,
  AgentDecision,
  WorkflowNode,
  AgentMetrics,
  AgentConfig
} from '@/types/agent'

const AGENT_API_BASE = '/api/agent'

export interface AgentListResponse {
  agents: AgentStatus[]
  total: number
}

export interface AgentDecisionRequest {
  agentId: string
  context?: Record<string, any>
  options?: {
    temperature?: number
    maxTokens?: number
  }
}

export interface AgentConfigUpdateRequest {
  agentId: string
  config: Partial<AgentConfig>
}

export async function getAgentStatus(): Promise<AgentListResponse> {
  const response = await api.get(`${AGENT_API_BASE}/status`)
  return response.data
}

export async function getAgentStatusById(agentId: string): Promise<AgentStatus> {
  const response = await api.get(`${AGENT_API_BASE}/status/${agentId}`)
  return response.data
}

export async function triggerDecision(request: AgentDecisionRequest): Promise<AgentDecision> {
  const response = await api.post(`${AGENT_API_BASE}/decide`, request)
  return response.data
}

export async function getWorkflowNodes(): Promise<WorkflowNode[]> {
  const response = await api.get(`${AGENT_API_BASE}/workflow/nodes`)
  return response.data
}

export async function getNodeStatus(nodeId: string): Promise<WorkflowNode> {
  const response = await api.get(`${AGENT_API_BASE}/workflow/nodes/${nodeId}`)
  return response.data
}

export async function getAgentMetrics(agentId: string): Promise<AgentMetrics> {
  const response = await api.get(`${AGENT_API_BASE}/metrics/${agentId}`)
  return response.data
}

export async function getSystemMetrics(): Promise<AgentMetrics> {
  const response = await api.get(`${AGENT_API_BASE}/metrics/system`)
  return response.data
}

export async function updateAgentConfig(request: AgentConfigUpdateRequest): Promise<AgentConfig> {
  const response = await api.put(`${AGENT_API_BASE}/config/${request.agentId}`, request.config)
  return response.data
}

export function createAgentWebSocket(agentId: string): WebSocket {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}${AGENT_API_BASE}/stream/${agentId}`
  return new WebSocket(wsUrl)
}

export function createSystemWebSocket(): WebSocket {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}${AGENT_API_BASE}/stream/system`
  return new WebSocket(wsUrl)
}
