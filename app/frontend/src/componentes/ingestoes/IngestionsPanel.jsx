import { useEffect, useState } from "react";
import EmptyState from "../ui/EmptyState.jsx";
import PanelHeader from "../ui/PanelHeader.jsx";
import { formatNumber } from "../../utils/format.js";
import { getErrorMessage } from "../../services/http";
import {
  downloadSanitizedIngestion,
  getIngestionExecutions,
  getIngestionSummary,
  getIngestionsPage,
  resumeIngestion,
  uploadIngestion,
} from "../../services/ingestoes";
import IngestionSources from "./IngestionSources.jsx";
import IngestionTraceTable from "./IngestionTraceTable.jsx";

export default function IngestionsPanel({ onApiStateChange }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [state, setState] = useState("loading");
  const [historyError, setHistoryError] = useState("");
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [revision, setRevision] = useState(0);
  const [selectedId, setSelectedId] = useState("");
  const [summary, setSummary] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [summaryLoading, setSummaryLoading] = useState(false);

  useEffect(() => {
    onApiStateChange(state);
  }, [onApiStateChange, state]);

  useEffect(() => {
    const controller = new AbortController();
    setState("loading"); setHistoryError("");
    getIngestionsPage(page, 10, controller.signal)
      .then((result) => { setData(result); setState("ready"); })
      .catch((cause) => { if (cause.name !== "AbortError") { setHistoryError(getErrorMessage(cause)); setState("error"); } });
    return () => controller.abort();
  }, [page, revision]);

  useEffect(() => {
    const processing = data?.items?.some((item) => item.status === "PROCESSANDO");
    if (!busy && !processing) return undefined;
    const interval = window.setInterval(() => setRevision((value) => value + 1), 10_000);
    return () => window.clearInterval(interval);
  }, [busy, data]);

  useEffect(() => {
    if (state !== "ready") return;
    const items = data?.items || [];
    if (!items.length) { setSelectedId(""); return; }
    if (!items.some((item) => item.id === selectedId)) setSelectedId(items[0].id);
  }, [data, selectedId, state]);

  useEffect(() => {
    if (!selectedId) { setSummary(null); setExecutions([]); return; }
    const controller = new AbortController();
    setSummary(null);
    setExecutions([]);
    setSummaryLoading(true);
    Promise.all([
      getIngestionSummary(selectedId, controller.signal),
      getIngestionExecutions(selectedId, controller.signal),
    ]).then(([sourceSummary, attempts]) => { setSummary(sourceSummary); setExecutions(attempts); })
      .catch((cause) => { if (cause.name !== "AbortError") setError(getErrorMessage(cause)); })
      .finally(() => { if (!controller.signal.aborted) setSummaryLoading(false); });
    return () => controller.abort();
  }, [selectedId, revision]);

  const selectedSource = data?.items?.find((item) => item.id === selectedId) || null;

  async function submit(event) {
    event.preventDefault();
    if (!file) return;
    const form = event.currentTarget;
    setBusy(true); setError("");
    setNotice("O envio e a ingestão podem levar alguns minutos; o processamento é salvo em lotes.");
    try {
      const result = await uploadIngestion(file);
      setNotice(`Ingestão ${result.ingestao_id}: ${formatNumber(result.linhas_processadas)} linha(s) inserida(s), ${formatNumber(result.bolsas_conflitantes)} bolsa(s) em conflito.`);
      setFile(null); form.reset(); setPage(1); setSelectedId(""); setState("loading");
      setRevision((value) => value + 1);
    } catch (cause) { setError(getErrorMessage(cause)); setSelectedId(""); setState("loading"); setRevision((value) => value + 1); }
    finally { setBusy(false); }
  }

  async function resume(id) {
    setBusy(true); setError(""); setNotice(`Retomando ingestão ${id}…`);
    try {
      const result = await resumeIngestion(id);
      setSelectedId(id);
      setNotice(`Retomada concluída: ${formatNumber(result.linhas_processadas)} linha(s) inserida(s), ${formatNumber(result.bolsas_conflitantes)} bolsa(s) em conflito.`);
      setRevision((value) => value + 1);
    } catch (cause) { setError(getErrorMessage(cause)); setRevision((value) => value + 1); }
    finally { setBusy(false); }
  }

  async function download(id) {
    try {
      const blob = await downloadSanitizedIngestion(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = `ingestao-${id}-com-lattes.csv`; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (cause) { setError(getErrorMessage(cause)); }
  }

  return <div className="ingestions-admin-page">
    <section className="panel ingest-upload-panel">
      <PanelHeader title="Nova ingestão" subtitle="O original fica arquivado; o arquivo final substitui os CPFs pelos Lattes." />
      <form className="upload-form" onSubmit={submit}>
        <label className="file-picker">{file ? file.name : "Selecione uma planilha CSV, XLS ou XLSX"}
          <input type="file" accept=".csv,.xls,.xlsx,.ods" onChange={(event) => setFile(event.target.files?.[0] || null)} />
        </label>
        <button className="primary-button" type="submit" disabled={!file || busy}>{busy ? "Processando…" : "Enviar e processar"}</button>
      </form>
      <p className="privacy-note">O CPF não é gravado no banco. A cópia original permanece no armazenamento da aplicação para retomada.</p>
    </section>
    {notice && <div className="ingest-notice" role="status">{notice}</div>}
    {error && <div className="api-error" role="alert"><span>{error}</span><button onClick={() => setError("")}>Fechar</button></div>}
    <IngestionSources
      data={data} state={state} error={historyError} selectedId={selectedId} busy={busy}
      selectedSource={selectedSource} summary={summary} executions={executions} summaryLoading={summaryLoading}
      onSelect={setSelectedId} onPageChange={setPage} onRefresh={() => setRevision((value) => value + 1)}
      onResume={resume} onDownload={download}
    />
    {selectedId && !selectedSource && state === "loading" ? <section className="panel"><EmptyState message="Carregando a fonte selecionada…" /></section> : null}
    {selectedId && <IngestionTraceTable sourceId={selectedId} revision={revision} />}
  </div>;
}
