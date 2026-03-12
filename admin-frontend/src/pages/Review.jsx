import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import api from '../services/api'

export default function Review({ token }) {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => { fetchReview() }, [page])
  const fetchReview = async () => {
    try { const { data } = await api.get('/admin/review', { params: { page, page_size: 12 } }); setItems(data.items); setTotal(data.total) } catch (e) { console.error(e) }
  }
  const accept = async (id) => {
    try { await api.post(`/admin/review/${id}/accept`); fetchReview() } catch (e) { console.error(e) }
  }
  const reject = async (id) => {
    try { await api.post(`/admin/review/${id}/reject`); fetchReview() } catch (e) { console.error(e) }
  }

  const severityColor = (s) => ({ Critical: 'text-red-400 bg-red-500/10', High: 'text-amber-400 bg-amber-500/10', Medium: 'text-yellow-300 bg-yellow-500/10', Low: 'text-green-400 bg-green-500/10' }[s] || 'text-gray-400 bg-white/5')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Detection Review</h2><p className="text-sm text-gray-400 mt-1">Review detections with confidence 0.65-0.84 ({total} pending)</p></div>
        <button onClick={fetchReview} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {items.map(p => (
          <div key={p.id} className="glass-card overflow-hidden">
            <div className="h-40 bg-surface-900 flex items-center justify-center">
              {p.image_path ? <img src={`/api/files/${p.image_path}`} alt="Detection" className="h-full w-full object-cover" /> : <span className="text-gray-600 text-sm">No image</span>}
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${severityColor(p.severity)}`}>{p.severity}</span>
                <span className="text-xs text-gray-500">#{p.id}</span>
              </div>
              <p className="text-sm text-white font-medium">{p.road_name || 'Unknown road'}</p>
              <p className="text-xs text-gray-400 mt-1">KM {p.km_marker || '—'} | {p.source_primary}</p>
              <div className="flex items-center justify-between mt-2">
                <div>
                  <p className="text-xs text-gray-500">Confidence</p>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-primary-500 rounded-full" style={{ width: `${(p.confidence_score || 0) * 100}%` }}></div></div>
                    <span className="text-xs text-primary-300">{((p.confidence_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">Risk</p>
                  <span className="text-sm font-bold text-amber-300">{p.risk_score?.toFixed(1) || '—'}</span>
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button onClick={() => accept(p.id)} className="flex-1 py-2 text-xs bg-green-500/10 text-green-400 rounded-lg hover:bg-green-500/20 flex items-center justify-center gap-1"><CheckCircle size={12} />Accept & File</button>
                <button onClick={() => reject(p.id)} className="flex-1 py-2 text-xs bg-red-500/10 text-red-400 rounded-lg hover:bg-red-500/20 flex items-center justify-center gap-1"><XCircle size={12} />Reject</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {items.length === 0 && <div className="glass-card p-8 text-center"><p className="text-gray-500">No detections pending review</p></div>}
    </div>
  )
}
