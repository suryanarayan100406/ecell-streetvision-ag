import { useState, useEffect } from 'react'
import { Brain, Star, RefreshCw } from 'lucide-react'
import api from '../services/api'

export default function Models({ token }) {
  const [models, setModels] = useState([])
  useEffect(() => { fetchModels() }, [])
  const fetchModels = async () => { try { const { data } = await api.get('/admin/models'); setModels(data) } catch (e) { console.error(e) } }
  const promote = async (id) => { try { await api.post(`/admin/models/${id}/promote`); fetchModels() } catch (e) { console.error(e) } }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Model Management</h2><p className="text-sm text-gray-400 mt-1">YOLOv8 and depth estimation model registry</p></div>
        <button onClick={fetchModels} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {models.map(m => (
          <div key={m.id} className={`glass-card p-5 ${m.active ? 'border-green-500/30' : ''}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2"><Brain size={16} className="text-primary-400" /><span className="text-sm font-medium text-white">{m.model_type}</span></div>
              {m.active && <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 flex items-center gap-1"><Star size={10} />Active</span>}
            </div>
            <p className="text-xs text-gray-400 mb-3">Version: {m.version} | {m.training_images || 0} images</p>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center p-2 rounded-lg bg-white/[0.03]"><p className="text-[10px] text-gray-500">mAP50</p><p className="text-sm font-medium text-white">{m.val_map50 ? (m.val_map50 * 100).toFixed(1) + '%' : '—'}</p></div>
              <div className="text-center p-2 rounded-lg bg-white/[0.03]"><p className="text-[10px] text-gray-500">mAP75</p><p className="text-sm font-medium text-white">{m.val_map75 ? (m.val_map75 * 100).toFixed(1) + '%' : '—'}</p></div>
              <div className="text-center p-2 rounded-lg bg-white/[0.03]"><p className="text-[10px] text-gray-500">FP Rate</p><p className="text-sm font-medium text-white">{m.false_positive_rate ? (m.false_positive_rate * 100).toFixed(1) + '%' : '—'}</p></div>
            </div>
            {!m.active && <button onClick={() => promote(m.id)} className="w-full py-2 text-xs bg-primary-600/20 text-primary-300 rounded-lg hover:bg-primary-600/30 transition-colors">Promote to Production</button>}
          </div>
        ))}
      </div>
      {models.length === 0 && <div className="glass-card p-8 text-center"><p className="text-gray-500">No models registered</p></div>}
    </div>
  )
}
