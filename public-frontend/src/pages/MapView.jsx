import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../App'

const SEVERITY_COLORS = { Critical: '#ef4444', High: '#f59e0b', Medium: '#eab308', Low: '#22c55e' }
const SEVERITY_RADIUS = { Critical: 8, High: 7, Medium: 6, Low: 5 }

export default function MapView() {
  const [potholes, setPotholes] = useState([])
  const [mapReady, setMapReady] = useState(false)
  const containerRef = useRef(null)
  const mapObjRef = useRef(null)

  useEffect(() => {
    api.get('/public/potholes?page_size=200')
      .then(r => setPotholes(r.data.items || []))
      .catch(console.error)
  }, [])

  // Dynamic import + init map once
  useEffect(() => {
    let cancelled = false
    let mapObj = null

    async function initMap() {
      const L = (await import('leaflet')).default
      await import('leaflet/dist/leaflet.css')

      if (cancelled || !containerRef.current) return
      // Prevent double-init (React 18 strict mode)
      if (containerRef.current._leaflet_id != null) return

      mapObj = L.map(containerRef.current, {
        center: [21.2514, 81.6296],
        zoom: 7,
        zoomControl: true,
      })

      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(mapObj)

      mapObjRef.current = mapObj
      setMapReady(true)
    }

    initMap()

    return () => {
      cancelled = true
      if (mapObj) {
        mapObj.remove()
        mapObj = null
      }
      mapObjRef.current = null
      setMapReady(false)
    }
  }, [])

  // Add markers when both map + data are ready
  useEffect(() => {
    if (!mapReady || !mapObjRef.current || potholes.length === 0) return

    let L
    import('leaflet').then(mod => {
      L = mod.default
      const map = mapObjRef.current
      if (!map) return

      const markers = []
      potholes.forEach(p => {
        if (!p.latitude || !p.longitude) return
        const color = SEVERITY_COLORS[p.severity] || '#6366f1'
        const radius = SEVERITY_RADIUS[p.severity] || 6

        const marker = L.circleMarker([p.latitude, p.longitude], {
          radius,
          color,
          fillColor: color,
          fillOpacity: 0.7,
          weight: 1,
        })
          .bindPopup(`
            <div style="color:#1e1b2e;min-width:200px;font-size:12px;font-family:Inter,sans-serif;">
              <div style="font-weight:700;margin-bottom:4px">${p.road_name || 'Unknown road'}</div>
              <div><b>Severity:</b> <span style="color:${color}">${p.severity}</span></div>
              <div><b>KM:</b> ${p.km_marker || '—'} &nbsp; <b>Risk:</b> ${p.risk_score?.toFixed(1)}/10</div>
              <div><b>Source:</b> ${p.source_primary}</div>
              <div><b>Confidence:</b> ${((p.confidence_score || 0) * 100).toFixed(0)}%</div>
              ${p.area_sqm ? `<div><b>Area:</b> ${p.area_sqm} m²</div>` : ''}
              ${p.depth_cm ? `<div><b>Depth:</b> ${p.depth_cm} cm</div>` : ''}
            </div>
          `)
          .addTo(map)

        markers.push(marker)
      })

      if (markers.length > 0) {
        const group = L.featureGroup(markers)
        map.fitBounds(group.getBounds().pad(0.1))
      }
    })
  }, [mapReady, potholes])

  const severityCounts = {}
  Object.keys(SEVERITY_COLORS).forEach(sev => {
    severityCounts[sev] = potholes.filter(p => p.severity === sev).length
  })

  return (
    <div className="mt-4 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Live Pothole Map</h2>
          <p className="text-sm text-gray-500 mt-1">{potholes.length} detections across Chhattisgarh highways</p>
        </div>
        <div className="flex gap-4 flex-wrap">
          {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
            <div key={sev} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}60` }}></div>
              <span className="text-xs text-gray-400">{sev}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="relative glass-card overflow-hidden" style={{ borderRadius: 20 }}>
        <div ref={containerRef} style={{ height: '70vh', width: '100%', borderRadius: 20, background: '#0a0a12' }} />

        {/* Summary overlay */}
        <div className="absolute bottom-4 left-4 glass-card px-4 py-2 z-[1000] flex gap-4">
          {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
            <div key={sev} className="text-center">
              <div className="text-lg font-bold" style={{ color }}>{severityCounts[sev] || 0}</div>
              <div className="text-[10px] text-gray-400">{sev}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
