import React, { useState, useCallback } from "react";
import {
  analyzeText,
  analyzeFile,
  selectFile,
  Preset,
  ALL_PRESETS,
  PRESET_LAYER1_FAST,
  AnalyzeTextResponse,
  AnalyzeFileResponse,
} from "./api";

type Mode = "text" | "file";

const styles = {
  container: {
    padding: 24,
    fontFamily: "system-ui, -apple-system, sans-serif",
    maxWidth: 1200,
    margin: "0 auto",
  } as React.CSSProperties,
  header: {
    marginBottom: 24,
    borderBottom: "1px solid #e0e0e0",
    paddingBottom: 16,
  } as React.CSSProperties,
  title: {
    margin: 0,
    fontSize: 24,
    fontWeight: 600,
  } as React.CSSProperties,
  subtitle: {
    margin: "8px 0 0 0",
    fontSize: 14,
    color: "#666",
  } as React.CSSProperties,
  modeSelector: {
    display: "flex",
    gap: 8,
    marginBottom: 20,
  } as React.CSSProperties,
  modeButton: (active: boolean) =>
    ({
      padding: "10px 20px",
      border: "1px solid #ccc",
      borderRadius: 6,
      background: active ? "#0066cc" : "#fff",
      color: active ? "#fff" : "#333",
      cursor: "pointer",
      fontWeight: active ? 600 : 400,
      transition: "all 0.2s",
    }) as React.CSSProperties,
  presetSelector: {
    marginBottom: 20,
  } as React.CSSProperties,
  presetSelect: {
    width: "100%",
    padding: "10px 12px",
    fontSize: 14,
    border: "1px solid #ccc",
    borderRadius: 6,
    background: "#fff",
  } as React.CSSProperties,
  mainGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 24,
  } as React.CSSProperties,
  panel: {
    background: "#f9f9f9",
    borderRadius: 8,
    padding: 16,
    border: "1px solid #e0e0e0",
  } as React.CSSProperties,
  panelTitle: {
    margin: "0 0 12px 0",
    fontSize: 16,
    fontWeight: 600,
  } as React.CSSProperties,
  textarea: {
    width: "100%",
    height: 200,
    padding: 12,
    fontSize: 14,
    fontFamily: "monospace",
    border: "1px solid #ccc",
    borderRadius: 6,
    resize: "vertical" as const,
    boxSizing: "border-box" as const,
  } as React.CSSProperties,
  fileDropZone: (isDragging: boolean) =>
    ({
      border: `2px dashed ${isDragging ? "#0066cc" : "#ccc"}`,
      borderRadius: 8,
      padding: 40,
      textAlign: "center" as const,
      background: isDragging ? "#f0f7ff" : "#fff",
      cursor: "pointer",
      transition: "all 0.2s",
    }) as React.CSSProperties,
  button: (primary: boolean, disabled: boolean) =>
    ({
      padding: "12px 24px",
      fontSize: 14,
      fontWeight: 600,
      border: "none",
      borderRadius: 6,
      cursor: disabled ? "not-allowed" : "pointer",
      background: disabled ? "#ccc" : primary ? "#0066cc" : "#666",
      color: "#fff",
      transition: "all 0.2s",
      marginTop: 12,
    }) as React.CSSProperties,
  statusBar: {
    marginTop: 16,
    padding: 12,
    background: "#fff",
    borderRadius: 6,
    border: "1px solid #e0e0e0",
    fontSize: 13,
  } as React.CSSProperties,
  summaryGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
    gap: 8,
    marginTop: 12,
  } as React.CSSProperties,
  summaryItem: {
    padding: 8,
    background: "#f0f0f0",
    borderRadius: 4,
    textAlign: "center" as const,
    fontSize: 12,
  } as React.CSSProperties,
  layerBadge: (layer: number) => {
    const colors: Record<number, string> = {
      1: "#4caf50",
      2: "#2196f3",
      3: "#ff9800",
    };
    return {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 12,
      fontSize: 11,
      fontWeight: 600,
      background: colors[layer] || "#666",
      color: "#fff",
      marginLeft: 8,
    } as React.CSSProperties;
  },
};

