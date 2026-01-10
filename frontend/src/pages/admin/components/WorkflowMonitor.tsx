import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Play, Pause, Square } from 'lucide-react'

interface WorkflowExecution {
  id: string
  status: 'running' | 'paused' | 'completed' | 'error'
  startTime: number
  endTime?: number
  currentNode: string
  error?: string
}

export default function WorkflowMonitor() {
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([])
  const [expandedWorkflow, setExpandedWorkflow] = useState<string | null>(null)

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await fetch('/api/agent/workflows')
        const data = await response.json()
        setWorkflows(data)
      } catch (error) {
        console.error('Failed to fetch workflows:', error)
      }
    }

    fetchWorkflows()
    const interval = setInterval(fetchWorkflows, 3000)

    return () => clearInterval(interval)
  }, [])

  const getStatusBadge = (status: string) => {
    const styles = {
      running: 'bg-blue-500',
      paused: 'bg-yellow-500',
      completed: 'bg-green-500',
      error: 'bg-red-500',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs text-white ${styles[status as keyof typeof styles]}`}>
        {status}
      </span>
    )
  }

  const handleAction = async (workflowId: string, action: 'pause' | 'resume' | 'stop') => {
    try {
      await fetch(`/api/agent/workflows/${workflowId}/${action}`, { method: 'POST' })
    } catch (error) {
      console.error('Failed to perform action:', error)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">工作流监控</h3>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="搜索工作流..."
            className="px-3 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <select className="px-3 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            <option value="">全部状态</option>
            <option value="running">运行中</option>
            <option value="paused">已暂停</option>
            <option value="completed">已完成</option>
            <option value="error">异常</option>
          </select>
        </div>
      </div>

      <div className="space-y-3">
        {workflows.map((workflow) => (
          <div key={workflow.id} className="border border-border rounded-lg overflow-hidden">
            <div
              className="flex items-center justify-between p-4 bg-card cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => setExpandedWorkflow(
                expandedWorkflow === workflow.id ? null : workflow.id
              )}
            >
              <div className="flex items-center gap-3">
                {expandedWorkflow === workflow.id ? (
                  <ChevronDown size={18} />
                ) : (
                  <ChevronRight size={18} />
                )}
                <div>
                  <div className="font-medium">{workflow.id}</div>
                  <div className="text-xs text-muted-foreground">
                    开始时间：{new Date(workflow.startTime).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getStatusBadge(workflow.status)}
                {workflow.status === 'running' && (
                  <div className="flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(workflow.id, 'pause')
                      }}
                      className="p-1 hover:bg-accent rounded transition-colors"
                    >
                      <Pause size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleAction(workflow.id, 'stop')
                      }}
                      className="p-1 hover:bg-accent rounded transition-colors"
                    >
                      <Square size={16} />
                    </button>
                  </div>
                )}
                {workflow.status === 'paused' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleAction(workflow.id, 'resume')
                    }}
                    className="p-1 hover:bg-accent rounded transition-colors"
                  >
                    <Play size={16} />
                  </button>
                )}
              </div>
            </div>

            {expandedWorkflow === workflow.id && (
              <div className="p-4 bg-muted/50 border-t border-border">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">当前节点</span>
                    <span className="text-sm font-medium">{workflow.currentNode}</span>
                  </div>
                  {workflow.endTime && (
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">结束时间</span>
                      <span className="text-sm">{new Date(workflow.endTime).toLocaleString()}</span>
                    </div>
                  )}
                  {workflow.endTime && (
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">执行时长</span>
                      <span className="text-sm">{workflow.endTime - workflow.startTime}ms</span>
                    </div>
                  )}
                  {workflow.error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded">
                      <div className="text-sm font-medium text-red-700">错误</div>
                      <div className="text-sm text-red-600">{workflow.error}</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
