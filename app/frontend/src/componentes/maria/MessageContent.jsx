import { lazy, Suspense } from "react";
import ProductionCards from "./ProductionCards.jsx";
import ResearcherCards from "./ResearcherCards.jsx";

// Carregado sob demanda para não pesar no pacote das demais páginas.
const MarkdownText = lazy(() => import("./MarkdownText.jsx"));

function DataTable({ columns, rows, title, truncated }) {
  return <div className="maria-data">
    {title && <strong>{title}</strong>}
    <div className="maria-table-scroll"><table><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column.key}>{row[column.key] == null ? "—" : String(row[column.key])}</td>)}</tr>)}</tbody></table></div>
    {truncated && <small>Resultado limitado pela fonte.</small>}
  </div>;
}

// Só as respostas da Maria são Markdown; a pergunta do usuário é texto simples.
function TextBlock({ text, role }) {
  const plain = <p className="maria-message-text">{text}</p>;
  if (role === "user") return plain;
  return <Suspense fallback={plain}><MarkdownText text={text} /></Suspense>;
}

export default function MessageContent({ blocks, role, onSuggest, disabled }) {
  return blocks.map((block, index) => {
    if (block.type === "text") return <TextBlock key={index} text={block.text} role={role} />;
    if (block.type === "suggestions") return <div className="suggestions" key={index}>{block.questions.map((question) => <button key={question} type="button" disabled={disabled} onClick={() => onSuggest(question)}>{question}</button>)}</div>;
    if (block.type === "table") return <DataTable key={index} columns={block.columns} rows={block.rows} title={block.title} truncated={block.truncated} />;
    if (block.type === "chart") return <DataTable key={index} columns={[block.x, ...(block.group ? [block.group] : []), ...block.series]} rows={block.data} title={`${block.title} — dados do gráfico`} truncated={block.truncated} />;
    if (block.type === "researchers") return <ResearcherCards key={index} block={block} />;
    if (block.type === "productions") return <ProductionCards key={index} block={block} />;
    return <p key={index}>Conteúdo não reconhecido pela interface.</p>;
  });
}
