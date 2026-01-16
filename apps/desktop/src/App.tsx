import React, { useState, useCallback, useEffect } from "react";
import {
  analyzeText,
  analyzeFile,
  selectFile,
  Preset,
  ALL_PRESETS,
  PRESET_LAYER1_FAST,
  SUPPORTED_LANGUAGES,
  DEFAULT_ENTITIES,
  isDesktopApp,
  AnalyzeTextResponse,
  AnalyzeFileResponse,
} from "./api";
import { ModelManager, ModelSetupStatus, getModelSetupStatus } from "./ModelManager";
import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";
import * as XLSX from "xlsx";

type Mode = "text" | "file";
type View = "main" | "models" | "settings" | "info";
type QualityMode = "fast" | "accurate" | "thorough";

// Map quality modes to internal layer presets
const QUALITY_TO_PRESET: Record<QualityMode, string> = {
  fast: "layer1_fast",
  accurate: "layer2_accurate",
  thorough: "layer3_presidio",
};

const QUALITY_INFO: Record<QualityMode, { name: string; description: string }> = {
  fast: { name: "Fast", description: "Quick scan using pattern matching" },
  accurate: { name: "Accurate", description: "AI-powered detection for better results" },
  thorough: { name: "Thorough", description: "Maximum protection for sensitive documents" },
};

