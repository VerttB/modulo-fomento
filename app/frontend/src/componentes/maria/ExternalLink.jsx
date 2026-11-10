export default function ExternalLink({ href, children }) {
  return <a className="maria-card-link" href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
}
