import { useState, useEffect } from 'react'
import { api } from '../App'

export default function Complaints() {
  const [kanban, setKanban] = useState({})

  useEffect(() => {
    api.get('/dashboard/kanban').then(r => setKanban(r.data)).catch(console.error)
  }, [])

  const COLUMNS = [
    { key: 'DETECTED', label: 'Detected', color: '#6366f1' },
    { key: 'FILED', label: 'Filed', color: '#f59e0b' },
    { key: 'ACKNOWLEDGED', label: 'Acknowledged', color: '#3b82f6' },
    { key: 'IN_PROGRESS', label: 'In Progress', color: '#8b5cf6' },
    { key: 'REPAIRED', label: 'Repaired', color: '#22c55e' },
  ]

  const severityClass = (s) => `severity-${(s || 'low').toLowerCase()}`

  return (
    <div className="mt-4 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Complaint Tracker</h2>
        <p className="text-sm text-gray-500 mt-1">Track every pothole from detection through repair</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 overflow-x-auto">
        {COLUMNS.map(col => (
          <div key={col.key} className="min-w-[240px]">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 rounded-full" style={{ background: col.color }}></div>
              <span className="text-sm font-semibold text-white">{col.label}</span>
              <span className="text-xs text-gray-500 ml-auto">{(kanban[col.key] || []).length}</span>
            </div>
            <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
              {(kanban[col.key] || []).map((card, i) => (
                <div key={i} className={`glass-card p-3 hover:bg-white/[0.04] transition-colors ${card.critically_overdue ? 'border-red-500/40' : ''}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${severityClass(card.severity)}`}>{card.severity}</span>
                    {card.rain_flag && <span className="text-xs">🌧️</span>}
                  </div>
                  <p className="text-xs text-white font-medium">{card.road_name || 'Unknown'}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">KM {card.km_marker || '—'} • Risk {card.risk_score?.toFixed(1) || '—'}</p>
                  {card.portal_ref && <p className="text-[10px] text-indigo-400 mt-1">Ref: {card.portal_ref}</p>}
                  {card.escalation_level > 0 && <span className="text-[10px] text-amber-400 mt-1 inline-block">⬆ Escalation L{card.escalation_level}</span>}
                </div>
              ))}
              {(kanban[col.key] || []).length === 0 && <p className="text-xs text-gray-600 text-center py-4">Empty</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
