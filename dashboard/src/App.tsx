import { lazy, Suspense, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './supabase'
import IncidentDetail from './IncidentDetail'
import './App.css'

type Incident = {
  id: string
  category: { code: string; name: string }
  title: string
  severity: string
  status: string
  reports_count: number
  priority_score: number
  priority_level: string
  created_at: string
}
type Neighborhood = { id: string; name: string; settlement_type: string; source_key: string; postal_code: string | null; incidents_count: number }

const apiUrl = import.meta.env.VITE_API_URL
const IncidentMap = lazy(() => import('./IncidentMap'))
const statusNames: Record<string, string> = {
  reported: 'Reportado', in_review: 'En revisión', confirmed: 'Confirmado',
  in_progress: 'En atención', resolved: 'Resuelto', discarded: 'Descartado',
}
const severityNames: Record<string, string> = {
  low: 'Baja', medium: 'Media', high: 'Alta', critical: 'Crítica',
}

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [checking, setChecking] = useState(true)
  const [role, setRole] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([])
  const [neighborhoodId, setNeighborhoodId] = useState('')
  const [nameSearch, setNameSearch] = useState('')
  const [postalSearch, setPostalSearch] = useState('')
  const [view, setView] = useState<'active' | 'closed'>('active')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [authRetry, setAuthRetry] = useState(0)

  useEffect(() => {
    if (!supabase) {
      const timer = setTimeout(() => setChecking(false), 0)
      return () => clearTimeout(timer)
    }
    const client = supabase
    let currentUserId: string | null = null
    const { data: listener } = client.auth.onAuthStateChange((event, current) => {
      const nextUserId = current?.user.id ?? null
      if (event === 'SIGNED_OUT' || (currentUserId && currentUserId !== nextUserId)) {
        setRole(''); setIncidents([]); setNeighborhoods([]); setNeighborhoodId('')
        setNameSearch(''); setPostalSearch('')
        setNextCursor(null); setSelectedId(null); setView('active')
      }
      currentUserId = nextUserId
      setSession(current)
      setChecking(false)
    })
    return () => listener.subscription.unsubscribe()
  }, [])

  const loadIncidents = async (token: string, cursor?: string, scope: 'active' | 'closed' = view, area = neighborhoodId) => {
    const params = new URLSearchParams({ limit: '20', scope })
    if (cursor) params.set('cursor', cursor)
    if (area) params.set('neighborhood_id', area)
    const response = await fetch(`${apiUrl}/incidents?${params}`, { headers: { Authorization: `Bearer ${token}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error?.message || 'No se pudieron cargar los incidentes')
    setIncidents((previous) => cursor ? [...previous, ...data.items] : data.items)
    setNextCursor(data.next_cursor)
  }

  const loadNeighborhoods = async (token: string) => {
    const response = await fetch(`${apiUrl}/neighborhoods`, { headers: { Authorization: `Bearer ${token}` } })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error?.message || 'No se pudieron cargar los asentamientos')
    setNeighborhoods(data.items)
  }

  const accessToken = session?.access_token
  useEffect(() => {
    if (!accessToken || !apiUrl) return
    let cancelled = false
    const token = accessToken
    const load = async () => {
      setBusy(true); setMessage('')
      try {
        const response = await fetch(`${apiUrl}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
        const data = await response.json()
        if (!response.ok) throw new Error(data.error?.message || 'No se pudo verificar el acceso')
        if (cancelled) return
        setRole(data.role)
        if (data.role === 'staff') await Promise.all([
          loadNeighborhoods(token), loadIncidents(token, undefined, 'active'),
        ])
      } catch (error) {
        if (!cancelled) setMessage(error instanceof Error ? error.message : 'No se pudo conectar')
      } finally { if (!cancelled) setBusy(false) }
    }
    const timer = setTimeout(() => { void load() }, 0)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [accessToken, authRetry])

  const signIn = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!supabase) return
    setBusy(true); setMessage('')
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) setMessage('No se pudo iniciar sesión. Revisa las credenciales.')
    } catch {
      setMessage('No se pudo conectar con Supabase Auth')
    } finally { setPassword(''); setBusy(false) }
  }

  const refresh = async (cursor?: string) => {
    if (!session) return
    setBusy(true); setMessage('')
    try { await loadIncidents(session.access_token, cursor) }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo actualizar') }
    finally { setBusy(false) }
  }

  const switchView = async (scope: 'active' | 'closed') => {
    if (!session || scope === view) return
    setView(scope); setIncidents([]); setNextCursor(null); setBusy(true); setMessage('')
    try { await loadIncidents(session.access_token, undefined, scope) }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo cargar la lista') }
    finally { setBusy(false) }
  }

  const changeNeighborhood = async (area: string) => {
    if (!session || area === neighborhoodId) return
    setNeighborhoodId(area); setIncidents([]); setNextCursor(null); setBusy(true); setMessage('')
    try { await loadIncidents(session.access_token, undefined, view, area) }
    catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo filtrar la lista') }
    finally { setBusy(false) }
  }

  const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  const visibleNeighborhoods = neighborhoods.filter((area) =>
    normalize(area.name).includes(normalize(nameSearch.trim())) &&
    (!postalSearch || area.postal_code?.startsWith(postalSearch))
  )

  const client = supabase
  if (!client || !apiUrl) return <main className="page"><h1>Configura el dashboard</h1><p>Completa las variables VITE_ en dashboard/.env.</p></main>
  if (checking) return <main className="page"><p>Comprobando sesión…</p></main>

  return <main className="page">
    <header className="header">
      <div><p className="eyebrow">Inteligencia Urbana</p><h1>Panel de incidentes</h1></div>
      {session && <button className="secondary" onClick={() => void client.auth.signOut()}>Cerrar sesión</button>}
    </header>
    {message && <p className="error" role="alert">{message}</p>}
    {!session && <section className="card login">
      <h2>Acceso para funcionarios</h2>
      <p>Ingresa con la cuenta autorizada para el municipio.</p>
      <form onSubmit={signIn}>
        <label>Correo<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Contraseña<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <button disabled={busy} type="submit">Entrar</button>
      </form>
    </section>}
    {session && !role && <section className="card"><h2>Verificando acceso</h2>
      <p>{busy ? 'Cargando el mapa y los incidentes…' : 'No se pudo completar la verificación de acceso.'}</p>
      {!busy && <button onClick={() => setAuthRetry((value) => value + 1)}>Reintentar</button>}
    </section>}
    {session && role && role !== 'staff' && <section className="card"><h2>Acceso no autorizado</h2><p>Esta cuenta no está registrada como funcionario activo.</p></section>}
    {session && role === 'staff' && selectedId && <IncidentDetail id={selectedId} token={session.access_token} apiUrl={apiUrl} onClose={() => setSelectedId(null)} onChanged={() => refresh()} />}
    {session && role === 'staff' && !selectedId && <>
      <section className="card neighborhood-filter">
        <div className="neighborhood-search">
          <label>Buscar colonia o asentamiento
            <input value={nameSearch} disabled={busy} placeholder="Escribe un nombre"
              onChange={(event) => { setNameSearch(event.target.value); if (neighborhoodId) void changeNeighborhood('') }} />
          </label>
          <label>Código postal
            <input value={postalSearch} disabled={busy} inputMode="numeric" maxLength={5} placeholder="Ej. 20263"
              onChange={(event) => { setPostalSearch(event.target.value.replace(/\D/g, '').slice(0, 5)); if (neighborhoodId) void changeNeighborhood('') }} />
          </label>
        </div>
        <label htmlFor="neighborhood">Filtrar incidentes por colonia o asentamiento</label>
        <select id="neighborhood" value={neighborhoodId} disabled={busy}
          onChange={(event) => void changeNeighborhood(event.target.value)}>
          <option value="">Todos los asentamientos</option>
          {visibleNeighborhoods.map((area) => <option key={area.id} value={area.id}>
            {area.name} · {area.settlement_type} · CP {area.postal_code || 'sin dato'} · {area.incidents_count} incidente{area.incidents_count === 1 ? '' : 's'}
          </option>)}
        </select>
        <small>{visibleNeighborhoods.length} asentamientos coinciden con la búsqueda.</small>
        <small>Fuente: INEGI, Delimitación de colonias y otros asentamientos humanos 2024.</small>
      </section>
      {view === 'active' && (import.meta.env.VITE_MAPBOX_TOKEN
        ? <Suspense fallback={<p>Cargando mapa…</p>}><IncidentMap token={session.access_token} apiUrl={apiUrl} neighborhoodId={neighborhoodId} onSelect={setSelectedId} /></Suspense>
        : <section className="card"><p>Configura VITE_MAPBOX_TOKEN para mostrar el mapa.</p></section>)}
      <section className="card">
      <div className="section-head"><div><h2>{view === 'active' ? 'Incidentes activos' : 'Completados y descartados'}</h2><p>{view === 'active' ? 'Pendientes de atención, ordenados por fecha.' : 'Registros finalizados de solo lectura.'}</p></div><button className="secondary" onClick={() => void refresh()} disabled={busy}>Actualizar</button></div>
      <div className="list-tabs">
        <button className={view === 'active' ? '' : 'secondary'} aria-pressed={view === 'active'} onClick={() => void switchView('active')} disabled={busy}>Activos</button>
        <button className={view === 'closed' ? '' : 'secondary'} aria-pressed={view === 'closed'} onClick={() => void switchView('closed')} disabled={busy}>Completados y descartados</button>
      </div>
      {incidents.length === 0 && !busy ? <p>No hay incidentes para mostrar.</p> : null}
      {incidents.length > 0 && <div className="table-wrap"><table>
        <thead><tr><th>Incidente</th><th>Estado</th><th>Gravedad</th><th>Prioridad</th><th>Reportes</th><th>Fecha</th></tr></thead>
        <tbody>{incidents.map((item) => <tr key={item.id}>
          <td><button className="link-button" onClick={() => setSelectedId(item.id)}>{item.title}</button><small>{item.category.name}</small></td>
          <td>{statusNames[item.status] || item.status}</td>
          <td>{severityNames[item.severity] || item.severity}</td>
          <td><span className={`priority ${item.priority_level}`}>{item.priority_score.toFixed(2)} · {severityNames[item.priority_level] || item.priority_level}</span></td>
          <td>{item.reports_count}</td><td>{new Date(item.created_at).toLocaleString('es-MX')}</td>
        </tr>)}</tbody>
      </table></div>}
      {nextCursor && <button className="secondary more" onClick={() => void refresh(nextCursor)} disabled={busy}>Cargar más</button>}
      {busy && <p>Actualizando…</p>}
      </section>
    </>}
  </main>
}

export default App
