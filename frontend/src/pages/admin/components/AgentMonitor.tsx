import { useEffect } from 'react'
import { Play, Pause, CheckCircle, XCircle, Clock } from 'lucide-react'
import { useAgentStore } from '@/store/agentStore'
import { AgentState, WorkflowNode } from '@/types'

export default function AgentMonitor() {
  const agentState = useAgentStore((state) => state.agentState)
  const setAgentState = useAgentStore((state) => state.setAgentState)

  useEffect(() => {
    const fetchAgentState = async () => {
      try {
        const response = await fetch('/api/agent/status')
        const data = await response.json()
        setAgentState(data)
      } catch (error) {
        console.error('Failed to fetch agent state:', error)
      }
    }

    fetchAgentState()
    const interval = setInterval(fetchAgentState, 2000)

    return () => clearInterval(interval)
  }, [setAgentState])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play size={20} className="text-green-500" />
      case 'paused':
        return <Pause size={20} className="text-yellow-500" />
      case 'completed':
        return <CheckCircle size={20} className="text-blue-500" />
      case 'error':
        return <XCircle size={20} className="text-red-500" />
      case 'idle':
        return <Clock size={20} className="text-gray-500" />
      default:
        return null
    }
  }

  const getNodeStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'running':
        return 'bg-blue-500'
      case 'error':
        return 'bg-red-500'
      case 'skipped':
        return 'bg-gray-400'
      default:
        return 'bg-gray-300'
    }
  }

  const mockNodes: WorkflowNode[] = [
    { id: '1', name: 'IntentRecognition', status: 'completed', startTime: Date.now() - 10000, endTime: Date.now() - 8000 },
    { id: '2', name: 'SandboxLogin', status: 'completed', startTime: Date.now() - 8000, endTime: Date.now() - 5000 },
    { id: '3', name: 'VisualPositioning', status: 'completed', startTime: Date.now() - 5000, endTime: Date.now() - 3000 },
    { id: '4', name: 'MessageStream', status: 'running', startTime: Date.now() - 3000 },
    { id: '5', name: 'MultiModalUnderstanding', status: 'pending' },
    { id: '6', name: 'AgentDecision', status: 'pending' },
  ]

  return (
    <div className="space-y-6">
      <div className="p-6 bg-card border border-border rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Agent状态</h3>
          <div className="flex items-center gap-2">
            {getStatusIcon(agentState?.status || 'idle')}
            <span className="font-medium">{agentState?.status || 'idle'}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">工作流ID</div>
            <div className="font-medium">{agentState?.workflowId || '-'}</div>
          </div>
          <div className="p-4 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">当前节点</div>
            <div className="font-medium">{agentState?.currentNode || '-'}</div>
          </div>
          <div className="p-4 bg-muted rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">当前步骤</div>
            <div className="font-medium">{agentState?.currentStep || '-'}</div>
          </div>
        </div>

        {agentState?.error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-sm font-medium text-red-700">错误信息</div>
            <div className="text-sm text-red-600">{agentState.error}</div>
          </div>
        )}
      </div>

      <div className="p-6 bg-card border border-border rounded-lg">
        <h3 className="text-lg font-semibold mb-4">工作流节点</h3>
        <div className="space-y-3">
          {mockNodes.map((node, index) => (
            <div key={node.id} className="flex items-center gap-4">
              <div className={`w-3 h-3 rounded-full ${getNodeStatusColor(node.status)}`} />
              <div className="flex-1">
                <div className="font-medium">{node.name}</div>
                {node.startTime && (
                  <div className="text-xs text-muted-foreground">
                    开始时间：{new Date(node.startTime).toLocaleTimeString()}
                    {node.endTime && ` · 耗时：${node.endTime - node.startTime}ms`}
                  </div>
                )}
              </div>
              <div className="text-sm text-muted-foreground capitalize">
                {node.status}
              </div>
              {index < mockNodes.length - 1 && (
                <div className="w-8 h-px bg-border" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
