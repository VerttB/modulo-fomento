import { Info } from "lucide-react";

/**
 * Nota de leitura exibida abaixo de um gráfico, no tom editorial do protótipo
 * do Observatório: explica como interpretar o número, não apenas repeti-lo.
 */
export default function ReadingNote({ children }) {
  return (
    <p className="reading-note">
      <Info size={14} strokeWidth={1.9} aria-hidden="true" />
      <span>{children}</span>
    </p>
  );
}
