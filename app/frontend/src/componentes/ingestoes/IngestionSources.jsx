import EmptyState from "../ui/EmptyState.jsx";
import Pagination from "../ui/Pagination.jsx";
import PanelHeader from "../ui/PanelHeader.jsx";
import IngestionTraceSummary from "./IngestionTraceSummary.jsx";

export default function IngestionSources({
  data,
  state,
  error,
  selectedId,
  selectedSource,
  summary,
  executions,
  summaryLoading,
  busy,
  onSelect,
  onPageChange,
  onRefresh,
  onResume,
  onDownload,
  onRebuildTrace,
}) {
  return <section className="panel table-panel ingestion-sources-panel">
    <PanelHeader title="Fontes disponíveis" subtitle="Selecione uma ingestão para consultar as linhas e os motivos de cada resultado." action="Atualizar" onAction={onRefresh} />
    {state === "loading" ? <EmptyState message="Carregando fontes…" />
      : state === "error" ? <div className="api-error" role="alert"><span>{error || "Não foi possível carregar as ingestões."}</span><button onClick={onRefresh}>Tentar novamente</button></div>
        : !data?.items?.length ? <EmptyState message="Nenhuma ingestão registrada." /> : <>
          <div className="data-table-wrap"><table className="ingestion-source-table"><thead><tr><th>FONTE</th><th>SITUAÇÃO</th><th>AÇÕES</th></tr></thead><tbody>
            {data.items.map((batch) => <tr key={batch.id} className={selectedId === batch.id ? "selected-source-row" : ""}>
              <td><button className="source-select" onClick={() => onSelect(batch.id)} aria-pressed={selectedId === batch.id}><strong>{batch.nome_arquivo}</strong><small className="table-secondary">{new Date(batch.iniciada_em).toLocaleString("pt-BR")} · {batch.tipo.toUpperCase()}</small></button></td>
              <td><span className={`tag status-${batch.status.toLowerCase()}`}>{batch.status}</span></td>
              <td className="row-actions">{batch.status !== "CONCLUIDA" && <button disabled={busy} onClick={() => onResume(batch.id)}>Retomar</button>}{batch.status === "CONCLUIDA" && <button onClick={() => onDownload(batch.id)}>Baixar sem CPF</button>}{selectedId === batch.id && <button disabled={busy} onClick={() => onRebuildTrace(batch.id)}>Completar rastreabilidade</button>}</td>
            </tr>)}
          </tbody></table></div>
          <Pagination page={data.page} pages={data.pages} total={data.total} onChange={onPageChange} />
          <IngestionTraceSummary source={selectedSource} summary={summary} executions={executions} loading={summaryLoading} />
        </>}
  </section>;
}
