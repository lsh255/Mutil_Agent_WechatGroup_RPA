import api from './api'
import type {
  SandboxInstance,
  ROIConfig,
  LogEntry,
  ProducerStatus,
  ScreenshotResponse,
  ConfigResponse
} from '@/types/sandbox'

const SANDBOX_API_BASE = '/api/sandbox'

export interface SandboxListResponse {
  instances: SandboxInstance[]
  total: number
}

export interface StartInstanceRequest {
  instanceId: string
  userId?: string
}

export interface StopInstanceRequest {
  instanceId: string
}

export interface UpdateROIRequest {
  instanceId: string
  roi: ROIConfig
}

export interface ScreenshotRequest {
  instanceId: string
  format?: 'png' | 'jpeg'
}

export interface LogsRequest {
  instanceId: string
  level?: 'info' | 'warn' | 'error' | 'all'
  limit?: number
  since?: number
}

export async function getSandboxInstances(): Promise<SandboxInstance[]> {
  const response = await api.get(`${SANDBOX_API_BASE}/instances`)
  return response.data
}

export async function getInstanceStatus(userId: string = 'default'): Promise<SandboxInstance> {
  const response = await api.get(`${SANDBOX_API_BASE}/status/${userId}`)
  return response.data
}

export async function startInstance(request: StartInstanceRequest): Promise<SandboxInstance> {
  const userId = request.userId || 'default'
  const response = await api.post(`${SANDBOX_API_BASE}/start/${userId}`)
  return response.data
}

export async function stopInstance(_request: StopInstanceRequest): Promise<SandboxInstance> {
  const userId = 'default'
  const response = await api.post(`${SANDBOX_API_BASE}/stop/${userId}`)
  return response.data
}

export async function restartInstance(_request: StopInstanceRequest): Promise<SandboxInstance> {
  const userId = 'default'
  const response = await api.post(`${SANDBOX_API_BASE}/restart/${userId}`)
  return response.data
}

export async function getROIConfig(instanceId: string): Promise<ROIConfig> {
  const response = await api.get(`${SANDBOX_API_BASE}/instances/${instanceId}/roi`)
  return response.data
}

export async function updateROIConfig(request: UpdateROIRequest): Promise<ROIConfig> {
  const response = await api.post(`${SANDBOX_API_BASE}/roi`, request.roi)
  return response.data
}

export async function takeScreenshot(request: ScreenshotRequest): Promise<ScreenshotResponse> {
  const response = await api.get(`${SANDBOX_API_BASE}/screenshot`, {
    params: {
      format: request.format || 'png'
    },
    responseType: 'arraybuffer'
  })
  return response.data
}

export async function getLogs(request: LogsRequest): Promise<LogEntry[]> {
  const response = await api.get(`${SANDBOX_API_BASE}/logs`, {
    params: {
      level: request.level || 'all',
      limit: request.limit || 100,
      since: request.since
    }
  })
  return response.data
}

export async function getProducerStatus(instanceId: string): Promise<ProducerStatus[]> {
  const response = await api.get(`${SANDBOX_API_BASE}/instances/${instanceId}/producers`)
  return response.data
}

export async function getConfig(instanceId: string): Promise<ConfigResponse> {
  const response = await api.get(`${SANDBOX_API_BASE}/instances/${instanceId}/config`)
  return response.data
}

export function createSandboxWebSocket(instanceId: string): WebSocket {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}${SANDBOX_API_BASE}/instances/${instanceId}/stream`
  return new WebSocket(wsUrl)
}