export function App() {
  const [view, setView] = useState<View>("main");
  const [mode, setMode] = useState<Mode>("text");
  const [quality, setQuality] = useState<QualityMode>("fast");
  const [preset, setPreset] = useState<Preset>({ ...PRESET_LAYER1_FAST });
  const [language, setLanguage] = useState("auto");
  const [text, setText] = useState("");
  const [result, setResult] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [entities, setEntities] = useState<Record<string, boolean>>({ ...DEFAULT_ENTITIES });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [modelStatus, setModelStatus] = useState<ModelSetupStatus | null>(null);
  const [showSetupPrompt, setShowSetupPrompt] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [globalWhitelist, setGlobalWhitelist] = useState("");
  const [globalBlacklist, setGlobalBlacklist] = useState("");
  const [languageWhitelists, setLanguageWhitelists] = useState<Record<string, string>>({});
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [settingsLang, setSettingsLang] = useState("en");

  const isDesktop = isDesktopApp();

  // Check model status on mount
  useEffect(() => {
    const status = getModelSetupStatus();
    setModelStatus(status);
    if (!status.ready && status.missingLayers.includes(1)) {
      setShowSetupPrompt(true);
    }
  }, []);

  // Update preset when quality changes
  useEffect(() => {
    const presetId = QUALITY_TO_PRESET[quality];
    const selected = ALL_PRESETS.find((p) => p.preset_id === presetId);
    if (selected) {
      setPreset({ ...selected });
    }
  }, [quality]);

  const getCurrentPreset = useCallback((): Preset => {
    const langWhitelists: Record<string, string[]> = {};
    for (const [lang, text] of Object.entries(languageWhitelists)) {
      const words = text.split("\n").map(s => s.trim()).filter(s => s);
      if (words.length > 0) langWhitelists[lang] = words;
    }

    return {
      ...preset,
      language_mode: language === "auto" ? "auto" : "fixed",
      language: language === "auto" ? undefined : language,
      entities_enabled: entities,
      whitelist: globalWhitelist.split("\n").filter((s) => s.trim()),
      blacklist: globalBlacklist.split("\n").filter((s) => s.trim()),
      language_whitelists: langWhitelists,
    };
  }, [preset, language, entities, globalWhitelist, globalBlacklist, languageWhitelists]);

  const handleAnalyze = useCallback(async () => {
    if (mode === "text" && !text.trim()) return;
    if (mode === "file" && !selectedFile) return;

    setIsProcessing(true);
    setResult("");
    setSummary({});
    setStatusMessage("");

    try {
      if (mode === "text") {
        const resp: AnalyzeTextResponse = await analyzeText(text, getCurrentPreset());
        setResult(resp.redacted_text);
        setSummary(resp.summary);
        const count = resp.findings_count;
        setStatusMessage(count > 0 ? `Found and protected ${count} item${count !== 1 ? 's' : ''}` : "No sensitive information found");
      } else {
        const resp: AnalyzeFileResponse = await analyzeFile(selectedFile!, getCurrentPreset());
        setSummary(resp.summary);
        setResult(`Protected file saved to:\n${resp.output_path}`);
        setStatusMessage(`Found and protected ${resp.findings_count} items`);
      }
    } catch (e: unknown) {
      setStatusMessage(`Something went wrong. Please try again.`);
    } finally {
      setIsProcessing(false);
    }
  }, [mode, text, selectedFile, getCurrentPreset]);

  const handleSelectFile = useCallback(async () => {
    if (!isDesktop) return;
    try {
      const path = await selectFile();
      if (path) setSelectedFile(path);
    } catch (e) {
      // Silently handle
    }
  }, [isDesktop]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch {
      // Silent fail
    }
  }, [result]);

  // Export as plain text
  const handleExportTxt = useCallback(() => {
    const blob = new Blob([result], { type: "text/plain;charset=utf-8" });
    saveAs(blob, `anonymized-${Date.now()}.txt`);
    setShowExportMenu(false);
  }, [result]);

  // Export as DOCX
  const handleExportDocx = useCallback(async () => {
    const paragraphs = result.split("\n").map(
      (line) =>
        new Paragraph({
          children: [new TextRun({ text: line, size: 24 })],
          spacing: { after: 120 },
        })
    );

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: "Anonymized Document",
                  bold: true,
                  size: 32,
                }),
              ],
              spacing: { after: 400 },
            }),
            new Paragraph({
              children: [
                new TextRun({
                  text: `Generated: ${new Date().toLocaleString()}`,
                  size: 20,
                  color: "666666",
                }),
              ],
              spacing: { after: 400 },
            }),
            ...paragraphs,
          ],
        },
      ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `anonymized-${Date.now()}.docx`);
    setShowExportMenu(false);
  }, [result]);

  // Export findings as XLSX
  const handleExportXlsx = useCallback(() => {
    const data = [
      ["Entity Type", "Count"],
      ...Object.entries(summary).map(([entity, count]) => [
        entity.replace(/_/g, " "),
        count,
      ]),
      [],
      ["Generated", new Date().toLocaleString()],
    ];

    const ws = XLSX.utils.aoa_to_sheet(data);
    ws["!cols"] = [{ wch: 25 }, { wch: 10 }];

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Findings Report");

    // Also add the anonymized text in a second sheet
    const textData = [["Anonymized Text"], [result]];
    const textWs = XLSX.utils.aoa_to_sheet(textData);
    textWs["!cols"] = [{ wch: 100 }];
    XLSX.utils.book_append_sheet(wb, textWs, "Anonymized Content");

    XLSX.writeFile(wb, `anonymized-report-${Date.now()}.xlsx`);
    setShowExportMenu(false);
  }, [result, summary]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  // Check if current quality mode has models ready
  const isQualityAvailable = (q: QualityMode): boolean => {
    if (!modelStatus) return q === "fast"; // Default fast always works
    const layer = q === "fast" ? 1 : q === "accurate" ? 2 : 3;
    return !modelStatus.missingLayers.includes(layer);
  };

  return (
    <div style={styles.app}>
      {/* Navigation */}
      <nav style={styles.nav}>
        <div style={styles.navLeft}>
          <div style={styles.logo}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <span style={styles.logoText}>Legal Anonymizer</span>
          </div>
        </div>
        <div style={styles.navCenter}>
          <button
            style={styles.navButton(view === "main")}
            onClick={() => setView("main")}
          >
            Anonymize
          </button>
          <button
            style={styles.navButton(view === "models")}
            onClick={() => setView("models")}
          >
            Setup
            {modelStatus && !modelStatus.ready && (
              <span style={styles.navBadge}>!</span>
            )}
          </button>
          <button
            style={styles.navButton(view === "settings")}
            onClick={() => setView("settings")}
          >
            Settings
          </button>
          <button
            style={styles.navButton(view === "info")}
            onClick={() => setView("info")}
          >
            Info
          </button>
        </div>
        <div style={styles.navRight}>
          {isDesktop ? (
            <span style={styles.statusPill}>Offline Ready</span>
          ) : (
            <span style={{ ...styles.statusPill, background: "#fef3c7", color: "#92400e" }}>Preview Mode</span>
          )}
        </div>
      </nav>

      {/* Setup Prompt */}
      {showSetupPrompt && view === "main" && (
        <div style={styles.setupPrompt}>
          <div style={styles.setupPromptContent}>
            <div style={styles.setupPromptIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4M12 8h.01" />
              </svg>
            </div>
            <div style={styles.setupPromptText}>
              <h3 style={styles.setupPromptTitle}>Quick Setup Required</h3>
              <p style={styles.setupPromptDesc}>
                Download the language models to start protecting your documents. Takes about 2 minutes.
              </p>
            </div>
            <div style={styles.setupPromptActions}>
              <button
                style={styles.setupButton}
                onClick={() => { setView("models"); setShowSetupPrompt(false); }}
              >
                Set Up Now
              </button>
              <button
                style={styles.setupButtonSecondary}
                onClick={() => setShowSetupPrompt(false)}
              >
                Later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main View */}
      {view === "main" && (
        <main style={styles.main}>
          {/* Mode Toggle */}
          <div style={styles.modeToggle}>
            <button
              style={styles.modeButton(mode === "text")}
              onClick={() => setMode("text")}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              Text
            </button>
            <button
              style={styles.modeButton(mode === "file")}
              onClick={() => setMode("file")}
              disabled={!isDesktop}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                <polyline points="13 2 13 9 20 9" />
              </svg>
              File
              {!isDesktop && <span style={styles.desktopBadge}>Desktop</span>}
            </button>
          </div>

          {/* Quality Selector */}
          <div style={styles.qualitySelector}>
            <span style={styles.qualityLabel}>Protection Level</span>
            <div style={styles.qualityOptions}>
              {(["fast", "accurate", "thorough"] as QualityMode[]).map((q) => {
                const available = isQualityAvailable(q);
                return (
                  <button
                    key={q}
                    style={styles.qualityButton(quality === q, available)}
                    onClick={() => available && setQuality(q)}
                    disabled={!available}
                  >
                    <span style={styles.qualityName}>{QUALITY_INFO[q].name}</span>
                    {!available && (
                      <span style={styles.qualitySetup}>Setup required</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Content Area */}
          <div style={styles.workspace}>
            {/* Input Panel */}
            <div style={styles.panel}>
              <div style={styles.panelHeader}>
                <span style={styles.panelTitle}>
                  {mode === "text" ? "Paste your text" : "Select a file"}
                </span>
                {mode === "text" && (
                  <button
                    style={styles.pasteButton}
                    onClick={async () => {
                      try {
                        const clipText = await navigator.clipboard.readText();
                        setText(clipText);
                      } catch {}
                    }}
                  >
                    Paste from clipboard
                  </button>
                )}
              </div>

              {mode === "text" ? (
                <textarea
                  style={styles.textarea}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste or type the text you want to protect..."
                />
              ) : (
                <div
                  style={styles.dropZone(isDragging, !isDesktop)}
                  onClick={handleSelectFile}
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                  onDrop={handleDrop}
                >
                  {selectedFile ? (
                    <div style={styles.selectedFile}>
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="1.5">
                        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                        <polyline points="13 2 13 9 20 9" />
                      </svg>
                      <span style={styles.fileName}>{selectedFile.split(/[/\\]/).pop()}</span>
                      <span style={styles.changeFile}>Click to change</span>
                    </div>
                  ) : (
                    <div style={styles.dropContent}>
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="1.5">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      <span style={styles.dropText}>Click to select a file</span>
                      <span style={styles.dropHint}>Supports PDF, DOCX, TXT</span>
                    </div>
                  )}
                </div>
              )}

              {/* Advanced Toggle */}
              <button
                style={styles.advancedToggle}
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <span>Advanced options</span>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  style={{ transform: showAdvanced ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {showAdvanced && (
                <div style={styles.advancedPanel}>
                  <div style={styles.advancedRow}>
                    <label style={styles.advancedLabel}>Language</label>
                    <select
                      style={styles.select}
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                    >
                      {SUPPORTED_LANGUAGES.map((lang) => (
                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Output Panel */}
            <div style={styles.panel}>
              <div style={styles.panelHeader}>
                <span style={styles.panelTitle}>Protected result</span>
                {result && (
                  <div style={styles.headerButtons}>
                    <button
                      style={styles.copyButton(copySuccess)}
                      onClick={handleCopy}
                    >
                      {copySuccess ? "Copied!" : "Copy"}
                    </button>
                    <div style={styles.exportWrapper}>
                      <button
                        style={styles.exportButton}
                        onClick={() => setShowExportMenu(!showExportMenu)}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Export
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      </button>
                      {showExportMenu && (
                        <div style={styles.exportMenu}>
                          <button style={styles.exportMenuItem} onClick={handleExportTxt}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                            </svg>
                            Plain Text (.txt)
                          </button>
                          <button style={styles.exportMenuItem} onClick={handleExportDocx}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                              <line x1="16" y1="13" x2="8" y2="13" />
                              <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                            Word Document (.docx)
                          </button>
                          <button style={styles.exportMenuItem} onClick={handleExportXlsx}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
                              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                              <line x1="3" y1="9" x2="21" y2="9" />
                              <line x1="3" y1="15" x2="21" y2="15" />
                              <line x1="9" y1="3" x2="9" y2="21" />
                            </svg>
                            Excel Report (.xlsx)
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <textarea
                style={{ ...styles.textarea, background: "#fafafa" }}
                value={result}
                readOnly
                placeholder="Your protected text will appear here..."
              />

              {/* Summary */}
              {Object.keys(summary).length > 0 && (
                <div style={styles.summary}>
                  {Object.entries(summary).map(([entity, count]) => (
                    <span key={entity} style={styles.summaryTag}>
                      {count} {entity.replace(/_/g, " ").toLowerCase()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action Button */}
          <div style={styles.actionArea}>
            <button
              style={styles.actionButton(isProcessing || (mode === "text" ? !text.trim() : !selectedFile))}
              onClick={handleAnalyze}
              disabled={isProcessing || (mode === "text" ? !text.trim() : !selectedFile)}
            >
              {isProcessing ? (
                <>
                  <span style={styles.spinner} />
                  Processing...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  Protect Document
                </>
              )}
            </button>
            {statusMessage && (
              <p style={styles.statusMessage}>{statusMessage}</p>
            )}
          </div>
        </main>
      )}

      {/* Models View */}
      {view === "models" && (
        <ModelManager
          isDesktop={isDesktop}
          onStatusChange={(msg) => setStatusMessage(msg)}
          onSetupComplete={() => {
            setModelStatus(getModelSetupStatus());
            setShowSetupPrompt(false);
          }}
        />
      )}

      {/* Settings View */}
      {view === "settings" && (
        <main style={styles.settingsMain}>
          <div style={styles.settingsHeader}>
            <h1 style={styles.settingsTitle}>Settings</h1>
            <p style={styles.settingsSubtitle}>Customize how documents are protected</p>
          </div>

          {/* Global Lists Section */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>Global Lists</h2>
            <p style={styles.sectionDesc}>These apply to all languages</p>

            <div style={styles.settingsGrid}>
              {/* Global Whitelist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  Skip List (Global)
                </h3>
                <p style={styles.cardDesc}>Words that should never be hidden, regardless of language</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={globalWhitelist}
                  onChange={(e) => setGlobalWhitelist(e.target.value)}
                  placeholder="Company names, product names, public figures...&#10;One per line"
                />
              </div>

              {/* Global Blacklist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                  </svg>
                  Always Hide (Global)
                </h3>
                <p style={styles.cardDesc}>Words that should always be hidden, even if not detected as PII</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={globalBlacklist}
                  onChange={(e) => setGlobalBlacklist(e.target.value)}
                  placeholder="Internal codes, specific client names...&#10;One per line"
                />
              </div>
            </div>
          </div>

          {/* Language-Specific Lists Section */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>Language-Specific Lists</h2>
            <p style={styles.sectionDesc}>
              Words that cause false positives in specific languages
            </p>

            {/* Language Selector */}
            <div style={styles.langSelectorRow}>
              <label style={styles.langSelectorLabel}>Select language:</label>
              <select
                style={styles.langDropdown}
                value={settingsLang}
                onChange={(e) => setSettingsLang(e.target.value)}
              >
                {SUPPORTED_LANGUAGES.filter(l => l.code !== "auto").map((lang) => {
                  const count = languageWhitelists[lang.code]?.split("\n").filter(s => s.trim()).length || 0;
                  return (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}{count > 0 ? ` (${count} terms)` : ""}
                    </option>
                  );
                })}
              </select>
            </div>

            <div style={styles.settingsGrid}>
              {/* Language-specific Whitelist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  Skip List ({SUPPORTED_LANGUAGES.find(l => l.code === settingsLang)?.name || settingsLang})
                </h3>
                <p style={styles.cardDesc}>
                  Normal words in this language that get falsely flagged as names
                </p>
                <textarea
                  style={styles.settingsTextarea}
                  value={languageWhitelists[settingsLang] || ""}
                  onChange={(e) => setLanguageWhitelists(prev => ({
                    ...prev,
                    [settingsLang]: e.target.value
                  }))}
                  placeholder={`Legal terms, common words...&#10;One per line`}
                />
              </div>

              {/* Language-specific Blacklist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  Always Hide ({SUPPORTED_LANGUAGES.find(l => l.code === settingsLang)?.name || settingsLang})
                </h3>
                <p style={styles.cardDesc}>
                  Terms specific to this language that should always be redacted
                </p>
                <textarea
                  style={styles.settingsTextarea}
                  value={(languageWhitelists[`${settingsLang}_blacklist`] || "")}
                  onChange={(e) => setLanguageWhitelists(prev => ({
                    ...prev,
                    [`${settingsLang}_blacklist`]: e.target.value
                  }))}
                  placeholder={`Language-specific terms to hide...&#10;One per line`}
                />
              </div>
            </div>
          </div>
        </main>
      )}

      {/* Info View */}
      {view === "info" && (
        <main style={styles.settingsMain}>
          <div style={styles.settingsHeader}>
            <h1 style={styles.settingsTitle}>Information</h1>
            <p style={styles.settingsSubtitle}>About Legal Anonymizer</p>
          </div>

          {/* License Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                <h2 style={styles.infoCardTitle}>License</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>
                  <strong>Elastic License 2.0 (ELv2)</strong>
                </p>
                <p style={styles.infoParagraph}>
                  This software is licensed under the Elastic License 2.0. You are free to use, modify, and distribute
                  this software for your own purposes, including commercial use within your organization.
                </p>
                <div style={styles.infoList}>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Use for any purpose, including commercial</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Modify the software for your own use</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Distribute within your organization</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCross}>✗</span>
                    <span>Offer as a hosted/managed service (SaaS)</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCross}>✗</span>
                    <span>Sell as a product</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Logging Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                <h2 style={styles.infoCardTitle}>Data Processing & Logging</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>
                  <strong>All processing happens locally on your device.</strong> No data is sent to external servers.
                </p>
                <p style={styles.infoParagraph}>
                  The application may log operational data locally for debugging purposes. This includes:
                </p>
                <ul style={styles.infoBulletList}>
                  <li>Processing timestamps and duration</li>
                  <li>Entity types detected (not the actual values)</li>
                  <li>Error messages and stack traces</li>
                  <li>Custom whitelist/blacklist terms you configure</li>
                </ul>
                <p style={styles.infoParagraph}>
                  <strong>Important:</strong> Terms you add to whitelists or blacklists are stored locally and may be
                  included in logs. Do not add sensitive personal data to these lists.
                </p>
              </div>
            </div>
          </div>

          {/* AI Act Compliance Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <h2 style={styles.infoCardTitle}>EU AI Act Compliance</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>
                  This tool is designed with the EU AI Act principles in mind:
                </p>
                <div style={styles.infoGrid}>
                  <div style={styles.infoGridItem}>
                    <h4 style={styles.infoGridTitle}>Transparency</h4>
                    <p style={styles.infoGridText}>
                      The tool clearly indicates when AI models are used (Accurate mode uses transformer-based NER).
                      All entity detections are shown to the user for review.
                    </p>
                  </div>
                  <div style={styles.infoGridItem}>
                    <h4 style={styles.infoGridTitle}>Human Oversight</h4>
                    <p style={styles.infoGridText}>
                      Users maintain full control. All anonymization suggestions can be reviewed, and users can add
                      custom whitelists to prevent over-redaction.
                    </p>
                  </div>
                  <div style={styles.infoGridItem}>
                    <h4 style={styles.infoGridTitle}>Risk Classification</h4>
                    <p style={styles.infoGridText}>
                      This tool assists with document anonymization and is intended as a support tool, not an
                      autonomous decision-maker. Final review responsibility remains with the user.
                    </p>
                  </div>
                  <div style={styles.infoGridItem}>
                    <h4 style={styles.infoGridTitle}>Data Minimization</h4>
                    <p style={styles.infoGridText}>
                      No document content is stored or transmitted. Processing occurs entirely on-device using
                      locally downloaded models.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* GDPR Compliance Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <h2 style={styles.infoCardTitle}>GDPR Compliance</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>
                  Legal Anonymizer supports GDPR compliance efforts by helping redact personal data from documents:
                </p>
                <div style={styles.infoList}>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span><strong>Local Processing:</strong> Documents never leave your device</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span><strong>No Data Retention:</strong> Processed content is not stored</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span><strong>PII Detection:</strong> Identifies names, addresses, phone numbers, emails, and more</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span><strong>Audit Trail:</strong> Export findings reports for compliance documentation</span>
                  </div>
                </div>
                <div style={styles.infoWarning}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <p>
                    <strong>Disclaimer:</strong> This tool assists with anonymization but does not guarantee complete
                    GDPR compliance. Always perform a manual review of anonymized documents. The tool may miss some
                    personal data or incorrectly flag non-personal data.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Version Info */}
          <div style={styles.versionInfo}>
            <p>Legal Anonymizer v0.1.0</p>
            <p>© 2024 Legal Anonymizer Contributors</p>
          </div>
        </main>
      )}
    </div>
  );
}

// ============================================================================
// Styles - Apple-inspired design system
// ============================================================================

const styles = {
  app: {
    minHeight: "100vh",
    background: "#f5f5f7",
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", system-ui, sans-serif',
    color: "#1d1d1f",
    WebkitFontSmoothing: "antialiased" as const,
  } as React.CSSProperties,

  // Navigation
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 24px",
    background: "rgba(255, 255, 255, 0.72)",
    backdropFilter: "saturate(180%) blur(20px)",
    borderBottom: "1px solid rgba(0, 0, 0, 0.08)",
    position: "sticky" as const,
    top: 0,
    zIndex: 100,
  } as React.CSSProperties,

  navLeft: {
    flex: 1,
  } as React.CSSProperties,

  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    color: "#1d1d1f",
  } as React.CSSProperties,

  logoText: {
    fontSize: 17,
    fontWeight: 600,
    letterSpacing: "-0.02em",
  } as React.CSSProperties,

  navCenter: {
    display: "flex",
    gap: 4,
    background: "rgba(0, 0, 0, 0.04)",
    borderRadius: 10,
    padding: 4,
  } as React.CSSProperties,

  navButton: (active: boolean) => ({
    padding: "8px 20px",
    fontSize: 14,
    fontWeight: 500,
    border: "none",
    borderRadius: 8,
    background: active ? "#fff" : "transparent",
    color: active ? "#1d1d1f" : "#6e6e73",
    cursor: "pointer",
    transition: "all 0.2s",
    boxShadow: active ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
    position: "relative" as const,
  }) as React.CSSProperties,

  navBadge: {
    position: "absolute" as const,
    top: 4,
    right: 8,
    width: 8,
    height: 8,
    background: "#ff3b30",
    borderRadius: "50%",
  } as React.CSSProperties,

  navRight: {
    flex: 1,
    display: "flex",
    justifyContent: "flex-end",
  } as React.CSSProperties,

  statusPill: {
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 500,
    background: "#dcfce7",
    color: "#166534",
    borderRadius: 20,
  } as React.CSSProperties,

  // Setup Prompt
  setupPrompt: {
    padding: "16px 24px",
    background: "#eff6ff",
    borderBottom: "1px solid #dbeafe",
  } as React.CSSProperties,

  setupPromptContent: {
    maxWidth: 960,
    margin: "0 auto",
    display: "flex",
    alignItems: "center",
    gap: 16,
  } as React.CSSProperties,

  setupPromptIcon: {
    flexShrink: 0,
  } as React.CSSProperties,

  setupPromptText: {
    flex: 1,
  } as React.CSSProperties,

  setupPromptTitle: {
    margin: 0,
    fontSize: 15,
    fontWeight: 600,
    color: "#1e40af",
  } as React.CSSProperties,

  setupPromptDesc: {
    margin: "4px 0 0",
    fontSize: 13,
    color: "#3b82f6",
  } as React.CSSProperties,

  setupPromptActions: {
    display: "flex",
    gap: 8,
  } as React.CSSProperties,

  setupButton: {
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: 600,
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.2s",
  } as React.CSSProperties,

  setupButtonSecondary: {
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: 500,
    background: "transparent",
    color: "#3b82f6",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
  } as React.CSSProperties,

  // Main Content
  main: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "40px 24px",
  } as React.CSSProperties,

  // Mode Toggle
  modeToggle: {
    display: "flex",
    justifyContent: "center",
    gap: 8,
    marginBottom: 32,
  } as React.CSSProperties,

  modeButton: (active: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "12px 24px",
    fontSize: 15,
    fontWeight: 500,
    border: "none",
    borderRadius: 12,
    background: active ? "#fff" : "transparent",
    color: active ? "#1d1d1f" : "#6e6e73",
    cursor: "pointer",
    transition: "all 0.2s",
    boxShadow: active ? "0 2px 8px rgba(0,0,0,0.08)" : "none",
    position: "relative" as const,
  }) as React.CSSProperties,

  desktopBadge: {
    position: "absolute" as const,
    top: -6,
    right: -6,
    padding: "2px 6px",
    fontSize: 9,
    fontWeight: 600,
    background: "#f3f4f6",
    color: "#6b7280",
    borderRadius: 4,
    textTransform: "uppercase" as const,
  } as React.CSSProperties,

  // Quality Selector
  qualitySelector: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 12,
    marginBottom: 32,
  } as React.CSSProperties,

  qualityLabel: {
    fontSize: 13,
    fontWeight: 500,
    color: "#6e6e73",
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
  } as React.CSSProperties,

  qualityOptions: {
    display: "flex",
    gap: 12,
  } as React.CSSProperties,

  qualityButton: (active: boolean, available: boolean) => ({
    padding: "16px 32px",
    fontSize: 15,
    fontWeight: 500,
    border: active ? "2px solid #3b82f6" : "2px solid transparent",
    borderRadius: 12,
    background: active ? "#eff6ff" : "#fff",
    color: available ? (active ? "#1d4ed8" : "#1d1d1f") : "#9ca3af",
    cursor: available ? "pointer" : "default",
    transition: "all 0.2s",
    opacity: available ? 1 : 0.6,
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 4,
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  }) as React.CSSProperties,

  qualityName: {
    fontWeight: 600,
  } as React.CSSProperties,

  qualitySetup: {
    fontSize: 11,
    color: "#9ca3af",
  } as React.CSSProperties,

  // Workspace
  workspace: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 24,
    marginBottom: 32,
  } as React.CSSProperties,

  panel: {
    background: "#fff",
    borderRadius: 16,
    padding: 24,
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  } as React.CSSProperties,

  panelHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  } as React.CSSProperties,

  panelTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: "#1d1d1f",
  } as React.CSSProperties,

  pasteButton: {
    padding: "6px 12px",
    fontSize: 13,
    fontWeight: 500,
    background: "#f5f5f7",
    color: "#6e6e73",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    transition: "all 0.2s",
  } as React.CSSProperties,

  copyButton: (copied: boolean) => ({
    padding: "6px 12px",
    fontSize: 13,
    fontWeight: 500,
    background: copied ? "#dcfce7" : "#f5f5f7",
    color: copied ? "#166534" : "#6e6e73",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    transition: "all 0.2s",
  }) as React.CSSProperties,

  headerButtons: {
    display: "flex",
    gap: 8,
    alignItems: "center",
  } as React.CSSProperties,

  exportWrapper: {
    position: "relative" as const,
  } as React.CSSProperties,

  exportButton: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 12px",
    fontSize: 13,
    fontWeight: 500,
    background: "#3b82f6",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    transition: "all 0.2s",
  } as React.CSSProperties,

  exportMenu: {
    position: "absolute" as const,
    top: "calc(100% + 8px)",
    right: 0,
    background: "#fff",
    borderRadius: 12,
    boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
    border: "1px solid #e5e5e5",
    overflow: "hidden",
    zIndex: 50,
    minWidth: 200,
  } as React.CSSProperties,

  exportMenuItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    width: "100%",
    padding: "12px 16px",
    fontSize: 14,
    fontWeight: 500,
    background: "transparent",
    color: "#1d1d1f",
    border: "none",
    borderBottom: "1px solid #f0f0f0",
    cursor: "pointer",
    transition: "background 0.15s",
    textAlign: "left" as const,
  } as React.CSSProperties,

  textarea: {
    width: "100%",
    height: 280,
    padding: 16,
    fontSize: 14,
    lineHeight: 1.6,
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif',
    border: "1px solid #e5e5e5",
    borderRadius: 12,
    resize: "none" as const,
    outline: "none",
    transition: "border-color 0.2s",
    boxSizing: "border-box" as const,
  } as React.CSSProperties,

  // Drop Zone
  dropZone: (dragging: boolean, disabled: boolean) => ({
    height: 280,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: `2px dashed ${dragging ? "#3b82f6" : "#e5e5e5"}`,
    borderRadius: 12,
    background: dragging ? "#eff6ff" : disabled ? "#fafafa" : "#fff",
    cursor: disabled ? "default" : "pointer",
    transition: "all 0.2s",
    opacity: disabled ? 0.5 : 1,
  }) as React.CSSProperties,

  dropContent: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 12,
  } as React.CSSProperties,

  dropText: {
    fontSize: 15,
    fontWeight: 500,
    color: "#6e6e73",
  } as React.CSSProperties,

  dropHint: {
    fontSize: 13,
    color: "#9ca3af",
  } as React.CSSProperties,

  selectedFile: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 8,
  } as React.CSSProperties,

  fileName: {
    fontSize: 15,
    fontWeight: 500,
    color: "#1d1d1f",
  } as React.CSSProperties,

  changeFile: {
    fontSize: 13,
    color: "#3b82f6",
  } as React.CSSProperties,

  // Advanced
  advancedToggle: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
    padding: "12px 0",
    marginTop: 8,
    fontSize: 13,
    fontWeight: 500,
    color: "#6e6e73",
    background: "transparent",
    border: "none",
    borderTop: "1px solid #f0f0f0",
    cursor: "pointer",
  } as React.CSSProperties,

  advancedPanel: {
    paddingTop: 12,
  } as React.CSSProperties,

  advancedRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 16,
  } as React.CSSProperties,

  advancedLabel: {
    fontSize: 13,
    fontWeight: 500,
    color: "#6e6e73",
  } as React.CSSProperties,

  select: {
    padding: "8px 12px",
    fontSize: 14,
    border: "1px solid #e5e5e5",
    borderRadius: 8,
    background: "#fff",
    outline: "none",
    minWidth: 180,
  } as React.CSSProperties,

  // Summary
  summary: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 8,
    marginTop: 16,
    paddingTop: 16,
    borderTop: "1px solid #f0f0f0",
  } as React.CSSProperties,

  summaryTag: {
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 500,
    background: "#f0fdf4",
    color: "#166534",
    borderRadius: 6,
  } as React.CSSProperties,

  // Action Area
  actionArea: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 12,
  } as React.CSSProperties,

  actionButton: (disabled: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "16px 48px",
    fontSize: 17,
    fontWeight: 600,
    background: disabled ? "#e5e5e5" : "linear-gradient(180deg, #3b82f6 0%, #2563eb 100%)",
    color: disabled ? "#9ca3af" : "#fff",
    border: "none",
    borderRadius: 14,
    cursor: disabled ? "default" : "pointer",
    transition: "all 0.2s",
    boxShadow: disabled ? "none" : "0 4px 14px rgba(59, 130, 246, 0.4)",
  }) as React.CSSProperties,

  spinner: {
    width: 16,
    height: 16,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTopColor: "#fff",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  } as React.CSSProperties,

  statusMessage: {
    fontSize: 14,
    color: "#6e6e73",
    margin: 0,
  } as React.CSSProperties,

  // Settings
  settingsMain: {
    maxWidth: 900,
    margin: "0 auto",
    padding: "40px 24px",
  } as React.CSSProperties,

  settingsHeader: {
    marginBottom: 32,
  } as React.CSSProperties,

  settingsTitle: {
    margin: 0,
    fontSize: 28,
    fontWeight: 600,
    letterSpacing: "-0.02em",
  } as React.CSSProperties,

  settingsSubtitle: {
    margin: "8px 0 0",
    fontSize: 15,
    color: "#6e6e73",
  } as React.CSSProperties,

  settingsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 20,
  } as React.CSSProperties,

  settingsCard: {
    background: "#fff",
    borderRadius: 16,
    padding: 24,
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  } as React.CSSProperties,

  cardTitle: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    margin: "0 0 8px",
    fontSize: 17,
    fontWeight: 600,
  } as React.CSSProperties,

  cardDesc: {
    margin: "0 0 16px",
    fontSize: 13,
    color: "#6e6e73",
  } as React.CSSProperties,

  settingsTextarea: {
    width: "100%",
    height: 120,
    padding: 12,
    fontSize: 13,
    fontFamily: "monospace",
    border: "1px solid #e5e5e5",
    borderRadius: 8,
    resize: "vertical" as const,
    outline: "none",
    boxSizing: "border-box" as const,
  } as React.CSSProperties,

  settingsSection: {
    marginBottom: 40,
  } as React.CSSProperties,

  sectionTitle: {
    margin: "0 0 8px",
    fontSize: 20,
    fontWeight: 600,
    color: "#1d1d1f",
  } as React.CSSProperties,

  sectionDesc: {
    margin: "0 0 20px",
    fontSize: 14,
    color: "#6e6e73",
  } as React.CSSProperties,

  langSelector: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 8,
    marginBottom: 20,
  } as React.CSSProperties,

  langButton: (active: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 500,
    background: active ? "#3b82f6" : "#fff",
    color: active ? "#fff" : "#1d1d1f",
    border: active ? "1px solid #3b82f6" : "1px solid #e5e5e5",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.2s",
  }) as React.CSSProperties,

  langCount: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    minWidth: 18,
    height: 18,
    padding: "0 5px",
    fontSize: 11,
    fontWeight: 600,
    background: "rgba(255,255,255,0.2)",
    borderRadius: 9,
  } as React.CSSProperties,

  // Language dropdown styles
  langSelectorRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 20,
  } as React.CSSProperties,

  langSelectorLabel: {
    fontSize: 14,
    fontWeight: 500,
    color: "#6e6e73",
  } as React.CSSProperties,

  langDropdown: {
    padding: "10px 16px",
    fontSize: 14,
    fontWeight: 500,
    border: "1px solid #e5e5e5",
    borderRadius: 10,
    background: "#fff",
    color: "#1d1d1f",
    outline: "none",
    cursor: "pointer",
    minWidth: 220,
    transition: "border-color 0.2s",
  } as React.CSSProperties,

  // Info page styles
  infoSection: {
    marginBottom: 24,
  } as React.CSSProperties,

  infoCard: {
    background: "#fff",
    borderRadius: 16,
    padding: 28,
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  } as React.CSSProperties,

  infoCardHeader: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 16,
  } as React.CSSProperties,

  infoCardTitle: {
    margin: 0,
    fontSize: 20,
    fontWeight: 600,
    color: "#1d1d1f",
  } as React.CSSProperties,

  infoCardContent: {
    paddingLeft: 36,
  } as React.CSSProperties,

  infoParagraph: {
    margin: "0 0 12px",
    fontSize: 14,
    lineHeight: 1.6,
    color: "#3d3d3f",
  } as React.CSSProperties,

  infoList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 10,
    marginTop: 16,
  } as React.CSSProperties,

  infoListItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
    fontSize: 14,
    color: "#3d3d3f",
  } as React.CSSProperties,

  infoCheck: {
    color: "#10b981",
    fontWeight: 600,
    fontSize: 16,
    flexShrink: 0,
  } as React.CSSProperties,

  infoCross: {
    color: "#ef4444",
    fontWeight: 600,
    fontSize: 16,
    flexShrink: 0,
  } as React.CSSProperties,

  infoBulletList: {
    margin: "8px 0 16px 20px",
    padding: 0,
    fontSize: 14,
    lineHeight: 1.8,
    color: "#3d3d3f",
  } as React.CSSProperties,

  infoGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 20,
    marginTop: 16,
  } as React.CSSProperties,

  infoGridItem: {
    background: "#f9fafb",
    borderRadius: 12,
    padding: 16,
  } as React.CSSProperties,

  infoGridTitle: {
    margin: "0 0 8px",
    fontSize: 15,
    fontWeight: 600,
    color: "#1d1d1f",
  } as React.CSSProperties,

  infoGridText: {
    margin: 0,
    fontSize: 13,
    lineHeight: 1.5,
    color: "#6e6e73",
  } as React.CSSProperties,

  infoWarning: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    marginTop: 20,
    padding: 16,
    background: "#fef3c7",
    borderRadius: 12,
    color: "#92400e",
    fontSize: 13,
    lineHeight: 1.5,
  } as React.CSSProperties,

  versionInfo: {
    textAlign: "center" as const,
    padding: "40px 0",
    fontSize: 13,
    color: "#9ca3af",
  } as React.CSSProperties,
};

