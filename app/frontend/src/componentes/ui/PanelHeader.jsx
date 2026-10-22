export default function PanelHeader({ title, subtitle, action, onAction }) {
  return (
    <div className="panel-header">
      <div><h3>{title}</h3><p>{subtitle}</p></div>
      {action && <button onClick={onAction} className="panel-action">{action}</button>}
    </div>
  );
}
