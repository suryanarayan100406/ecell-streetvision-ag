import { useState, useEffect } from 'react'
import { RefreshCw, Wifi, WifiOff, ChevronDown, Play, Download } from 'lucide-react'
import api from '../services/api'

export default function Satellites({ token }) {
  const [sources, setSources] = useState([])
  const [expanded, setExpanded] = useState(null)
  const [downloads, setDownloads] = useState({})
  const [selectionLog, setSelectionLog] = useState([])

  useEffect(() => { fetchSources(); fetchSelectionLog() }, [])

  const fetchSources = async () => {
    try { const { data } = await api.get('/admin/satellites'); setSources(data) } catch (e) { console.error(e) }
  }
  const fetchSelectionLog = async () => {
    try { const { data } = await api.get('/admin/satellites/selection-log'); setSelectionLog(data) } catch (e) { console.error(e) }
  }
  const fetchDownloads = async (id) => {
    try { const { data } = await api.get(`/admin/satellites/${id}/downloads`); setDownloads(p => ({ ...p, [id]: data })) } catch (e) { console.error(e) }
  }
  const testConnection = async (id) => {
    try { await api.post(`/admin/satellites/${id}/test`) } catch (e) { console.error(e) }
  }
  const triggerIngestion = async (id) => {
    try { await api.post(`/admin/satellites/${id}/trigger`) } catch (e) { console.error(e) }
  }

  const statusColor = (s) => s === 'ACTIVE' ? 'text-green-400' : s === 'INACTIVE' ? 'text-gray-500' : 'text-amber-400'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Satellite Sources</h2><p className="text-sm text-gray-400 mt-1">Manage all 9+ satellite data providers</p></div>
        <button onClick={fetchSources} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>

      <div className="space-y-3">
        {sources.map(src => (
          <div key={src.id} className="glass-card overflow-hidden">
            <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
              onClick={() => { setExpanded(expanded === src.id ? null : src.id); if (expanded !== src.id) fetchDownloads(src.id) }}>
              <div className="flex items-center gap-4">
                {src.credentials_configured ? <Wifi size={16} className="text-green-400" /> : <WifiOff size={16} className="text-red-400" />}
                <div>
                  <p className="text-sm font-medium text-white">{src.display_name || src.source_name}</p>
                  <p className="text-xs text-gray-500">{src.source_type} • {src.resolution_m}m • Every {src.repeat_cycle_days} days</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-medium ${statusColor(src.status)}`}>{src.status}</span>
                <ChevronDown size={16} className={`text-gray-500 transition-transform ${expanded === src.id ? 'rotate-180' : ''}`} />
              </div>
            </div>

            {expanded === src.id && (
              <div className="border-t border-primary-800/20 p-4 space-y-3">
                <div className="flex gap-2">
                  <button onClick={() => testConnection(src.id)} className="px-3 py-1.5 text-xs bg-blue-500/10 text-blue-400 rounded-lg hover:bg-blue-500/20 transition-colors flex items-center gap-1"><Wifi size={12} />Test Connection</button>
                  <button onClick={() => triggerIngestion(src.id)} className="px-3 py-1.5 text-xs bg-green-500/10 text-green-400 rounded-lg hover:bg-green-500/20 transition-colors flex items-center gap-1"><Play size={12} />Trigger Ingestion</button>
                </div>
                {src.last_error && <div className="text-xs text-red-400 bg-red-500/10 rounded-lg p-2">{src.last_error}</div>}
                {src.last_successful_download && <p className="text-xs text-gray-500">Last success: {new Date(src.last_successful_download).toLocaleString()}</p>}

                {downloads[src.id] && downloads[src.id].length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-300 mb-2">Recent Downloads</p>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {downloads[src.id].map((d, i) => (
                        <div key={i} className="flex items-center justify-between text-xs p-2 rounded-lg bg-white/[0.02]">
                          <span className="text-gray-400">{d.product_id?.substring(0, 30)}...</span>
                          <span className={d.success ? 'text-green-400' : 'text-red-400'}>{d.success ? `${d.file_size_mb}MB` : 'Failed'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectionLog.length > 0 && (
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Source Selection Log</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {selectionLog.map((s, i) => (
              <div key={i} className="text-xs p-2 rounded-lg bg-white/[0.02] flex justify-between">
                <span className="text-gray-400">{s.highway} → <span className="text-primary-300 font-medium">{s.selected_source}</span></span>
                <span className="text-gray-600">{s.selected_at ? new Date(s.selected_at).toLocaleDateString() : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
