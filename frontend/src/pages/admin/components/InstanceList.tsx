import { useState, useEffect } from 'react'
import { Search, Plus, Trash2, Edit } from 'lucide-react'

interface Instance {
  id: string
  name: string
  status: 'running' | 'stopped' | 'error'
  containerId?: string
  port: number
  createdAt: number
}

export default function InstanceList() {
  const [instances, setInstances] = useState<Instance[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    const fetchInstances = async () => {
      try {
        const response = await fetch('/api/sandbox/instances')
        const data = await response.json()
        setInstances(data)
      } catch (error) {
        console.error('Failed to fetch instances:', error)
      }
    }

    fetchInstances()
    const interval = setInterval(fetchInstances, 5000)

    return () => clearInterval(interval)
  }, [])

  const filteredInstances = instances.filter((instance) =>
    instance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    instance.id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500'
      case 'stopped':
        return 'bg-gray-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
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
      default:
        return status
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个实例吗？')) return

    try {
      await fetch(`/api/sandbox/instances/${id}`, { method: 'DELETE' })
      setInstances(instances.filter((i) => i.id !== id))
    } catch (error) {
      console.error('Failed to delete instance:', error)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">实例管理</h3>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          <Plus size={16} />
          新建实例
        </button>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          <input
            type="text"
            placeholder="搜索实例..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">实例名称</th>
              <th className="px-4 py-3 text-left text-sm font-medium">ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium">端口</th>
              <th className="px-4 py-3 text-left text-sm font-medium">容器ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium">创建时间</th>
              <th className="px-4 py-3 text-right text-sm font-medium">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredInstances.map((instance) => (
              <tr key={instance.id} className="hover:bg-muted/50">
                <td className="px-4 py-3 font-medium">{instance.name}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{instance.id}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(instance.status)}`} />
                    <span className="text-sm">{getStatusText(instance.status)}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">{instance.port}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">
                  {instance.containerId || '-'}
                </td>
                <td className="px-4 py-3 text-sm">
                  {new Date(instance.createdAt).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-2">
                    <button className="p-1 hover:bg-accent rounded transition-colors">
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(instance.id)}
                      className="p-1 hover:bg-accent rounded transition-colors text-red-500"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredInstances.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            没有找到实例
          </div>
        )}
      </div>
    </div>
  )
}
