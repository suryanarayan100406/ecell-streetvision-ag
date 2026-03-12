import { useState, useEffect } from 'react'
import { Clock, Play, RefreshCw } from 'lucide-react'
import api from '../services/api'

export default function Scheduler({ token }) {
  const [tasks, setTasks] = useState([])
  useEffect(() => { fetchTasks() }, [])
  const fetchTasks = async () => { try { const { data } = await api.get('/admin/scheduler/tasks'); setTasks(data) } catch (e) { console.error(e) } }
  const trigger = async (name) => { try { await api.post(`/admin/scheduler/${encodeURIComponent(name)}/trigger`) } catch (e) { console.error(e) } }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">Task Scheduler</h2><p className="text-sm text-gray-400 mt-1">Celery Beat scheduled tasks ({tasks.length} configured)</p></div>
        <button onClick={fetchTasks} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>
      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="text-xs uppercase text-gray-500 border-b border-primary-800/20">
            <th className="p-3 text-left">Task</th><th className="p-3 text-left">Function</th><th className="p-3 text-left">Schedule</th><th className="p-3 text-left">Queue</th><th className="p-3 text-center">Action</th>
          </tr></thead>
          <tbody>
            {tasks.map((t, i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="p-3 text-white text-xs font-medium">{t.task_name}</td>
                <td className="p-3 text-gray-400 text-xs font-mono">{t.task_function}</td>
                <td className="p-3 text-gray-300 text-xs"><div className="flex items-center gap-1"><Clock size={12} className="text-primary-400" />{t.schedule}</div></td>
                <td className="p-3 text-xs"><span className="px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-300">{t.queue}</span></td>
                <td className="p-3 text-center"><button onClick={() => trigger(t.task_name)} className="px-2 py-1 text-xs text-green-400 bg-green-500/10 rounded-lg hover:bg-green-500/20 flex items-center gap-1 mx-auto"><Play size={10} />Run Now</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {tasks.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">No scheduled tasks</p>}
      </div>
    </div>
  )
}