export function App() {
  const [mode, setMode] = useState<Mode>("text");
  const [preset, setPreset] = useState<Preset>(PRESET_LAYER1_FAST);
  const [text, setText] = useState(
    "Client John Smith (john.smith@example.com) has IBAN NL91ABNA0417164300 and phone +31 6 12345678.\n\nDr. Sarah Johnson from Amsterdam Medical Center reviewed the case on 15-03-2024."
  );
  const [result, setResult] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handlePresetChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const selected = ALL_PRESETS.find((p) => p.preset_id === e.target.value);
      if (selected) {
        setPreset(selected);
      }
    },
    []
  );

  const handleAnalyzeText = useCallback(async () => {
    if (!text.trim()) {
      setStatus("Please enter some text to analyze.");
      return;
    }

    setIsProcessing(true);
    setStatus("Analyzing...");
    setResult("");
    setSummary({});

    try {
      const resp: AnalyzeTextResponse = await analyzeText(text, preset);
      setResult(resp.redacted_text);
      setSummary(resp.summary);
      setStatus(
        `Run ${resp.run_id} completed. Found ${resp.findings_count} entities. Language: ${resp.language}. Artifacts: ${resp.run_folder}`
      );
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsProcessing(false);
    }
  }, [text, preset]);

  const handleSelectFile = useCallback(async () => {
    const path = await selectFile();
    if (path) {
      setSelectedFile(path);
    }
  }, []);

  const handleAnalyzeFile = useCallback(async () => {
    if (!selectedFile) {
      setStatus("Please select a file first.");
      return;
    }

    setIsProcessing(true);
    setStatus("Analyzing file...");
    setResult("");
    setSummary({});

    try {
      const resp: AnalyzeFileResponse = await analyzeFile(selectedFile, preset);
      setSummary(resp.summary);
      setStatus(
        `Run ${resp.run_id} completed. Found ${resp.findings_count} entities. Output: ${resp.output_path}`
      );
      setResult(`Redacted file saved to:\n${resp.output_path}`);
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIsProcessing(false);
    }
  }, [selectedFile, preset]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // Note: In Tauri, we'd need to handle this differently
      // For now, prompt user to use the file picker
      setStatus("Please use the 'Select File' button to choose files.");
    }
  }, []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>
          Legal Anonymizer
          <span style={styles.layerBadge(preset.layer)}>Layer {preset.layer}</span>
        </h1>
        <p style={styles.subtitle}>
          GDPR-compliant offline anonymization for legal documents
        </p>
      </header>

      {/* Mode Selector */}
      <div style={styles.modeSelector}>
        <button
          style={styles.modeButton(mode === "text")}
          onClick={() => setMode("text")}
        >
          Text Input
        </button>
        <button
          style={styles.modeButton(mode === "file")}
          onClick={() => setMode("file")}
        >
          File Upload
        </button>
      </div>

      {/* Preset Selector */}
      <div style={styles.presetSelector}>
        <select
          style={styles.presetSelect}
          value={preset.preset_id}
          onChange={handlePresetChange}
        >
          {ALL_PRESETS.map((p) => (
            <option key={p.preset_id} value={p.preset_id}>
              {p.name} - Confidence: {p.minimum_confidence}%
            </option>
          ))}
        </select>
      </div>

      <div style={styles.mainGrid}>
        {/* Input Panel */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>
            {mode === "text" ? "Input Text" : "Select File"}
          </h3>

          {mode === "text" ? (
            <>
              <textarea
                style={styles.textarea}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text to anonymize..."
              />
              <button
                style={styles.button(true, isProcessing || !text.trim())}
                onClick={handleAnalyzeText}
                disabled={isProcessing || !text.trim()}
              >
                {isProcessing ? "Processing..." : "Anonymize Text"}
              </button>
            </>
          ) : (
            <>
              <div
                style={styles.fileDropZone(isDragging)}
                onClick={handleSelectFile}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {selectedFile ? (
                  <div>
                    <strong>Selected:</strong>
                    <br />
                    {selectedFile.split(/[/\\]/).pop()}
                  </div>
                ) : (
                  <div>
                    Click to select a file
                    <br />
                    <small>(DOCX, PDF, TXT)</small>
                  </div>
                )}
              </div>
              <button
                style={styles.button(true, isProcessing || !selectedFile)}
                onClick={handleAnalyzeFile}
                disabled={isProcessing || !selectedFile}
              >
                {isProcessing ? "Processing..." : "Anonymize File"}
              </button>
            </>
          )}
        </div>

        {/* Output Panel */}
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Output</h3>
          <textarea
            style={styles.textarea}
            value={result}
            readOnly
            placeholder="Anonymized output will appear here..."
          />

          {/* Summary */}
          {Object.keys(summary).length > 0 && (
            <div style={styles.summaryGrid}>
              {Object.entries(summary).map(([entity, count]) => (
                <div key={entity} style={styles.summaryItem}>
                  <strong>{count}</strong>
                  <br />
                  {entity}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Status Bar */}
      {status && <div style={styles.statusBar}>{status}</div>}
    </div>
  );
}
