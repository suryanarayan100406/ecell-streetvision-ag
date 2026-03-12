import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts'
import { AlertTriangle, CheckCircle, FileText, MapPin, Activity } from 'lucide-react'
import api from '../services/api'

const STATUS_COLORS = { HEALTHY: 'healthy', DEGRADED: 'degraded', ERROR: 'error', INACTIVE: 'inactive' }

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
          <p className={`text-3xl font-bold ${color}`}>{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-xl bg-${color === 'text-white' ? 'primary' : color.replace('text-', '')}-500/10`}>
          <Icon size={20} className={color} />
        </div>
      </div>
    </div>
  )
}

function HealthGrid({ components }) {
  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-white mb-4">System Health</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        {components.map((c, i) => (
          <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] transition-colors cursor-pointer">
            <span className={`status-dot ${STATUS_COLORS[c.status] || 'inactive'}`}></span>
            <span className="text-xs text-gray-300 truncate">{c.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ActivityFeed({ events }) {
  const typeColors = {
    DETECTION: 'text-amber-400',
    COMPLAINT_FILED: 'text-green-400',
    ESCALATION: 'text-purple-400',
    REPAIR_VERIFIED: 'text-blue-400',
  }

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-white mb-4">Activity Feed</h3>
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-white/[0.03] transition-colors">
            <Activity size={14} className={typeColors[e.event_type] || 'text-gray-400'} />
            <div className="flex-1">
              <p className="text-xs text-gray-300">{e.description}</p>
              <p className="text-[10px] text-gray-600 mt-0.5">{new Date(e.timestamp).toLocaleString()}</p>
            </div>
          </div>
        ))}
        {events.length === 0 && <p className="text-xs text-gray-600 text-center py-4">No recent activity</p>}
      </div>
    </div>
  )
}

export default function Overview({ token }) {
  const [overview, setOverview] = useState(null)
  const [events, setEvents] = useState([])
  const [chartData, setChartData] = useState([])

  useEffect(() => {
    fetchOverview()
    fetchActivity()
    const interval = setInterval(() => { fetchOverview(); fetchActivity() }, 15000)
    return () => clearInterval(interval)
  }, [])

  const fetchOverview = async () => {
    try {
      const { data } = await api.get('/admin/overview')
      setOverview(data)
    } catch (err) {
      console.error('Failed to fetch overview', err)
    }
  }

  const fetchActivity = async () => {
    try {
      const { data } = await api.get('/admin/activity-feed?limit=50')
      setEvents(data)
      // Build chart data from events
      const hourly = {}
      data.forEach(e => {
        const h = new Date(e.timestamp).getHours()
        hourly[h] = (hourly[h] || 0) + 1
      })
      setChartData(Object.entries(hourly).map(([h, c]) => ({ hour: `${h}:00`, count: c })))
    } catch (err) {
      console.error('Failed to fetch activity', err)
    }
  }

  const openComplaints = overview?.open_complaints || {}
  const totalOpen = Object.values(openComplaints).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">System Overview</h2>
        <p className="text-sm text-gray-400 mt-1">Real-time health and metrics for all pipeline components</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={MapPin} label="Total Potholes" value={overview?.total_potholes || 0} color="text-white" sub="All-time detected" />
        <StatCard icon={AlertTriangle} label="Open Complaints" value={totalOpen} color="text-amber-400" sub={`L0: ${openComplaints.level_0 || 0} | L1: ${openComplaints.level_1 || 0} | L2: ${openComplaints.level_2 || 0} | L3: ${openComplaints.level_3 || 0}`} />
        <StatCard icon={FileText} label="Filed Today" value={overview?.complaints_filed_today || 0} color="text-green-400" />
        <StatCard icon={CheckCircle} label="Repairs (Month)" value={overview?.verified_repairs_month || 0} color="text-blue-400" />
      </div>

      {/* Health Grid */}
      <HealthGrid components={overview?.component_health || []} />

      {/* Charts + Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Detections Per Hour (Last 24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1e1b2e', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 12 }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ActivityFeed events={events} />
      </div>
    </div>
  )
}
