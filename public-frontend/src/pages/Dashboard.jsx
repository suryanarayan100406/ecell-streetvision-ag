import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area } from 'recharts'
import { MapPin, AlertTriangle, FileText, CheckCircle, TrendingUp } from 'lucide-react'
import { api } from '../App'

const SEVERITY_COLORS = { Critical: '#ef4444', High: '#f59e0b', Medium: '#eab308', Low: '#22c55e' }

function StatCard({ icon: Icon, label, value, color, delay }) {
  return (
    <div className="glass-card p-6 animate-in" style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">{label}</p>
          <p className={`stat-value ${color}`}>{value}</p>
        </div>
        <div className="p-3 rounded-2xl" style={{ background: `${color === 'text-white' ? 'rgba(99,102,241,0.1)' : 'rgba(255,255,255,0.05)'}` }}>
          <Icon size={22} className={color} style={{ opacity: 0.8 }} />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [highways, setHighways] = useState([])

  useEffect(() => {
    api.get('/public/analytics/summary').then(r => setSummary(r.data)).catch(console.error)
    api.get('/public/highways').then(r => setHighways(r.data)).catch(console.error)
  }, [])

  const severityData = summary ? Object.entries(summary.by_severity).map(([name, value]) => ({ name, value })) : []
  const sourceData = summary ? Object.entries(summary.by_source).map(([name, value]) => ({ name, value })) : []

  return (
    <div className="space-y-6 mt-4">
      <div className="animate-in">
        <h2 className="text-3xl font-black text-white tracking-tight">Road Safety Intelligence</h2>
        <p className="text-sm text-gray-500 mt-1">Real-time pothole detection across Chhattisgarh national highways</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={MapPin} label="Total Potholes" value={summary?.total_potholes?.toLocaleString() || '0'} color="text-white" delay={100} />
        <StatCard icon={AlertTriangle} label="Critical" value={summary?.by_severity?.Critical || 0} color="text-red-400" delay={200} />
        <StatCard icon={FileText} label="Complaints Filed" value={summary?.total_complaints?.toLocaleString() || '0'} color="text-indigo-400" delay={300} />
        <StatCard icon={TrendingUp} label="Sources Active" value={sourceData.length} color="text-emerald-400" delay={400} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Severity Distribution */}
        <div className="glass-card p-6 animate-in" style={{ animationDelay: '500ms' }}>
          <h3 className="text-sm font-semibold text-white mb-4">Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={severityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={40} strokeWidth={0}>
                {severityData.map((entry, i) => <Cell key={i} fill={SEVERITY_COLORS[entry.name] || '#6366f1'} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 12, fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {severityData.map((s, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: SEVERITY_COLORS[s.name] }}></div>
                <span className="text-xs text-gray-400">{s.name}: {s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Detection Sources */}
        <div className="glass-card p-6 animate-in" style={{ animationDelay: '600ms' }}>
          <h3 className="text-sm font-semibold text-white mb-4">Detection Sources</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sourceData} layout="vertical">
              <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fill: '#94a3b8', fontSize: 11 }} width={100} />
              <Tooltip contentStyle={{ background: '#0f0f1a', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 12, fontSize: 12 }} />
              <Bar dataKey="value" fill="#6366f1" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Highway Statistics */}
      {highways.length > 0 && (
        <div className="glass-card p-6 animate-in" style={{ animationDelay: '700ms' }}>
          <h3 className="text-sm font-semibold text-white mb-4">Monitored Highways</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {highways.map((h, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
                <div>
                  <p className="text-sm font-medium text-white">{h.highway}</p>
                  <p className="text-xs text-gray-500">{h.total_km.toFixed(1)} km • {h.segments} segments</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
