import { useState, useEffect } from 'react'
import { RefreshCw, Filter } from 'lucide-react'
import api from '../services/api'

export default function Logs({ token }) {
  const [tab, setTab] = useState('audit')
  const [auditLog, setAuditLog] = useState([])
  const [geminiLog, setGeminiLog] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)

  useEffect(() => { tab === 'audit' ? fetchAudit() : fetchGemini() }, [tab, page])

  const fetchAudit = async () => {
    try { const { data } = await api.get('/admin/audit-log', { params: { page, page_size: 30 } }); setAuditLog(data.items); setTotal(data.total) } catch (e) { console.error(e) }
  }
  const fetchGemini = async () => {
    try { const { data } = await api.get('/admin/gemini-audit', { params: { page, page_size: 30 } }); setGeminiLog(data.items); setTotal(data.total) } catch (e) { console.error(e) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Logs & Audit</h2><p className="text-sm text-gray-400 mt-1">System audit trail and Gemini API logs</p></div>
        <button onClick={() => tab === 'audit' ? fetchAudit() : fetchGemini()} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>

      <div className="flex gap-2">
        {['audit', 'gemini'].map(t => (
          <button key={t} onClick={() => { setTab(t); setPage(1) }}
            className={`px-4 py-2 rounded-xl text-sm transition-all ${tab === t ? 'bg-primary-600/20 text-primary-300 border border-primary-500/30' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}>
            {t === 'audit' ? 'Admin Audit' : 'Gemini API'}
          </button>
        ))}
      </div>

      <div className="glass-card overflow-hidden">
        {tab === 'audit' ? (
          <table className="w-full text-sm">
            <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
              <th className="p-3 text-left">Action</th><th className="p-3 text-left">Resource</th><th className="p-3 text-left">Summary</th><th className="p-3 text-left">Time</th>
            </tr></thead>
            <tbody>
              {auditLog.map((a, i) => (
                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="p-3 text-xs"><span className="px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-300">{a.action_type}</span></td>
                  <td className="p-3 text-gray-400 text-xs">{a.resource_type}:{a.resource_id}</td>
                  <td className="p-3 text-gray-300 text-xs">{a.change_summary}</td>
                  <td className="p-3 text-gray-500 text-xs">{a.performed_at ? new Date(a.performed_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
              <th className="p-3 text-left">Use Case</th><th className="p-3 text-left">Model</th><th className="p-3 text-center">Tokens</th><th className="p-3 text-center">Status</th><th className="p-3 text-left">Time</th>
            </tr></thead>
            <tbody>
              {geminiLog.map((g, i) => (
                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="p-3 text-white text-xs">{g.use_case}</td>
                  <td className="p-3 text-gray-400 text-xs">{g.model_name}</td>
                  <td className="p-3 text-center text-gray-300 text-xs">{(g.prompt_tokens || 0) + (g.completion_tokens || 0)}</td>
                  <td className="p-3 text-center">{g.success ? <span className="text-green-400 text-xs">✓</span> : <span className="text-red-400 text-xs">✗</span>}</td>
                  <td className="p-3 text-gray-500 text-xs">{g.called_at ? new Date(g.called_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {((tab === 'audit' && auditLog.length === 0) || (tab === 'gemini' && geminiLog.length === 0)) && <p className="text-center py-8 text-gray-600 text-sm">No log entries</p>}
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
