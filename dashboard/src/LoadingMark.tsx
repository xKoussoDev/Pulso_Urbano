export default function LoadingMark({ label = 'Cargando…' }: { label?: string }) {
  return <div className="loading-mark" role="status" aria-label={label}>
    <img className="loading-logo" src="/pulso-icon.png" alt="" aria-hidden="true" />
    <span>{label}</span>
  </div>
}
