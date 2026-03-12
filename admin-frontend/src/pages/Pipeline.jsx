import { useState, useEffect } from 'react'
import { RefreshCw, Filter } from 'lucide-react'
import api from '../services/api'

export default function Pipeline({ token }) {
  const [tasks, setTasks] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => { fetchTasks() }, [page, statusFilter])
  const fetchTasks = async () => {
    try {
      const params = { page, page_size: 30 }
      if (statusFilter) params.status = statusFilter
      const { data } = await api.get('/admin/pipeline/task-history', { params })
      setTasks(data.items); setTotal(data.total)
    } catch (e) { console.error(e) }
  }

  const statusColor = (s) => ({ SUCCESS: 'text-green-400 bg-green-500/10', FAILURE: 'text-red-400 bg-red-500/10', STARTED: 'text-amber-400 bg-amber-500/10', PENDING: 'text-gray-400 bg-white/5' }[s] || 'text-gray-400 bg-white/5')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Pipeline Monitor</h2><p className="text-sm text-gray-400 mt-1">Celery task execution history</p></div>
        <div className="flex gap-2">
          <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            className="px-3 py-1.5 bg-surface-850 border border-primary-800/30 rounded-xl text-sm text-gray-300">
            <option value="">All</option><option value="SUCCESS">Success</option><option value="FAILURE">Failure</option><option value="STARTED">Running</option>
          </select>
          <button onClick={fetchTasks} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
        </div>
      </div>
      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
            <th className="p-3 text-left">Task</th><th className="p-3 text-left">Queue</th><th className="p-3 text-center">Status</th>
            <th className="p-3 text-right">Duration</th><th className="p-3 text-left">Started</th>
          </tr></thead>
          <tbody>
            {tasks.map((t, i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="p-3 text-white text-xs font-mono">{t.task_name || '—'}</td>
                <td className="p-3 text-gray-400 text-xs">{t.queue || '—'}</td>
                <td className="p-3 text-center"><span className={`text-xs px-2 py-0.5 rounded-full ${statusColor(t.status)}`}>{t.status}</span></td>
                <td className="p-3 text-right text-gray-400 text-xs">{t.duration_seconds ? `${t.duration_seconds}s` : '—'}</td>
                <td className="p-3 text-gray-500 text-xs">{t.started_at ? new Date(t.started_at).toLocaleString() : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {tasks.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">No task history</p>}
      </div>
      {total > 30 && (
        <div className="flex justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 text-sm bg-white/5 rounded-lg disabled:opacity-30">Prev</button>
          <span className="text-sm text-gray-400 py-1">Page {page} of {Math.ceil(total / 30)}</span>
          <button disabled={page >= Math.ceil(total / 30)} onClick={() => setPage(p => p + 1)} className="px-3 py-1 text-sm bg-white/5 rounded-lg disabled:opacity-30">Next</button>
        </div>
      )}
    </div>
  )
}
