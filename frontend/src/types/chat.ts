export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
}

export interface TaskConfig {
  workItems: Array<{
    workName: string
    location: string
    personnel: string[]
    description?: string
  }>
}

export interface GroupMonitor {
  groupName: string
  status: 'monitoring' | 'stopped' | 'error'
  messageCount: number
  lastUpdate: number
}

export interface IntentRecognitionResult {
  intent: 'task_config' | 'monitor_group' | 'other'
  confidence: number
}

export interface AgentDecision {
  actionType: 'write_report' | 'update_ledger' | 'save_message' | 'continue'
  reason: string
  timestamp: number
}
