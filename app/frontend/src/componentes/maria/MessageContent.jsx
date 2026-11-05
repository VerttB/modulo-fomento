function DataTable({ columns, rows, title, truncated }) {
  return <div className="maria-data">
    {title && <strong>{title}</strong>}
    <div className="maria-table-scroll"><table><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column.key}>{row[column.key] == null ? "—" : String(row[column.key])}</td>)}</tr>)}</tbody></table></div>
    {truncated && <small>Resultado limitado pela fonte.</small>}
  </div>;
}

export default function MessageContent({ blocks, onSuggest, disabled }) {
  return blocks.map((block, index) => {
    if (block.type === "text") return <p className="maria-message-text" key={index}>{block.text}</p>;
    if (block.type === "suggestions") return <div className="suggestions" key={index}>{block.questions.map((question) => <button key={question} type="button" disabled={disabled} onClick={() => onSuggest(question)}>{question}</button>)}</div>;
    if (block.type === "table") return <DataTable key={index} columns={block.columns} rows={block.rows} title={block.title} truncated={block.truncated} />;
    if (block.type === "chart") return <DataTable key={index} columns={[block.x, ...(block.group ? [block.group] : []), ...block.series]} rows={block.data} title={`${block.title} — dados do gráfico`} truncated={block.truncated} />;
    return <p key={index}>Conteúdo não reconhecido pela interface.</p>;
  });
}
