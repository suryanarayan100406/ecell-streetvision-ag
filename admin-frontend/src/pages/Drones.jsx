import { useState, useEffect } from 'react'
import { Upload, RefreshCw, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import api from '../services/api'

export default function Drones({ token }) {
  const [missions, setMissions] = useState([])
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => { fetchMissions() }, [])
  const fetchMissions = async () => {
    try { const { data } = await api.get('/admin/drones'); setMissions(data) } catch (e) { console.error(e) }
  }

  const statusIcon = (s) => s === 'COMPLETED' ? <CheckCircle size={14} className="text-green-400" /> : s === 'PROCESSING' ? <Clock size={14} className="text-amber-400" /> : s === 'FAILED' ? <AlertCircle size={14} className="text-red-400" /> : <Clock size={14} className="text-gray-400" />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Drone Missions</h2><p className="text-sm text-gray-400 mt-1">Upload and monitor drone imagery processing</p></div>
        <div className="flex gap-2">
          <button onClick={fetchMissions} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
          <button onClick={() => setShowUpload(!showUpload)} className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white text-sm rounded-xl flex items-center gap-2"><Upload size={14} />Upload Mission</button>
        </div>
      </div>

      {/* Mission table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
            <th className="p-3 text-left">Mission</th><th className="p-3 text-left">Highway</th><th className="p-3 text-left">KM Range</th>
            <th className="p-3 text-left">Source</th><th className="p-3 text-center">Images</th><th className="p-3 text-center">Detections</th>
            <th className="p-3 text-center">Status</th><th className="p-3 text-left">Date</th>
          </tr></thead>
          <tbody>
            {missions.map(m => (
              <tr key={m.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                <td className="p-3 text-white font-medium">{m.mission_name || `Mission #${m.id}`}</td>
                <td className="p-3 text-gray-400">{m.highway || '—'}</td>
                <td className="p-3 text-gray-400">{m.km_start && m.km_end ? `${m.km_start}-${m.km_end}` : '—'}</td>
                <td className="p-3 text-gray-400">{m.source}</td>
                <td className="p-3 text-center text-gray-300">{m.image_count || 0}</td>
                <td className="p-3 text-center text-amber-300 font-medium">{m.detection_count}</td>
                <td className="p-3 text-center"><div className="flex items-center justify-center gap-1.5">{statusIcon(m.processing_status)}<span className="text-xs">{m.processing_status}</span></div></td>
                <td className="p-3 text-gray-500 text-xs">{m.mission_date || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {missions.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">No drone missions yet</p>}
      </div>
    </div>
  )
}
