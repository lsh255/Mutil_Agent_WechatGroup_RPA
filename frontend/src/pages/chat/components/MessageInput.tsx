import { Send } from 'lucide-react'

interface MessageInputProps {
  value: string
  onChange: (value: string) => void
  onSend: (message: string) => void
  disabled: boolean
}

export default function MessageInput({ value, onChange, onSend, disabled }: MessageInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend(value)
    }
  }

  return (
    <div className="flex gap-2">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
        className="flex-1 min-h-[48px] max-h-32 px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none disabled:opacity-50"
        rows={1}
      />
      <button
        onClick={() => onSend(value)}
        disabled={disabled || !value.trim()}
        className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Send size={20} />
      </button>
    </div>
  )
}
