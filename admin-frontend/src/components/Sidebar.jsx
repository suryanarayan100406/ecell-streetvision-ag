import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Satellite, Plane, Camera, Database,
  GitBranch, Eye, Brain, Clock, Settings, FileText, LogOut
} from 'lucide-react'

const NAV_ITEMS = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/satellites', label: 'Satellite Sources', icon: Satellite },
  { path: '/drones', label: 'Drone Missions', icon: Plane },
  { path: '/cctv', label: 'CCTV Cameras', icon: Camera },
  { path: '/data-sources', label: 'Data Sources', icon: Database },
  { path: '/pipeline', label: 'Pipeline Monitor', icon: GitBranch },
  { path: '/review', label: 'Detection Review', icon: Eye },
  { path: '/models', label: 'Model Management', icon: Brain },
  { path: '/scheduler', label: 'Scheduler', icon: Clock },
  { path: '/settings', label: 'System Settings', icon: Settings },
  { path: '/logs', label: 'Logs & Audit', icon: FileText },
]

export default function Sidebar({ user, onLogout }) {
  return (
    <aside className="w-64 h-screen bg-surface-850 border-r border-primary-800/30 flex flex-col overflow-y-auto">
      {/* Logo */}
      <div className="p-5 border-b border-primary-800/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <span className="text-lg font-bold text-white">P</span>
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Pothole Intel</h1>
            <p className="text-[10px] text-primary-300/60 uppercase tracking-widest">Admin Panel</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-primary-600/20 text-primary-300 border border-primary-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-primary-800/20">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-white">{user?.name || 'Admin'}</p>
            <p className="text-[10px] text-gray-500">{user?.role}</p>
          </div>
          <button onClick={onLogout} className="p-2 rounded-lg hover:bg-red-500/10 text-gray-400 hover:text-red-400 transition-colors">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
