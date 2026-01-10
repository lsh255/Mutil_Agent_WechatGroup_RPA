import { Routes, Route, Navigate } from 'react-router-dom'
import ChatPage from '@/pages/chat/ChatPage'
import AdminPage from '@/pages/admin/AdminPage'
import NotFound from '@/pages/NotFound'

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="/chat" element={<ChatPage />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
