import { create } from 'zustand'
import { AgentState } from '@/types'

interface AgentStoreState {
  agentState: AgentState | null
  setAgentState: (state: AgentState | null) => void
}

export const useAgentStore = create<AgentStoreState>((set) => ({
  agentState: null,
  setAgentState: (agentState) => set({ agentState }),
}))
