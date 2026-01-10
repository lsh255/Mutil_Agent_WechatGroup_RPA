import { create } from 'zustand'
import { SandboxInstance } from '@/types'

interface SandboxState {
  instances: SandboxInstance[]
  setInstances: (instances: SandboxInstance[]) => void
  addInstance: (instance: SandboxInstance) => void
  updateInstance: (id: string, updates: Partial<SandboxInstance>) => void
  removeInstance: (id: string) => void
}

export const useSandboxStore = create<SandboxState>((set) => ({
  instances: [],
  setInstances: (instances) => set({ instances }),
  addInstance: (instance) =>
    set((state) => ({ instances: [...state.instances, instance] })),
  updateInstance: (id, updates) =>
    set((state) => ({
      instances: state.instances.map((instance) =>
        instance.id === id ? { ...instance, ...updates } : instance
      ),
    })),
  removeInstance: (id) =>
    set((state) => ({
      instances: state.instances.filter((instance) => instance.id !== id),
    })),
}))
