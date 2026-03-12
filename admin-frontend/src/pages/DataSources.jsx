import { useState } from 'react'
import { Database, Map, FileText, BarChart3, Users } from 'lucide-react'

const TABS = [
  { key: 'osm', label: 'OSM Highways', icon: Map, desc: 'OpenStreetMap road geometry — weekly refresh' },
  { key: 'accidents', label: 'Accident Data', icon: BarChart3, desc: 'data.gov.in road accident statistics' },
  { key: 'ncrb', label: 'NCRB Data', icon: FileText, desc: 'National Crime Records Bureau annual PDF data' },
  { key: 'nhai', label: 'NHAI Traffic', icon: Users, desc: 'National Highways Authority traffic census — quarterly' },
  { key: 'osm_notes', label: 'OSM Notes', icon: Database, desc: 'OSM notes with road damage keywords' },
]

export default function DataSources() {
  const [activeTab, setActiveTab] = useState('osm')
  const active = TABS.find(t => t.key === activeTab)
  return (
    <div className="space-y-6">
      <div><h2 className="text-2xl font-bold text-white">Government Data Sources</h2><p className="text-sm text-gray-400 mt-1">Manage 5 data ingestion pipelines</p></div>
      <div className="flex gap-2 flex-wrap">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition-all ${activeTab === t.key ? 'bg-primary-600/20 text-primary-300 border border-primary-500/30' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}>
            <t.icon size={14} />{t.label}
          </button>
        ))}
      </div>
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-2">{active?.label}</h3>
        <p className="text-sm text-gray-400 mb-4">{active?.desc}</p>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white/[0.03]"><p className="text-xs text-gray-500 mb-1">Last Refresh</p><p className="text-sm text-white">Pending initial load</p></div>
          <div className="p-4 rounded-xl bg-white/[0.03]"><p className="text-xs text-gray-500 mb-1">Records</p><p className="text-sm text-white">0</p></div>
        </div>
      </div>
    </div>
  )
}
