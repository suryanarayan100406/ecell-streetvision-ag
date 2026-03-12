import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Overview from './pages/Overview'
import Satellites from './pages/Satellites'
import Drones from './pages/Drones'
import CCTV from './pages/CCTV'
import DataSources from './pages/DataSources'
import Pipeline from './pages/Pipeline'
import Review from './pages/Review'
import Models from './pages/Models'
import Scheduler from './pages/Scheduler'
import Settings from './pages/Settings'
import Logs from './pages/Logs'
import Login from './pages/Login'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('admin_token'))
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('admin_user') || 'null'))

  const handleLogin = (accessToken, userData) => {
    localStorage.setItem('admin_token', accessToken)
    localStorage.setItem('admin_user', JSON.stringify(userData))
    setToken(accessToken)
    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    setToken(null)
    setUser(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="flex h-screen bg-surface-900">
      <Sidebar user={user} onLogout={handleLogout} />
      <main className="flex-1 overflow-y-auto p-6">
        <Routes>
          <Route path="/" element={<Overview token={token} />} />
          <Route path="/satellites" element={<Satellites token={token} />} />
          <Route path="/drones" element={<Drones token={token} />} />
          <Route path="/cctv" element={<CCTV token={token} />} />
          <Route path="/data-sources" element={<DataSources token={token} />} />
          <Route path="/pipeline" element={<Pipeline token={token} />} />
          <Route path="/review" element={<Review token={token} />} />
          <Route path="/models" element={<Models token={token} />} />
          <Route path="/scheduler" element={<Scheduler token={token} />} />
          <Route path="/settings" element={<Settings token={token} />} />
          <Route path="/logs" element={<Logs token={token} />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}
