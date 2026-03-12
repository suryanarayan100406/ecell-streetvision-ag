import { useState, useEffect } from 'react'
import { Camera, Plus, Wifi, Play, RefreshCw } from 'lucide-react'
import api from '../services/api'

export default function CCTV({ token }) {
  const [cameras, setCameras] = useState([])
  useEffect(() => { fetchCameras() }, [])
  const fetchCameras = async () => {
    try { const { data } = await api.get('/admin/cctv'); setCameras(data) } catch (e) { console.error(e) }
  }
  const testConn = async (id) => { try { await api.post(`/admin/cctv/${id}/test`) } catch (e) { console.error(e) } }
  const testInference = async (id) => { try { await api.post(`/admin/cctv/${id}/test-inference`) } catch (e) { console.error(e) } }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h2 className="text-2xl font-bold text-white">CCTV Cameras</h2><p className="text-sm text-gray-400 mt-1">Manage highway ATMS camera feeds</p></div>
        <button onClick={fetchCameras} className="p-2 rounded-xl bg-white/5 hover:bg-white/10"><RefreshCw size={16} className="text-gray-400" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {cameras.map(c => (
          <div key={c.id} className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2"><Camera size={16} className="text-primary-400" /><span className="text-sm font-medium text-white">{c.camera_id}</span></div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${c.status === 'ACTIVE' ? 'bg-green-500/10 text-green-400' : c.status === 'TESTING' ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'}`}>{c.status}</span>
            </div>
            <div className="space-y-1 text-xs text-gray-400 mb-3">
              <p>Highway: {c.highway || '—'} | KM: {c.km_marker || '—'}</p>
              <p>Zone: {c.atms_zone || '—'}</p>
              <p>Height: {c.mounting_height_m || '—'}m | Angle: {c.camera_angle_degrees || '—'}°</p>
              {c.last_active && <p>Last active: {new Date(c.last_active).toLocaleString()}</p>}
            </div>
            <div className="flex gap-2">
              <button onClick={() => testConn(c.camera_id)} className="flex-1 px-2 py-1.5 text-xs bg-blue-500/10 text-blue-400 rounded-lg hover:bg-blue-500/20 flex items-center justify-center gap-1"><Wifi size={10} />Test</button>
              <button onClick={() => testInference(c.camera_id)} className="flex-1 px-2 py-1.5 text-xs bg-purple-500/10 text-purple-400 rounded-lg hover:bg-purple-500/20 flex items-center justify-center gap-1"><Play size={10} />Inference</button>
            </div>
          </div>
        ))}
      </div>
      {cameras.length === 0 && <div className="glass-card p-8 text-center"><p className="text-gray-500">No CCTV cameras configured</p></div>}
    </div>
  )
}
