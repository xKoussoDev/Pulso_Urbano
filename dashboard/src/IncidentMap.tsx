import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import LoadingMark from './LoadingMark'

type Point = {
  id: string
  latitude: number
  longitude: number
  category_code: string
  priority_score: number
  priority_level: string
  status: string
}

const colors: Record<string, string> = {
  low: '#196b4b', medium: '#1749a2', high: '#895500', critical: '#a42b40',
}
const rank: Record<string, number> = { low: 1, medium: 2, high: 3, critical: 4 }

function groupNearby(points: Point[], map: mapboxgl.Map): Point[][] {
  const groups: Point[][] = []
  for (const point of points) {
    const position = map.project([point.longitude, point.latitude])
    const group = groups.find((current) => {
      const first = map.project([current[0].longitude, current[0].latitude])
      return Math.hypot(position.x - first.x, position.y - first.y) < 36
    })
    if (group) group.push(point)
    else groups.push([point])
  }
  return groups
}

export default function IncidentMap({ token, apiUrl, neighborhoodId, onSelect }: { token: string; apiUrl: string; neighborhoodId: string; onSelect: (id: string) => void }) {
  const container = useRef<HTMLDivElement>(null)
  const markers = useRef<mapboxgl.Marker[]>([])
  const [count, setCount] = useState(0)
  const [truncated, setTruncated] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    if (!container.current) return
    let request: AbortController | null = null
    const map = new mapboxgl.Map({
      container: container.current, accessToken: import.meta.env.VITE_MAPBOX_TOKEN,
      style: 'mapbox://styles/mapbox/streets-v12', center: [-102.2916, 21.8818], zoom: 11.5,
    })
    map.addControl(new mapboxgl.NavigationControl(), 'top-right')

    const update = async () => {
      const bounds = map.getBounds()
      if (!bounds) return
      setLoading(true)
      request?.abort()
      request = new AbortController()
      const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()].join(',')
      try {
        const params = new URLSearchParams({ scope: 'active', bbox })
        if (neighborhoodId) params.set('neighborhood_id', neighborhoodId)
        const response = await fetch(`${apiUrl}/incidents/map?${params}`, {
          headers: { Authorization: `Bearer ${token}` }, signal: request.signal,
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.error?.message || 'No se pudieron cargar los puntos')
        markers.current.forEach((marker) => marker.remove())
        markers.current = groupNearby(data.items as Point[], map).map((group) => {
          const point = group[0]
          const highest = group.reduce((best, item) => rank[item.priority_level] > rank[best.priority_level] ? item : best)
          const markerElement = document.createElement('button')
          markerElement.type = 'button'
          markerElement.className = 'incident-marker'
          markerElement.style.backgroundColor = colors[highest.priority_level] || '#2875a0'
          markerElement.textContent = group.length > 1 ? String(group.length) : '•'
          markerElement.setAttribute('aria-label', `${group.length} incidente${group.length === 1 ? '' : 's'} en esta zona`)
          const details = document.createElement('div')
          const title = document.createElement('strong')
          title.textContent = `${group.length} incidente${group.length === 1 ? '' : 's'} en esta zona`
          details.append(title)
          for (const item of group) {
            const line = document.createElement('button')
            line.type = 'button'
            line.className = 'popup-link'
            line.textContent = `${item.category_code.replaceAll('_', ' ')} · ${item.status} · prioridad ${item.priority_score.toFixed(2)}`
            line.addEventListener('click', () => onSelect(item.id))
            details.append(line)
          }
          return new mapboxgl.Marker({ element: markerElement, anchor: 'bottom' })
            .setLngLat([point.longitude, point.latitude])
            .setPopup(new mapboxgl.Popup({ offset: 20 }).setDOMContent(details))
            .addTo(map)
        })
        setCount(data.items.length)
        setTruncated(data.truncated)
        setMessage('')
        setLoading(false)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setMessage(error instanceof Error ? error.message : 'No se pudo cargar el mapa')
        setLoading(false)
      }
    }
    map.on('load', update)
    map.on('moveend', update)
    map.on('error', () => { setMessage('No se pudo cargar el mapa'); setLoading(false) })
    return () => { request?.abort(); markers.current.forEach((marker) => marker.remove()); map.remove() }
  }, [token, apiUrl, neighborhoodId, onSelect, retry])

  return <section className="card map-section">
    <h2>Mapa de incidentes</h2>
    <p>Mueve o acerca el mapa para consultar otra zona.</p>
    {message && <p className="error" role="alert">{message}</p>}
    {message && <button className="secondary" onClick={() => setRetry((value) => value + 1)}>Reintentar mapa</button>}
    <div className="map-frame">
      {loading && <div className="map-loading"><LoadingMark label="Cargando puntos del mapa…" /></div>}
      <div className="map-view" ref={container} role="region" aria-label="Mapa de incidentes" />
    </div>
    <div className="map-legend" aria-label="Prioridad de los marcadores">
      <span><i className="legend-dot low" /> Baja</span><span><i className="legend-dot medium" /> Media</span>
      <span><i className="legend-dot high" /> Alta</span><span><i className="legend-dot critical" /> Crítica</span>
    </div>
    <p className="map-caption">{count} incidentes en esta vista{truncated ? ' · Hay más puntos; acerca el mapa' : ''}</p>
  </section>
}
