import { useChatStore } from '@/store/chatStore'

export default function TaskStatusCard() {
  const taskConfig = useChatStore((state) => state.taskConfig)

  if (!taskConfig) return null

  return (
    <div className="space-y-2">
      {taskConfig.workItems.map((item, index) => (
        <div key={index} className="p-3 bg-muted rounded-lg">
          <div className="font-medium text-sm mb-1">
            工作项目 {index + 1}
          </div>
          <div className="text-xs text-muted-foreground">
            地点：{item.location}
          </div>
          <div className="text-xs text-muted-foreground">
            人员：{item.personnel.join(', ')}
          </div>
          {item.content && (
            <div className="text-xs text-muted-foreground mt-1">
              {item.content}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
