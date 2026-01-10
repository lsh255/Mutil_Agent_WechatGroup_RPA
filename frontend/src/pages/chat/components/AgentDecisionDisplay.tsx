import { AgentDecision } from '@/types'

interface AgentDecisionDisplayProps {
  decision: AgentDecision
}

export default function AgentDecisionDisplay({ decision }: AgentDecisionDisplayProps) {
  const actionLabels: Record<string, string> = {
    write_report: '生成日报',
    update_ledger: '更新台账',
    save_message: '保存消息',
    continue: '继续监控',
  }

  return (
    <div className="p-3 bg-muted rounded-lg">
      <div className="text-xs text-muted-foreground mb-1">
        操作：{actionLabels[decision.action] || decision.action}
      </div>
      <div className="text-xs text-muted-foreground">
        原因：{decision.reasoning}
      </div>
      <div className="text-xs text-muted-foreground mt-1">
        时间：{new Date(decision.timestamp).toLocaleString()}
      </div>
    </div>
  )
}
