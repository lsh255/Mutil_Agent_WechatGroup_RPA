import { useState, useCallback } from 'react'

export interface Toast {
  id: string
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
  duration?: number
}

let toastCount = 0

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback(
    ({ title, description, variant = 'default', duration = 3000 }: Omit<Toast, 'id'>) => {
      const id = `toast-${toastCount++}`
      const newToast: Toast = { id, title, description, variant, duration }

      setToasts((prev) => [...prev, newToast])

      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, duration)
      }

      return id
    },
    []
  )

  const dismiss = useCallback((toastId?: string) => {
    setToasts((prev) => {
      if (toastId) {
        return prev.filter((t) => t.id !== toastId)
      }
      return []
    })
  }, [])

  return {
    toast,
    dismiss,
    toasts,
  }
}
