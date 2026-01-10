import { useState } from 'react'
import { LayoutDashboard, Server, Activity, FileText, List, Settings, ChevronLeft } from 'lucide-react'
import Dashboard from './components/Dashboard'
import SandboxMonitor from './components/SandboxMonitor'
import AgentMonitor from './components/AgentMonitor'
import WorkflowMonitor from './components/WorkflowMonitor'
import InstanceList from './components/InstanceList'
import SystemMetrics from './components/SystemMetrics'
import LogViewer from './components/LogViewer'

type TabType = 'dashboard' | 'sandbox' | 'agent' | 'workflow' | 'instances' | 'metrics' | 'logs'

const tabs = [
  { id: 'dashboard', label: '概览', icon: LayoutDashboard },
  { id: 'sandbox', label: '沙盒监控', icon: Server },
  { id: 'agent', label: 'Agent状态', icon: Activity },
  { id: 'workflow', label: '工作流', icon: FileText },
  { id: 'instances', label: '实例管理', icon: List },
  { id: 'metrics', label: '系统指标', icon: Settings },
]

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />
      case 'sandbox':
        return <SandboxMonitor />
      case 'agent':
        return <AgentMonitor />
      case 'workflow':
        return <WorkflowMonitor />
      case 'instances':
        return <InstanceList />
      case 'metrics':
        return <SystemMetrics />
      default:
        return null
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <aside
        className={`${sidebarCollapsed ? 'w-16' : 'w-64'} border-r border-border bg-card transition-all duration-300 flex flex-col`}
      >
        <div className="p-4 border-b border-border flex items-center justify-between">
          {!sidebarCollapsed && (
            <h2 className="text-lg font-semibold">管理控制台</h2>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <ChevronLeft
              size={20}
              className={`transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`}
            />
          </button>
        </div>

        <nav className="flex-1 p-2 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-accent'
                }`}
              >
                <Icon size={18} />
                {!sidebarCollapsed && <span>{tab.label}</span>}
              </button>
            )
          })}
        </nav>

        {!sidebarCollapsed && (
          <div className="p-4 border-t border-border">
            <LogViewer />
          </div>
        )}
      </aside>

      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="border-b border-border bg-card px-6 py-4">
          <h1 className="text-xl font-semibold">
            {tabs.find((t) => t.id === activeTab)?.label}
          </h1>
        </header>

        <div className="flex-1 overflow-auto p-6">{renderContent()}</div>
      </main>
    </div>
  )
}
