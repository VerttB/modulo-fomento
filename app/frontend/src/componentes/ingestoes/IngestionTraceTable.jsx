import { Fragment, useEffect, useState } from "react";
import EmptyState from "../ui/EmptyState.jsx";
import Pagination from "../ui/Pagination.jsx";
import PanelHeader from "../ui/PanelHeader.jsx";
import { getErrorMessage } from "../../services/http";
import { getIngestionLineEvents, getIngestionLines } from "../../services/ingestoes";

const labels = {
  PENDENTE: "Pendente",
  INSERIDA: "Inserida",
  INSERIDA_CONFLITO: "Inserida com conflito",
  DUPLICADA: "Duplicada",
  IGNORADA: "Ignorada",
  INVALIDA: "Inválida",
  ERRO: "Falha",
};

function lineReason(line) {
  if (line.status === "DUPLICADA" && line.linha_duplicada) {
    return `Duplicata da linha ${line.linha_duplicada} do arquivo.`;
  }
  return line.motivo || "—";
}

export default function IngestionTraceTable({ sourceId, revision }) {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState("");
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [data, setData] = useState(null);
  const [state, setState] = useState("loading");
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [events, setEvents] = useState({});
  const [eventsLoading, setEventsLoading] = useState(false);

  useEffect(() => { setPage(1); setExpandedId(null); setEvents({}); }, [sourceId, revision]);

  useEffect(() => {
    if (!sourceId) return;
    const controller = new AbortController();
    setState("loading"); setError("");
    getIngestionLines(sourceId, page, 25, filter, search, controller.signal)
      .then((result) => { setData(result); setState("ready"); })
      .catch((cause) => { if (cause.name !== "AbortError") { setError(getErrorMessage(cause)); setState("error"); } });
    return () => controller.abort();
  }, [sourceId, page, filter, search, revision]);

  async function toggleEvents(line) {
    if (expandedId === line.id) { setExpandedId(null); return; }
    setExpandedId(line.id);
    if (events[line.id]) return;
    setEventsLoading(true);
    try {
      const result = await getIngestionLineEvents(sourceId, line.id);
      setEvents((current) => ({ ...current, [line.id]: result }));
    } catch (cause) { setError(getErrorMessage(cause)); }
    finally { setEventsLoading(false); }
  }

  return <section className="panel table-panel ingestion-trace-table-panel">
    <PanelHeader title="Linhas da fonte" subtitle="A numeração corresponde à linha física do arquivo, incluindo o cabeçalho. Abra o histórico para acompanhar tentativas anteriores." />
    <form className="trace-filters" onSubmit={(event) => { event.preventDefault(); setPage(1); setSearch(searchDraft.trim()); }}>
      <select aria-label="Filtrar por resultado" value={filter} onChange={(event) => { setPage(1); setFilter(event.target.value); }}>
        <option value="">Todos os resultados</option>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      <input aria-label="Buscar linha" placeholder="Pesquisar Lattes, pesquisador, projeto ou instituição…" value={searchDraft} onChange={(event) => setSearchDraft(event.target.value)} />
      <button type="submit">Buscar</button>
    </form>
    {error && <div className="api-error" role="alert"><span>{error}</span><button onClick={() => setError("")}>Fechar</button></div>}
    {state === "loading" ? <EmptyState message="Carregando linhas da fonte…" />
      : state === "error" ? <EmptyState message="Não foi possível carregar as linhas." />
        : !data?.items?.length ? <EmptyState message="Nenhuma linha encontrada com esses filtros." /> : <>
          <div className="data-table-wrap"><table className="trace-lines-table"><thead><tr><th>LINHA NO ARQUIVO</th><th>RESULTADO</th><th>PESQUISADOR</th><th>PROJETO</th><th>INSTITUIÇÃO</th><th>VÍNCULO</th><th>PERÍODO</th><th>MOTIVO</th><th>PROCESSADA EM</th><th>HISTÓRICO</th></tr></thead><tbody>
            {data.items.map((line) => <Fragment key={line.id}>
              <tr>
                <td>{line.linha_origem}</td>
                <td><span className={`tag trace-status-${line.status.toLowerCase()}`}>{labels[line.status]}</span></td>
                <td>{line.pesquisador_nome || (line.lattes_id ? `Lattes ${line.lattes_id}` : "—")}</td>
                <td>{line.projeto_nome || "—"}</td>
                <td>{line.instituicao_nome || "—"}</td>
                <td>{line.modalidade ? <><span>{line.modalidade}</span>{line.bolsa_id && <small className="trace-conflict-note">Registro {line.bolsa_id.slice(0, 8)} · {line.bolsa_status}</small>}{line.is_conflict && <small className="trace-conflict-note">Revisão de conflito</small>}</> : "—"}</td>
                <td>{line.quando_iniciou || line.quando_terminou ? `${line.quando_iniciou || "…"} — ${line.quando_terminou || "…"}` : "—"}</td>
                <td>{lineReason(line)}</td>
                <td>{new Date(line.atualizada_em).toLocaleString("pt-BR")}</td>
                <td><button className="trace-history-button" onClick={() => toggleEvents(line)}>{expandedId === line.id ? "Ocultar" : "Ver histórico"}</button></td>
              </tr>
              {expandedId === line.id && <tr className="trace-events-row" key={`${line.id}-events`}><td colSpan="10">
                {line.bolsas_conflitantes?.length > 0 && <div className="trace-conflict-list"><strong>Registros de bolsistas relacionados ao conflito</strong>{line.bolsas_conflitantes.map((conflict) => <span key={conflict.id}>{conflict.modalidade || "Registro"} · {conflict.projeto_nome || "Projeto sem título"} · {conflict.quando_iniciou || "…"} — {conflict.quando_terminou || "…"} · {conflict.status} · {conflict.motivo}</span>)}</div>}
                {eventsLoading && !events[line.id] ? "Carregando histórico…" : events[line.id]?.length ? <div className="trace-events-list">{events[line.id].map((event) => <div key={event.id}>
                  <strong>{labels[event.status] || event.status}</strong><time>{new Date(event.criado_em).toLocaleString("pt-BR")}</time>
                  <span>{event.execucao_numero ? `Tentativa ${event.execucao_numero}` : "Tentativa"}{event.pesquisador_nome ? ` · ${event.pesquisador_nome}` : ""}{event.projeto_nome ? ` · ${event.projeto_nome}` : ""}</span>
                  {event.motivo && <small>{event.motivo}</small>}
                </div>)}</div> : "Nenhum histórico de tentativa registrado. Ingestões anteriores à rastreabilidade não têm eventos detalhados."}
              </td></tr>}
            </Fragment>)}
          </tbody></table></div>
          <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
        </>}
  </section>;
}
