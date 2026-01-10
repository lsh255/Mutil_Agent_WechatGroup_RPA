import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Message } from '@/types'

interface ChatContainerProps {
  messages: Message[]
}

export default function ChatContainer({ messages }: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div ref={scrollRef} className="h-full overflow-y-auto p-6 space-y-4">
      {messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-muted-foreground">
          <p>开始对话吧！您可以发送任务配置或群聊监控指令。</p>
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-2xl rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-foreground'
            }`}
          >
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {message.role === 'assistant' ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : (
                <p>{message.content}</p>
              )}
            </div>
            <div className="mt-1 text-xs opacity-70">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
