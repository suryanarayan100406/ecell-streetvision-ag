import { useState, useEffect } from 'react'
import { Save, RefreshCw } from 'lucide-react'
import api from '../services/api'

export default function Settings({ token }) {
  const [settings, setSettings] = useState([])
  const [editingKey, setEditingKey] = useState(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => { fetchSettings() }, [])
  const fetchSettings = async () => { try { const { data } = await api.get('/admin/settings'); setSettings(data) } catch (e) { console.error(e) } }
  const saveSetting = async (key) => {
    try { await api.put(`/admin/settings/${key}?value=${encodeURIComponent(editValue)}`); setEditingKey(null); fetchSettings() } catch (e) { console.error(e) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">System Settings</h2><p className="text-sm text-gray-400 mt-1">Runtime configuration parameters</p></div>
        <button onClick={fetchSettings} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>
      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
            <th className="p-3 text-left">Key</th><th className="p-3 text-left">Value</th><th className="p-3 text-left">Type</th><th className="p-3 text-left">Description</th><th className="p-3 text-center">Edit</th>
          </tr></thead>
          <tbody>
            {settings.map(s => (
              <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="p-3 text-white text-xs font-mono">{s.key}</td>
                <td className="p-3">
                  {editingKey === s.key ? (
                    <div className="flex gap-1">
                      <input value={editValue} onChange={e => setEditValue(e.target.value)} className="px-2 py-1 bg-surface-900 border border-primary-500/30 rounded text-xs text-white w-32" />
                      <button onClick={() => saveSetting(s.key)} className="p-1 bg-green-500/10 text-green-400 rounded"><Save size={12} /></button>
                    </div>
                  ) : <span className="text-gray-300 text-xs">{s.value || '—'}</span>}
                </td>
                <td className="p-3 text-gray-500 text-xs">{s.value_type || '—'}</td>
                <td className="p-3 text-gray-500 text-xs">{s.description || '—'}</td>
                <td className="p-3 text-center">{editingKey !== s.key && <button onClick={() => { setEditingKey(s.key); setEditValue(s.value || '') }} className="text-xs text-primary-400 hover:text-primary-300">Edit</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {settings.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">No settings configured</p>}
      </div>
    </div>
  )
}
