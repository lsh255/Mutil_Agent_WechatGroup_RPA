import { create } from 'zustand'
import { Message, Task, AgentDecision } from '@/types'

interface TaskConfig {
  groupId?: string
  workItems: Array<{
    location: string
    personnel: string[]
    content?: string
  }>
}

interface ChatState {
  messages: Message[]
  isProcessing: boolean
  taskConfig: TaskConfig | null
  lastAgentDecision: AgentDecision | null
  currentIntent: string | null
  connected: boolean
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void
  clearMessages: () => void
  setProcessing: (processing: boolean) => void
  setTaskConfig: (config: TaskConfig | null) => void
  setLastAgentDecision: (decision: AgentDecision | null) => void
  setCurrentIntent: (intent: string | null) => void
  setConnected: (connected: boolean) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isProcessing: false,
  taskConfig: null,
  lastAgentDecision: null,
  currentIntent: null,
  connected: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: Date.now().toString(),
          timestamp: Date.now(),
        },
      ],
    })),
  clearMessages: () => set({ messages: [] }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  setTaskConfig: (taskConfig) => set({ taskConfig }),
  setLastAgentDecision: (lastAgentDecision) => set({ lastAgentDecision }),
  setCurrentIntent: (currentIntent) => set({ currentIntent }),
  setConnected: (connected) => set({ connected }),
}))
