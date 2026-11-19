import { useCallback, useEffect, useState } from 'react'

type Status = 'reported' | 'in_review' | 'confirmed' | 'in_progress' | 'resolved' | 'discarded'
type Detail = {
  id: string
  category: { code: string; name: string }
  title: string
  description: string
  location: { latitude: number; longitude: number }
  severity: string
  status: Status
  row_version: number
  reports_count: number
  confirmations_count: number
  priority: { score: number; level: string; version: number; factors: { G: number; T: number }; weights: { G: number; T: number }; calculated_at: string }
  status_history: { previous_status: string | null; new_status: string; notes: string | null; created_at: string; changed_by_label: string }[]
  photos: { id: string; url: string; created_at: string }[]
  created_at: string
  updated_at: string
}

const names: Record<string, string> = {
  reported: 'Reportado', in_review: 'En revisión', confirmed: 'Confirmado',
  in_progress: 'En atención', resolved: 'Resuelto', discarded: 'Descartado',
  low: 'Baja', medium: 'Media', high: 'Alta', critical: 'Crítica',
}
const transitions: Record<Status, Status[]> = {
  reported: ['in_review', 'discarded'],
  in_review: ['confirmed', 'discarded'],
  confirmed: ['in_progress', 'discarded'],
  in_progress: ['resolved', 'in_review'],
  resolved: [], discarded: [],
}

export default function IncidentDetail({ id, token, apiUrl, onClose, onChanged }: {
  id: string; token: string; apiUrl: string; onClose: () => void; onChanged: () => Promise<void>
}) {
  const [detail, setDetail] = useState<Detail | null>(null)
  const [nextStatus, setNextStatus] = useState<Status | ''>('')
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const load = useCallback(async () => {
    setBusy(true); setMessage('')
    try {
      const response = await fetch(`${apiUrl}/incidents/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error?.message || 'No se pudo cargar el incidente')
      setDetail(data)
      setNextStatus(transitions[data.status as Status][0] || '')
      return true
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo conectar')
      return false
    } finally { setBusy(false) }
  }, [id, token, apiUrl])

  useEffect(() => {
    const timer = setTimeout(() => { void load() }, 0)
    return () => clearTimeout(timer)
  }, [load])

  const save = async () => {
    if (!detail || !nextStatus || busy) return
    setBusy(true); setMessage('')
    try {
      const response = await fetch(`${apiUrl}/incidents/${id}/status`, {
        method: 'PATCH', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus, notes: notes.trim() || null, expected_version: detail.row_version }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error?.message || 'No se pudo cambiar el estado')
      setNotes('')
      await onChanged()
      if (await load()) setMessage('Estado actualizado')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo actualizar')
    } finally { setBusy(false) }
  }

  return <section className="card detail">
    <button className="secondary" onClick={onClose}>← Volver al mapa y listado</button>
    {message && <p className={message === 'Estado actualizado' ? 'success' : 'error'} role="status">{message}</p>}
    {busy && <p>Actualizando…</p>}
    {detail && <>
      <h2>{detail.title}</h2>
      <p className="detail-meta">{detail.category.name} · {names[detail.status]} · {detail.reports_count} reporte(s) · {detail.confirmations_count} confirmación(es) de otras sesiones</p>
      <p>{detail.description}</p>
      <p><strong>Gravedad declarada:</strong> {names[detail.severity] || detail.severity}</p>
      <p><strong>Ubicación:</strong> {detail.location.latitude.toFixed(5)}, {detail.location.longitude.toFixed(5)}</p>
      <p><strong>Registrado:</strong> {new Date(detail.created_at).toLocaleString('es-MX')}</p>

      <div className="detail-grid">
        <div className="detail-panel">
          <h3>Prioridad actual: {detail.priority.score.toFixed(2)} · {names[detail.priority.level]}</h3>
          <p>Fórmula v{detail.priority.version}: {detail.priority.weights.G} × gravedad + {detail.priority.weights.T} × tiempo abierto.</p>
          <p>Gravedad: {detail.priority.factors.G}/100. Tiempo: {detail.priority.factors.T.toFixed(4)}/100 (llega a 100 tras 14 días).</p>
          <p className="detail-meta">Las confirmaciones se muestran aparte y todavía no modifican esta puntuación.</p>
          <p className="detail-meta">Calculada: {new Date(detail.priority.calculated_at).toLocaleString('es-MX')}. La gravedad fue indicada por el ciudadano.</p>
        </div>
        {transitions[detail.status].length > 0 && <div className="detail-panel">
          <h3>Cambiar estado</h3>
          <label>Nuevo estado
            <select value={nextStatus} onChange={(event) => setNextStatus(event.target.value as Status)}>
              {transitions[detail.status].map((status) => <option key={status} value={status}>{names[status]}</option>)}
            </select>
          </label>
          <label>Nota opcional, sin datos personales
            <textarea value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={500} rows={3} />
          </label>
          <button onClick={() => void save()} disabled={busy}>Guardar estado</button>
        </div>}
      </div>
      {transitions[detail.status].length === 0 && <p className="detail-meta">Este incidente está finalizado. Su detalle e historial son de solo lectura.</p>}
      <h3>Fotografías del reporte</h3>
      {detail.photos.length === 0 ? <p className="detail-meta">Sin fotografías.</p> :
        <div className="detail-photos">{detail.photos.map((photo, index) =>
          <img key={photo.id} className="detail-photo" src={photo.url} alt={`Fotografía ${index + 1} del incidente`}
            loading="lazy" referrerPolicy="no-referrer" />)}</div>}
      <h3>Historial de estados</h3>
      <ol className="history">{detail.status_history.map((entry, index) =>
        <li key={index}><strong>{names[entry.new_status] || entry.new_status}</strong> · {new Date(entry.created_at).toLocaleString('es-MX')} · {entry.changed_by_label}
          {entry.notes && <p>{entry.notes}</p>}</li>)}</ol>
    </>}
  </section>
}
