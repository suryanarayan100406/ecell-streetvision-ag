import { useState, useEffect, useRef } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { MapPin, BarChart3, FileText, Trophy, Menu, X } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import MapView from './pages/MapView'
import Complaints from './pages/Complaints'
import Leaderboard from './pages/Leaderboard'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
export const api = axios.create({ baseURL: `${API_BASE}/api` })

const NAV = [
  { path: '/', label: 'Dashboard', icon: BarChart3 },
  { path: '/map', label: 'Live Map', icon: MapPin },
  { path: '/complaints', label: 'Complaints', icon: FileText },
  { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
]

export default function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen hero-gradient">
      {/* Nav */}
      <header className="sticky top-0 z-50 glass-card mx-4 mt-4 px-6 py-3 flex items-center justify-between" style={{ borderRadius: 16 }}>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <span className="text-lg font-bold text-white">P</span>
          </div>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold text-white leading-tight">Pothole Intelligence</h1>
            <p className="text-[10px] text-indigo-300/60 uppercase tracking-widest">Chhattisgarh Roads</p>
          </div>
        </div>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-6">
          {NAV.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span className="flex items-center gap-2"><Icon size={14} />{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Mobile toggle */}
        <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 text-gray-400">
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Mobile Nav */}
      {menuOpen && (
        <div className="md:hidden glass-card mx-4 mt-2 p-4 space-y-2" style={{ borderRadius: 16 }}>
          {NAV.map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} end={path === '/'} onClick={() => setMenuOpen(false)}
              className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl text-sm ${isActive ? 'bg-indigo-500/10 text-white' : 'text-gray-400'}`}>
              <Icon size={16} />{label}
            </NavLink>
          ))}
        </div>
      )}

      {/* Routes */}
      <main className="p-4 max-w-screen-2xl mx-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/complaints" element={<Complaints />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-xs text-gray-600">
        <p>CHIPS AIML Hackathon | PS-02 | Autonomous Pothole Intelligence System</p>
        <p className="mt-1">Powered by satellite + drone + CCTV + crowdsource intelligence</p>
      </footer>
    </div>
  )
}
