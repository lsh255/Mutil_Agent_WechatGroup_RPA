import { useState } from 'react'
import { Settings, RefreshCw } from 'lucide-react'
import ChatContainer from './components/ChatContainer'
import MessageInput from './components/MessageInput'
import TaskStatusCard from './components/TaskStatusCard'
import AgentDecisionDisplay from './components/AgentDecisionDisplay'
import { useChatStore } from '@/store/chatStore'
import { triggerWorkflow } from '@/services/orchestrator'

export default function ChatPage() {
  const [inputValue, setInputValue] = useState('')
  const messages = useChatStore((state) => state.messages)
  const isProcessing = useChatStore((state) => state.isProcessing)
  const taskConfig = useChatStore((state) => state.taskConfig)
  const lastAgentDecision = useChatStore((state) => state.lastAgentDecision)
  const addMessage = useChatStore((state) => state.addMessage)
  const setProcessing = useChatStore((state) => state.setProcessing)

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isProcessing) return

    setInputValue('')
    setProcessing(true)

    addMessage({
      role: 'user',
      content: message,
    })

    try {
      await triggerWorkflow({ userMessage: message })
    } catch (error) {
      console.error('Failed to trigger workflow:', error)
      addMessage({
        role: 'assistant',
        content: '抱歉，处理您的请求时出现错误，请稍后重试。',
      })
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <aside className="w-64 border-r border-border bg-card p-4">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">任务状态</h2>
          {taskConfig && <TaskStatusCard />}
        </div>
        
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">最近决策</h2>
          {lastAgentDecision && <AgentDecisionDisplay decision={lastAgentDecision} />}
        </div>

        <div className="space-y-2">
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent rounded-md transition-colors">
            <Settings size={16} />
            设置
          </button>
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-accent rounded-md transition-colors">
            <RefreshCw size={16} />
            清空对话
          </button>
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <header className="border-b border-border bg-card px-6 py-4">
          <h1 className="text-xl font-semibold">微信群自动化AI Agent</h1>
        </header>

        <div className="flex-1 overflow-hidden">
          <ChatContainer messages={messages} />
        </div>

        <div className="border-t border-border bg-card p-4">
          <MessageInput
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSendMessage}
            disabled={isProcessing}
          />
        </div>
      </main>
    </div>
  )
}
