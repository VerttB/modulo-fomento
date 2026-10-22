export default function MetricCard({ label, value, hint, icon, accent }) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${accent}`}>{icon}</div>
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-hint">{hint}</span>
    </article>
  );
}
