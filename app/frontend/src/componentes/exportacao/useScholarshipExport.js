import { useCallback, useRef, useState } from "react";
import { exportScholarshipSummary, exportScholarships } from "../../services/exportacoes";
import { getErrorMessage } from "../../services/http";

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function useScholarshipExport(filters, searchTerm) {
  const [exporting, setExporting] = useState(false);
  const [summaryExporting, setSummaryExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState("csv");
  const [exportError, setExportError] = useState("");
  const recordsActive = useRef(false);
  const summaryActive = useRef(false);

  const exportResults = useCallback(async () => {
    if (recordsActive.current) return;
    recordsActive.current = true;
    setExporting(true);
    setExportError("");
    try {
      const blob = await exportScholarships(filters, searchTerm, exportFormat);
      download(blob, `bolsistas-fapesb.${exportFormat}`);
    } catch (cause) { setExportError(getErrorMessage(cause)); }
    finally { recordsActive.current = false; setExporting(false); }
  }, [exportFormat, filters, searchTerm]);

  const exportSummary = useCallback(async (dimensions) => {
    if (summaryActive.current) return false;
    summaryActive.current = true;
    setSummaryExporting(true);
    setExportError("");
    try {
      const blob = await exportScholarshipSummary(filters, dimensions, exportFormat);
      const suffix = dimensions.length === 3 ? "todos" : dimensions.join("-");
      download(blob, `resumo-${suffix}-bolsistas-fapesb.${exportFormat}`);
      return true;
    } catch (cause) { setExportError(getErrorMessage(cause)); return false; }
    finally { summaryActive.current = false; setSummaryExporting(false); }
  }, [exportFormat, filters]);

  return { exporting, summaryExporting, exportFormat, setExportFormat, exportError, setExportError, exportResults, exportSummary };
}
