import { useState, useEffect, useRef } from 'react'
import { Play, Square, RefreshCw, ExternalLink, Monitor, Settings, AlertCircle, CheckCircle2, XCircle, Minimize2 } from 'lucide-react'
import { useSandboxStore } from '@/store/sandboxStore'
import { useToast } from '@/hooks/use-toast'

interface ROIConfig {
  left: number
  top: number
  right: number
  bottom: number
}

interface LogEntry {
  timestamp: number
  level: 'info' | 'warn' | 'error'
  message: string
}

interface ProducerStatus {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error'
}

export default function SandboxMonitor() {
  const instances = useSandboxStore((state) => state.instances)
  const setInstances = useSandboxStore((state) => state.setInstances)
  const updateInstance = useSandboxStore((state) => state.updateInstance)

  const [selectedInstance, setSelectedInstance] = useState<string | null>(null)
  const [roiConfig, setRoiConfig] = useState<ROIConfig>({ left: 100, top: 200, right: 500, bottom: 800 })
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isROIModalOpen, setIsROIModalOpen] = useState(false)
  const [screenshotUrl, setScreenshotUrl] = useState<string>('')
  const [currentPreset, setCurrentPreset] = useState<'receive_area' | 'send_area'>('receive_area')
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [currentROI, setCurrentROI] = useState<ROIConfig>({ left: 0, top: 0, right: 0, bottom: 0 })
  const [producerStatus, setProducerStatus] = useState<ProducerStatus[]>([
    { id: 'producer1', name: 'Producer1 (观察者)', status: 'running' },
    { id: 'producer2', name: 'Producer2 (内容获取)', status: 'running' },
    { id: 'queue', name: '消息队列 (Redis)', status: 'running' },
  ])

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    const fetchInstances = async () => {
      try {
        const response = await fetch('/api/sandbox/instances')
        const data = await response.json()
        setInstances(data)
      } catch (error) {
        console.error('Failed to fetch sandbox instances:', error)
      }
    }

    fetchInstances()
    const interval = setInterval(fetchInstances, 3000)

    return () => clearInterval(interval)
  }, [setInstances])

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch('/api/sandbox/logs')
        const data = await response.json()
        setLogs(data)
      } catch (error) {
        console.error('Failed to fetch logs:', error)
      }
    }

    fetchLogs()
    const interval = setInterval(fetchLogs, 2000)

    return () => clearInterval(interval)
  }, [])

  const handleStart = async (id: string) => {
    try {
      await fetch(`/api/sandbox/start/${id}`, { method: 'POST' })
      updateInstance(id, { status: 'running' })
      toast({ title: '启动成功', description: `实例 ${id} 已启动` })
    } catch (error) {
      console.error('Failed to start instance:', error)
      toast({ title: '启动失败', variant: 'destructive' })
    }
  }

  const handleStop = async (id: string) => {
    try {
      await fetch(`/api/sandbox/stop/${id}`, { method: 'POST' })
      updateInstance(id, { status: 'stopped' })
      toast({ title: '停止成功', description: `实例 ${id} 已停止` })
    } catch (error) {
      console.error('Failed to stop instance:', error)
      toast({ title: '停止失败', variant: 'destructive' })
    }
  }

  const handleRestart = async (id: string) => {
    try {
      await fetch(`/api/sandbox/restart/${id}`, { method: 'POST' })
      updateInstance(id, { status: 'running' })
      toast({ title: '重启成功', description: `实例 ${id} 已重启` })
    } catch (error) {
      console.error('Failed to restart instance:', error)
      toast({ title: '重启失败', variant: 'destructive' })
    }
  }

  const handleUpdateROI = async () => {
    try {
      const response = await fetch('/api/sandbox/roi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roiConfig),
      })
      if (response.ok) {
        toast({ title: '配置已更新', description: '监控区域配置已保存' })
      } else {
        toast({ title: '配置更新失败', variant: 'destructive' })
      }
    } catch (error) {
      console.error('Failed to update ROI:', error)
      toast({ title: '配置更新失败', variant: 'destructive' })
    }
  }

  const handleCaptureScreen = async () => {
    try {
      const response = await fetch('/api/sandbox/screenshot')
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        window.open(url, '_blank')
        toast({ title: '截屏成功' })
      } else {
        toast({ title: '截屏失败', variant: 'destructive' })
      }
    } catch (error) {
      console.error('Failed to capture screen:', error)
      toast({ title: '截屏失败', variant: 'destructive' })
    }
  }

  const handleRefreshScreenshot = async () => {
    try {
      const response = await fetch('/api/sandbox/screenshot')
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        setScreenshotUrl(url)
        toast({ title: '截图已刷新' })
      }
    } catch (error) {
      console.error('Failed to refresh screenshot:', error)
      toast({ title: '截图刷新失败', variant: 'destructive' })
    }
  }

  const handleSaveROI = async () => {
    try {
      const response = await fetch('/api/sandbox/roi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentROI),
      })
      if (response.ok) {
        setRoiConfig(currentROI)
        setIsROIModalOpen(false)
        toast({ title: 'ROI配置已保存' })
      } else {
        toast({ title: '保存失败', variant: 'destructive' })
      }
    } catch (error) {
      console.error('Failed to save ROI:', error)
      toast({ title: '保存失败', variant: 'destructive' })
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY

    setIsDragging(true)
    setDragStart({ x, y })
    setCurrentROI({ left: x, top: y, right: x, bottom: y })
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY

    setCurrentROI({
      left: Math.min(dragStart.x, x),
      top: Math.min(dragStart.y, y),
      right: Math.max(dragStart.x, x),
      bottom: Math.max(dragStart.y, y),
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const selectPreset = (preset: 'receive_area' | 'send_area') => {
    setCurrentPreset(preset)
    if (preset === 'receive_area') {
      setCurrentROI({ left: 100, top: 200, right: 500, bottom: 800 })
    } else {
      setCurrentROI({ left: 100, top: 900, right: 500, bottom: 1000 })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'stopped':
        return <XCircle className="w-5 h-5 text-gray-500" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return '运行中'
      case 'stopped':
        return '已停止'
      case 'error':
        return '异常'
      case 'initializing':
        return '初始化中'
      default:
        return status
    }
  }

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case 'warn':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">沙盒实例监控</h3>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          新建实例
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-center gap-2 mb-4">
              <Monitor className="w-5 h-5" />
              <h4 className="font-medium">远程桌面 - {selectedInstance || '选择实例'}</h4>
            </div>

            <div className="space-y-3 mb-4">
              {instances.slice(0, 3).map((instance) => (
                <div
                  key={instance.id}
                  onClick={() => setSelectedInstance(instance.id)}
                  className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedInstance === instance.id
                      ? 'bg-primary/10 border-2 border-primary'
                      : 'bg-muted hover:bg-muted/80'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(instance.status)}
                    <div>
                      <div className="font-medium">{instance.name}</div>
                      <div className="text-xs text-muted-foreground">{instance.id}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{getStatusText(instance.status)}</span>
                    <span className="text-xs text-muted-foreground">VNC: {instance.vncPort}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="aspect-video bg-black rounded-lg overflow-hidden">
              {selectedInstance ? (
                <iframe
                  src={`http://localhost:${instances.find(i => i.id === selectedInstance)?.vncPort || 6080}/vnc.html`}
                  className="w-full h-full border-0"
                  title="VNC Remote Desktop"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <Monitor className="w-16 h-16" />
                </div>
              )}
            </div>

            <div className="flex gap-2 mt-4">
              {selectedInstance && (
                <>
                  <button
                    onClick={() => handleStart(selectedInstance)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
                  >
                    <Play size={16} />
                    启动
                  </button>
                  <button
                    onClick={() => handleStop(selectedInstance)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                  >
                    <Square size={16} />
                    停止
                  </button>
                  <button
                    onClick={() => handleRestart(selectedInstance)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
                  >
                    <RefreshCw size={16} />
                    重启
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5" />
              <h4 className="font-medium">服务状态</h4>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {producerStatus.map((producer) => (
                <div key={producer.id} className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(producer.status)}
                    <span className="text-sm font-medium">{producer.name}</span>
                  </div>
                  <div className="text-lg font-bold">{getStatusText(producer.status)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <h4 className="font-medium">实时日志</h4>
              </div>
              <button
                onClick={() => setLogs([])}
                className="px-3 py-1 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                清空
              </button>
            </div>

            <div className="h-48 overflow-y-auto bg-black text-green-400 p-3 rounded-lg font-mono text-sm">
              {logs.length === 0 ? (
                <div className="text-gray-400">等待日志...</div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2 mb-1">
                    {getLogIcon(log.level)}
                    <span className="text-xs text-gray-500">{formatTimestamp(log.timestamp)}</span>
                    <span>{log.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-4 bg-card border border-border rounded-lg">
            <div className="flex items-center gap-2 mb-4">
              <Monitor className="w-5 h-5" />
              <h4 className="font-medium">监控区域配置 (ROI)</h4>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Left</label>
                  <input
                    type="number"
                    value={roiConfig.left}
                    onChange={(e) => setRoiConfig({ ...roiConfig, left: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Top</label>
                  <input
                    type="number"
                    value={roiConfig.top}
                    onChange={(e) => setRoiConfig({ ...roiConfig, top: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Right</label>
                  <input
                    type="number"
                    value={roiConfig.right}
                    onChange={(e) => setRoiConfig({ ...roiConfig, right: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Bottom</label>
                  <input
                    type="number"
                    value={roiConfig.bottom}
                    onChange={(e) => setRoiConfig({ ...roiConfig, bottom: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                  />
                </div>
              </div>

              <button
                onClick={handleUpdateROI}
                className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                更新监控区域
              </button>

              <button
                onClick={handleCaptureScreen}
                className="w-full px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                截屏预览
              </button>

              <button
                onClick={() => setIsROIModalOpen(true)}
                className="w-full px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                打开ROI选择器
              </button>
            </div>

            <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-500 rounded">
              <h5 className="text-sm font-medium text-yellow-800 mb-2">使用说明</h5>
              <ul className="text-xs text-yellow-700 space-y-1">
                <li>• 通过左侧远程桌面操作Linux微信登录</li>
                <li>• 点击"打开ROI选择器"配置监控区域</li>
                <li>• 选择预设区域：发送区域/接收区域</li>
                <li>• VNC密码: vnc123</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {isROIModalOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold">选择监控区域 (ROI)</h2>
              <button
                onClick={() => setIsROIModalOpen(false)}
                className="p-2 hover:bg-muted rounded-md transition-colors"
              >
                <Minimize2 size={24} />
              </button>
            </div>

            <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
              <p className="text-sm text-blue-800">
                <strong>操作提示：</strong>选择预设区域或直接在图片上拖拽鼠标选择区域
              </p>
            </div>

            <div className="flex gap-2 mb-4">
              <button
                onClick={() => selectPreset('receive_area')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  currentPreset === 'receive_area'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                接收区域
              </button>
              <button
                onClick={() => selectPreset('send_area')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  currentPreset === 'send_area'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                发送区域
              </button>
              <button
                onClick={handleRefreshScreenshot}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                刷新截图
              </button>
            </div>

            <div className="relative mb-4 bg-black rounded-lg overflow-hidden">
              {screenshotUrl ? (
                <canvas
                  ref={canvasRef}
                  width={1920}
                  height={1080}
                  className="w-full cursor-crosshair"
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                />
              ) : (
                <div className="aspect-video flex items-center justify-center text-gray-400">
                  <ExternalLink className="w-16 h-16" />
                </div>
              )}
            </div>

            <div className="grid grid-cols-4 gap-3 mb-4">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Left (左)</label>
                <input
                  type="number"
                  value={Math.round(currentROI.left)}
                  onChange={(e) => setCurrentROI({ ...currentROI, left: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Top (上)</label>
                <input
                  type="number"
                  value={Math.round(currentROI.top)}
                  onChange={(e) => setCurrentROI({ ...currentROI, top: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Right (右)</label>
                <input
                  type="number"
                  value={Math.round(currentROI.right)}
                  onChange={(e) => setCurrentROI({ ...currentROI, right: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Bottom (下)</label>
                <input
                  type="number"
                  value={Math.round(currentROI.bottom)}
                  onChange={(e) => setCurrentROI({ ...currentROI, bottom: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-muted border border-border rounded-md text-sm"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setIsROIModalOpen(false)}
                className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSaveROI}
                className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                保存配置
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
