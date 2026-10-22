import PanelHeader from "../ui/PanelHeader.jsx";
import { formatNumber } from "../../utils/format.js";

const summaryItems = [
  ["INSERIDA", "Inseridas"],
  ["INSERIDA_CONFLITO", "Com conflito"],
  ["DUPLICADA", "Duplicadas"],
  ["IGNORADA", "Ignoradas"],
  ["INVALIDA", "Inválidas"],
  ["ERRO", "Com erro"],
  ["PENDENTE", "Pendentes"],
];

export default function IngestionTraceSummary({ source, summary, executions, loading }) {
  if (!source) return null;
  const statusCounts = summary?.por_status || {};
  // Versões antigas podem não ter checkpoints para linhas duplicadas. Nesse
  // caso, preserva o total registrado na ingestão original.
  const duplicateCount = Math.max(
    statusCounts.DUPLICADA || 0,
    source.linhas_duplicadas || 0,
  );
  const accountedLines = Object.entries(statusCounts).reduce(
    (total, [status, count]) => total + (status === "DUPLICADA" ? duplicateCount : count),
    0,
  );
  const unclassifiedCount = summary
    ? Math.max(source.quantidade_linhas - accountedLines, 0)
    : 0;

  return <div className="ingestion-trace-summary">
    <PanelHeader title="Resumo da ingestão selecionada" subtitle={`${source.nome_arquivo} · iniciada em ${new Date(source.iniciada_em).toLocaleString("pt-BR")}${source.finalizada_em ? ` · finalizada em ${new Date(source.finalizada_em).toLocaleString("pt-BR")}` : " · em processamento"}`} />
    <div className="trace-summary-grid">
      <div className="trace-summary-card"><span>Total no arquivo</span><strong>{formatNumber(source.quantidade_linhas)}</strong></div>
      {summaryItems.map(([key, label]) => <div className="trace-summary-card" key={key}><span>{label}</span><strong>{formatNumber(key === "DUPLICADA" ? duplicateCount : statusCounts[key] || 0)}</strong></div>)}
      {unclassifiedCount > 0 && <div className="trace-summary-card trace-summary-unclassified"><span>Sem classificação</span><strong>{formatNumber(unclassifiedCount)}</strong></div>}
      <div className="trace-summary-card"><span>Tentativas</span><strong>{formatNumber(summary?.total_execucoes ?? executions.length)}</strong></div>
    </div>
    <div className="execution-history">
      <strong>Histórico de processamento</strong>
      {loading ? <span>Carregando tentativas…</span> : executions.length ? executions.map((execution) => <span key={execution.id}>
        Tentativa {execution.numero} · {execution.status} · início {new Date(execution.iniciada_em).toLocaleString("pt-BR")}{execution.finalizada_em ? ` · fim ${new Date(execution.finalizada_em).toLocaleString("pt-BR")}` : ""}{execution.erro ? ` · ${execution.erro}` : ""}
      </span>) : <span>Nenhuma tentativa registrada para esta fonte.</span>}
    </div>
  </div>;
}
