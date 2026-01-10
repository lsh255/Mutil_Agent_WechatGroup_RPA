import { useEffect } from 'react'
import { Activity, Server, FileText, AlertCircle } from 'lucide-react'
import { useSandboxStore } from '@/store/sandboxStore'
import { useAgentStore } from '@/store/agentStore'

export default function Dashboard() {
  const instances = useSandboxStore((state) => state.instances)
  const setInstances = useSandboxStore((state) => state.setInstances)
  const agentState = useAgentStore((state) => state.agentState)
  const setAgentState = useAgentStore((state) => state.setAgentState)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const instancesResponse = await fetch('/api/sandbox/instances')
        const instancesData = await instancesResponse.json()
        setInstances(instancesData)

        const agentResponse = await fetch('/api/agent/status')
        const agentData = await agentResponse.json()
        setAgentState(agentData)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      }
    }

    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000)

    return () => clearInterval(interval)
  }, [setInstances, setAgentState])

  const runningInstances = instances.filter((i) => i.status === 'running').length
  const activeWorkflows = agentState?.status === 'running' ? 1 : 0
  const errorCount = instances.filter((i) => i.status === 'error').length

  const stats = [
    {
      label: '运行中沙盒',
      value: runningInstances,
      icon: Server,
      color: 'text-green-500',
    },
    {
      label: '活跃工作流',
      value: activeWorkflows,
      icon: Activity,
      color: 'text-blue-500',
    },
    {
      label: '总实例数',
      value: instances.length,
      icon: Server,
      color: 'text-purple-500',
    },
    {
      label: '异常实例',
      value: errorCount,
      icon: AlertCircle,
      color: 'text-red-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.label}
              className="p-6 bg-card border border-border rounded-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">{stat.label}</span>
                <Icon size={20} className={stat.color} />
              </div>
              <div className="text-2xl font-bold">{stat.value}</div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 bg-card border border-border rounded-lg">
          <h3 className="text-lg font-semibold mb-4">系统状态</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">系统运行时间</span>
              <span className="font-medium">12小时30分</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">处理消息总数</span>
              <span className="font-medium">1,234</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">API调用次数</span>
              <span className="font-medium">5,678</span>
            </div>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <h3 className="text-lg font-semibold mb-4">近期活动</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 mt-2 rounded-full bg-green-500" />
              <div>
                <div className="text-sm font-medium">沙盒实例启动成功</div>
                <div className="text-xs text-muted-foreground">2分钟前</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 mt-2 rounded-full bg-blue-500" />
              <div>
                <div className="text-sm font-medium">工作流执行完成</div>
                <div className="text-xs text-muted-foreground">5分钟前</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 mt-2 rounded-full bg-yellow-500" />
              <div>
                <div className="text-sm font-medium">群聊消息监控启动</div>
                <div className="text-xs text-muted-foreground">10分钟前</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
