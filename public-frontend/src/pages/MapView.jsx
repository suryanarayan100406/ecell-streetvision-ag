import { useState, useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import { api } from '../App'

// Set token — user should set VITE_MAPBOX_TOKEN env variable
mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.placeholder'

const SEVERITY_COLORS = { Critical: '#ef4444', High: '#f59e0b', Medium: '#eab308', Low: '#22c55e' }

export default function MapView() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [potholes, setPotholes] = useState([])
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.get('/public/potholes?page_size=200').then(r => setPotholes(r.data.items || [])).catch(console.error)
  }, [])

  useEffect(() => {
    if (map.current || !mapContainer.current) return
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [81.6296, 21.2514], // Raipur, Chhattisgarh
      zoom: 7,
    })
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')
  }, [])

  useEffect(() => {
    if (!map.current || potholes.length === 0) return

    const addMarkers = () => {
      // Remove existing markers
      document.querySelectorAll('.pothole-marker').forEach(m => m.remove())

      potholes.forEach(p => {
        if (!p.latitude || !p.longitude) return

        const el = document.createElement('div')
        el.className = 'pothole-marker'
        el.style.cssText = `
          width: ${p.severity === 'Critical' ? 16 : p.severity === 'High' ? 14 : 12}px;
          height: ${p.severity === 'Critical' ? 16 : p.severity === 'High' ? 14 : 12}px;
          background: ${SEVERITY_COLORS[p.severity] || '#6366f1'};
          border-radius: 50%;
          border: 2px solid rgba(0,0,0,0.3);
          cursor: pointer;
          box-shadow: 0 0 8px ${SEVERITY_COLORS[p.severity] || '#6366f1'}80;
        `

        el.addEventListener('click', () => setSelected(p))

        new mapboxgl.Marker({ element: el })
          .setLngLat([p.longitude, p.latitude])
          .addTo(map.current)
      })
    }

    if (map.current.loaded()) addMarkers()
    else map.current.on('load', addMarkers)
  }, [potholes])

  return (
    <div className="mt-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Live Pothole Map</h2>
          <p className="text-sm text-gray-500 mt-1">{potholes.length} detections across Chhattisgarh highways</p>
        </div>
        <div className="flex gap-3">
          {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
            <div key={sev} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}60` }}></div>
              <span className="text-xs text-gray-400">{sev}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="relative">
        <div ref={mapContainer} className="glass-card w-full" style={{ height: '70vh' }}></div>

        {/* Detail Panel */}
        {selected && (
          <div className="absolute top-4 right-4 w-80 glass-card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className={`text-xs px-2 py-0.5 rounded-full severity-${selected.severity?.toLowerCase()}`}>{selected.severity}</span>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white text-sm">✕</button>
            </div>
            <h3 className="text-sm font-semibold text-white">{selected.road_name || 'Unknown road'}</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div><span className="text-gray-500">KM Marker</span><p className="text-white">{selected.km_marker || '—'}</p></div>
              <div><span className="text-gray-500">Risk Score</span><p className="text-amber-300 font-bold">{selected.risk_score?.toFixed(1) || '—'}/10</p></div>
              <div><span className="text-gray-500">Source</span><p className="text-white">{selected.source_primary}</p></div>
              <div><span className="text-gray-500">Detected</span><p className="text-white">{selected.detected_at ? new Date(selected.detected_at).toLocaleDateString() : '—'}</p></div>
              <div><span className="text-gray-500">Area</span><p className="text-white">{selected.area_sqm ? `${selected.area_sqm} m²` : '—'}</p></div>
              <div><span className="text-gray-500">Depth</span><p className="text-white">{selected.depth_cm ? `${selected.depth_cm} cm` : '—'}</p></div>
            </div>
            <div><span className="text-xs text-gray-500">Confidence</span>
              <div className="flex items-center gap-2 mt-1">
                <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-indigo-500 rounded-full" style={{ width: `${(selected.confidence_score || 0) * 100}%` }}></div></div>
                <span className="text-xs text-indigo-300 font-medium">{((selected.confidence_score || 0) * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
