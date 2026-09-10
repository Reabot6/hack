import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Videos from './pages/Videos'
import Upload from './pages/Upload'
import Dashboard from './pages/Dashboard'
import AuthGate from './components/AuthGate'

export default function App() {
  return (
    <AuthGate><BrowserRouter>
      <Routes>
        <Route path="/" element={<Videos />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/dashboard/:videoId" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter></AuthGate>
  )
}
