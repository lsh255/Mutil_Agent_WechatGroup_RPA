import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface MetricData {
  time: string
  cpu: number
  memory: number
  disk: number
  network: number
}

export default function SystemMetrics() {
  const [metrics, setMetrics] = useState<MetricData[]>([])
  const [timeRange, setTimeRange] = useState('1h')

  useEffect(() => {
    const generateMockData = () => {
      const now = Date.now()
      const data: MetricData[] = []
      
      for (let i = 60; i >= 0; i--) {
        data.push({
          time: new Date(now - i * 60000).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          cpu: Math.random() * 40 + 20,
          memory: Math.random() * 30 + 40,
          disk: Math.random() * 10 + 50,
          network: Math.random() * 100,
        })
      }
      
      setMetrics(data)
    }

    generateMockData()
    const interval = setInterval(generateMockData, 5000)

    return () => clearInterval(interval)
  }, [])

  const currentMetrics = metrics[metrics.length - 1] || {
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0,
  }

  const metricCards = [
    {
      label: 'CPU使用率',
      value: currentMetrics.cpu.toFixed(1) + '%',
      color: 'text-blue-500',
    },
    {
      label: '内存使用率',
      value: currentMetrics.memory.toFixed(1) + '%',
      color: 'text-green-500',
    },
    {
      label: '磁盘使用率',
      value: currentMetrics.disk.toFixed(1) + '%',
      color: 'text-purple-500',
    },
    {
      label: '网络流量',
      value: currentMetrics.network.toFixed(1) + 'Mbps',
      color: 'text-orange-500',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">系统指标</h3>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="1h">最近1小时</option>
          <option value="6h">最近6小时</option>
          <option value="24h">最近24小时</option>
          <option value="7d">最近7天</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((card) => (
          <div key={card.label} className="p-4 bg-card border border-border rounded-lg">
            <div className="text-sm text-muted-foreground mb-1">{card.label}</div>
            <div className={`text-2xl font-bold ${card.color}`}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      <div className="p-6 bg-card border border-border rounded-lg">
        <h4 className="font-semibold mb-4">资源使用趋势</h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="time"
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: 'hsl(var(--muted-foreground))' }}
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '0.5rem',
                }}
              />
              <Line
                type="monotone"
                dataKey="cpu"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="CPU"
              />
              <Line
                type="monotone"
                dataKey="memory"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                name="内存"
              />
              <Line
                type="monotone"
                dataKey="disk"
                stroke="#a855f7"
                strokeWidth={2}
                dot={false}
                name="磁盘"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-card border border-border rounded-lg">
          <h4 className="font-semibold mb-4">Docker容器资源</h4>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">wechat-sandbox-1</span>
                <span className="text-sm text-muted-foreground">2.5%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '2.5%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">wechat-sandbox-2</span>
                <span className="text-sm text-muted-foreground">1.8%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: '1.8%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">orchestrator</span>
                <span className="text-sm text-muted-foreground">5.2%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-green-500 rounded-full" style={{ width: '5.2%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-sm">ollama</span>
                <span className="text-sm text-muted-foreground">45.6%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: '45.6%' }} />
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <h4 className="font-semibold mb-4">API调用统计</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm">今日总调用</span>
              <span className="font-medium">5,678</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">成功</span>
              <span className="font-medium text-green-500">5,654 (99.6%)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">失败</span>
              <span className="font-medium text-red-500">24 (0.4%)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">平均响应时间</span>
              <span className="font-medium">234ms</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
