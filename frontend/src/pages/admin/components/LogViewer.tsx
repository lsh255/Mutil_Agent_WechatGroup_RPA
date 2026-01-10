import { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronUp, X, Search } from 'lucide-react'

interface LogEntry {
  timestamp: number
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  message: string
  source?: string
}

export default function LogViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState<'all' | 'error'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [expanded, setExpanded] = useState(false)
  const logContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const generateMockLogs = () => {
      const levels: Array<'INFO' | 'WARN' | 'ERROR' | 'DEBUG'> = ['INFO', 'INFO', 'INFO', 'WARN', 'DEBUG', 'ERROR']
      const sources = ['orchestrator', 'sandbox', 'agent', 'api']
      const messages = [
        '工作流执行成功',
        '沙盒实例已启动',
        '收到新的群聊消息',
        'Agent决策完成',
        'API调用成功',
        '连接超时，正在重试',
        '内存使用率过高',
        '处理请求失败',
      ]

      const newLog: LogEntry = {
        timestamp: Date.now(),
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
        source: sources[Math.floor(Math.random() * sources.length)],
      }

      setLogs((prev) => [...prev.slice(-99), newLog])
    }

    const interval = setInterval(generateMockLogs, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-500 bg-red-50 dark:bg-red-950'
      case 'WARN':
        return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-950'
      case 'INFO':
        return 'text-blue-500 bg-blue-50 dark:bg-blue-950'
      case 'DEBUG':
        return 'text-gray-500 bg-gray-50 dark:bg-gray-950'
      default:
        return 'text-gray-500'
    }
  }

  const filteredLogs = logs.filter((log) => {
    if (filter === 'error' && log.level !== 'ERROR') return false
    if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent rounded-md transition-colors"
      >
        <ChevronUp size={16} />
        日志查看器
      </button>
    )
  }

  return (
    <div className="flex flex-col h-80">
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => setExpanded(false)}
          className="flex items-center gap-2 text-sm hover:bg-accent rounded px-2 py-1"
        >
          <ChevronDown size={16} />
          日志查看器
        </button>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter(filter === 'all' ? 'error' : 'all')}
            className={`px-2 py-1 text-xs rounded ${
              filter === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' : 'bg-muted'
            }`}
          >
            {filter === 'error' ? '仅错误' : '全部'}
          </button>
        </div>
      </div>

      <div className="relative mb-2">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
        <input
          type="text"
          placeholder="搜索日志..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-8 pr-8 py-1 text-xs border border-input bg-background rounded focus:outline-none focus:ring-1 focus:ring-ring"
        />
        {searchTerm && (
          <button
            onClick={() => setSearchTerm('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto p-2 bg-muted/50 rounded text-xs font-mono space-y-1"
      >
        {filteredLogs.map((log, index) => (
          <div
            key={index}
            className={`flex gap-2 px-2 py-1 rounded ${getLevelColor(log.level)}`}
          >
            <span className="opacity-70">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className="font-semibold">{log.level}</span>
            {log.source && <span className="opacity-70">[{log.source}]</span>}
            <span className="flex-1">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
