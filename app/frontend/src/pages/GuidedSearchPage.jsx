import { useCallback, useEffect, useRef, useState } from "react";
import MessageContent from "../componentes/maria/MessageContent.jsx";
import { createConversation, getConversation, getMessages, listConversations, sendMessage } from "../services/maria";
import { getErrorMessage } from "../services/http";

const PENDING_ID = "pending";

// Rola só a área de mensagens, sem animação: até o fim ("end") ou até o início
// de uma mensagem.
function scrollMessages(container, target) {
  const node = target === "end" ? null : container.querySelector(`[data-message-id="${CSS.escape(target)}"]`);
  container.scrollTop = node ? node.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop : container.scrollHeight;
}

export default function GuidedSearchPage({ onApiStateChange }) {
  const [conversations, setConversations] = useState([]);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(null);
  const [query, setQuery] = useState("");
  const [loadingList, setLoadingList] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [listError, setListError] = useState("");
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  // Conversa cujas mensagens estão na tela; evita recarregá-la ao enviar.
  const shownConversationRef = useRef(null);
  const messagesRef = useRef(null);
  const scrollTargetRef = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoadingList(true); setListError(""); onApiStateChange("loading");
    listConversations(offset, controller.signal).then((result) => {
      setConversations(result.conversations); setTotal(result.total); onApiStateChange("ready");
    }).catch((cause) => {
      if (cause.name !== "AbortError") { setListError(getErrorMessage(cause)); onApiStateChange("error"); }
    }).finally(() => { if (!controller.signal.aborted) setLoadingList(false); });
    return () => controller.abort();
  }, [offset, refresh, onApiStateChange]);

  useEffect(() => {
    if (selected === shownConversationRef.current) return;
    shownConversationRef.current = null;
    if (!selected) { setMessages([]); setDetail(null); setLoadingMessages(false); return; }
    const controller = new AbortController();
    setMessages([]); setDetail(null); setLoadingMessages(true);
    Promise.all([getConversation(selected, controller.signal), getMessages(selected, controller.signal)])
      .then(([conversation, result]) => { shownConversationRef.current = selected; setDetail(conversation); setMessages(result.messages); })
      .catch((cause) => { if (cause.name !== "AbortError") setError(getErrorMessage(cause)); })
      .finally(() => { if (!controller.signal.aborted) setLoadingMessages(false); });
    return () => controller.abort();
  }, [selected]);

  useEffect(() => {
    const target = scrollTargetRef.current;
    if (!target || !messagesRef.current) return;
    scrollTargetRef.current = null;
    scrollMessages(messagesRef.current, target);
  }, [messages, pending]);

  // Atualiza a conversa na tela sem esvaziá-la; ignora o resultado se ela mudou.
  const syncConversation = useCallback((id, withMessages) => {
    Promise.all([getConversation(id), withMessages ? getMessages(id) : null]).then(([conversation, result]) => {
      if (shownConversationRef.current !== id) return;
      setDetail(conversation);
      if (result) setMessages(result.messages);
    }).catch(() => {});
  }, []);

  const submit = useCallback(async (value) => {
    const content = value.trim();
    if (!content || sending || loadingMessages) return;
    setSending(true); setError("");
    scrollTargetRef.current = "end";
    setPending(content);
    let id = selected;
    try {
      if (!id) {
        const conversation = await createConversation();
        id = conversation.id;
        shownConversationRef.current = id;
        setSelected(id);
      }
      const exchange = await sendMessage(id, content);
      setQuery("");
      if (shownConversationRef.current === id) {
        scrollTargetRef.current = exchange.assistant_message.id;
        setMessages((current) => [...current, exchange.user_message, exchange.assistant_message]);
        syncConversation(id, false);
      }
      setRefresh((n) => n + 1);
    } catch (cause) {
      setError(`${getErrorMessage(cause)} Atualize a conversa antes de reenviar, pois a mensagem pode ter sido recebida.`);
      if (id) {
        syncConversation(id, true);
        setRefresh((n) => n + 1);
      }
    } finally { setPending(null); setSending(false); }
  }, [selected, sending, loadingMessages, syncConversation]);

  return <section className="maria-panel maria-chat">
    <div><div className="eyebrow">ASSISTENTE MARIA</div><h2>Converse com a Maria</h2>
      <p>As conversas são compartilhadas pela API Maria e podem ser vistas por outras pessoas. Não inclua dados sensíveis.</p>
      <p>Os filtros do observatório não são enviados à Maria; inclua o recorte desejado na pergunta.</p></div>
    <div className="maria-layout">
      <aside className="maria-conversations" aria-label="Conversas">
        <button className="primary-button" disabled={sending} onClick={() => { setSelected(null); setQuery(""); setError(""); }}>Nova conversa</button>
        <strong>Conversas</strong>
        {loadingList ? <p>Carregando conversas…</p> : listError ? <div className="api-error" role="alert">{listError}<button onClick={() => setRefresh((n) => n + 1)}>Tentar novamente</button></div> : conversations.length === 0 ? <p>Nenhuma conversa encontrada.</p> : conversations.map((item) => <button className="maria-conversation" key={item.id} disabled={sending} aria-pressed={selected === item.id} onClick={() => { setError(""); setSelected(item.id); }}>{item.title || "Conversa sem título"}</button>)}
        <div className="pagination"><button disabled={loadingList || offset === 0} onClick={() => setOffset(Math.max(0, offset - 30))}>Anterior</button><span>{Math.min(offset + 1, total)}–{Math.min(offset + 30, total)} de {total}</span><button disabled={loadingList || offset + 30 >= total} onClick={() => setOffset(offset + 30)}>Próxima</button></div>
      </aside>
      <div className="maria-dialogue">
        <h3>{detail?.title || (selected ? "Conversa" : "Nova conversa")}</h3>
        {detail?.questions_limit != null && <small>Perguntas: {detail.questions_asked} de {detail.questions_limit}</small>}
        <div className="maria-messages" ref={messagesRef}>
          {loadingMessages ? <p>Carregando mensagens…</p> : messages.length === 0 && !sending ? <p>Envie uma pergunta para iniciar a conversa.</p> : messages.map((message) => <article className="maria-message" key={message.id} data-message-id={message.id}><strong>{message.role === "user" ? "Você" : "Maria"}</strong><MessageContent blocks={message.content} role={message.role} onSuggest={submit} disabled={sending || loadingMessages} /></article>)}
          {pending && <article className="maria-message maria-message-pending" data-message-id={PENDING_ID} aria-busy="true"><strong>Você</strong><p className="maria-message-text">{pending}</p></article>}
          {sending && <div className="maria-typing" role="status"><span className="maria-typing-dots" aria-hidden="true"><i /><i /><i /></span><span>A Maria está preparando sua resposta…</span></div>}
        </div>
        {error && <div className="api-error" role="alert"><span>{error}</span>{selected && <button onClick={() => getMessages(selected).then((result) => { setMessages(result.messages); setError(""); }).catch((cause) => setError(getErrorMessage(cause)))}>Atualizar conversa</button>}</div>}
        <form className="question-form" onSubmit={(event) => { event.preventDefault(); submit(query); }}><input value={query} maxLength={10000} disabled={sending} onChange={(event) => setQuery(event.target.value)} aria-label="Mensagem para Maria" placeholder="Escreva sua pergunta" /><button type="submit" disabled={sending || loadingMessages || !query.trim()}>{sending ? "Enviando…" : "Enviar"}</button></form>
      </div>
    </div>
  </section>;
}
