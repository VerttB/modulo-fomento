import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Sem rehype-raw, HTML presente no texto não é interpretado, e o
// react-markdown descarta URLs com esquemas perigosos (ex.: javascript:).
const components = {
  a: ({ node, href, children, ...props }) => href
    ? <a {...props} href={href} target="_blank" rel="noopener noreferrer">{children}</a>
    : <span>{children}</span>,
  table: ({ node, ...props }) => <div className="maria-table-scroll"><table {...props} /></div>,
};

const remarkPlugins = [remarkGfm];

export default function MarkdownText({ text }) {
  return <div className="maria-markdown">
    <Markdown remarkPlugins={remarkPlugins} components={components}>{text}</Markdown>
  </div>;
}
