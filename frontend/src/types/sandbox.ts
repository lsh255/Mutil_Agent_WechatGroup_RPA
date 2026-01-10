export interface SandboxInstance {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error' | 'initializing'
  containerId?: string
  port: number
  vncPort: number
  createdAt: number
  lastHeartbeat?: number
  resources: {
    cpu: number
    memory: number
    disk: number
  }
}

export interface SandboxMetrics {
  uptime: number
  totalMessages: number
  errorCount: number
  lastError?: string
}

export interface ROIConfig {
  left: number
  top: number
  right: number
  bottom: number
}

export interface LogEntry {
  timestamp: number
  level: 'info' | 'warn' | 'error'
  message: string
}

export interface ProducerStatus {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error'
}

export interface ScreenshotResponse {
  blob: Blob
  url: string
}

export interface ConfigResponse {
  roi: ROIConfig
  vncPassword?: string
  monitoringEnabled: boolean
}
