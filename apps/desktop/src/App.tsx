import React, { useState, useCallback, useEffect } from "react";
import { ErrorBoundary } from "./ErrorBoundary";
import {
  analyzeText,
  analyzeFile,
  selectFile,
  Preset,
  ALL_PRESETS,
  PRESET_LAYER1_FAST,
  SUPPORTED_LANGUAGES,
  DEFAULT_ENTITIES,
  DEFAULT_LANGUAGE_WHITELISTS,
  isDesktopApp,
  getApiMode,
  AnalyzeTextResponse,
  AnalyzeFileResponse,
  FindingItem,
  UncertaintyPolicy,
  PseudonymStyle,
  LanguageMode,
} from "./api";
import { t, UI_LANGUAGES, detectUILanguage, saveUILanguage, LangCode } from "./i18n";
import { ModelManager, ModelSetupStatus, getModelSetupStatus } from "./ModelManager";
import { Document, Packer, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";
import * as XLSX from "xlsx";
import "./styles.css";

const APP_VERSION = import.meta.env.VITE_APP_VERSION ?? "0.1.0";

type Mode = "text" | "file";
type View = "main" | "models" | "settings" | "info";
type QualityMode = "fast" | "accurate" | "thorough";
type ResultView = "anonymized" | "highlight";

// Map quality modes to internal layer presets — values must match preset_id fields in ALL_PRESETS
const QUALITY_TO_PRESET: Record<QualityMode, string> = {
  fast: "layer1_fast_legal_scrub",
  accurate: "layer2_accurate_legal_review",
  thorough: "layer3_regulatory_standard",
};

// Quality mode i18n keys — resolved at render time via t()
const QUALITY_NAME_KEY: Record<QualityMode, "quality_fast" | "quality_accurate" | "quality_thorough"> = {
  fast: "quality_fast",
  accurate: "quality_accurate",
  thorough: "quality_thorough",
};

// Colors for highlighting different PII types
const ENTITY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  PERSON: { bg: "#fef3c7", border: "#f59e0b", text: "#92400e" },
  EMAIL: { bg: "#dbeafe", border: "#3b82f6", text: "#1e40af" },
  PHONE_NUMBER: { bg: "#dcfce7", border: "#22c55e", text: "#166534" },
  BANK_ACCOUNT: { bg: "#fce7f3", border: "#ec4899", text: "#9d174d" },
  CREDIT_CARD: { bg: "#fee2e2", border: "#ef4444", text: "#991b1b" },
  NATIONAL_ID: { bg: "#fee2e2", border: "#ef4444", text: "#991b1b" },
  PASSPORT_NUMBER: { bg: "#fef3c7", border: "#f59e0b", text: "#92400e" },
  DATE: { bg: "#e0e7ff", border: "#6366f1", text: "#3730a3" },
  DATE_OF_BIRTH: { bg: "#fae8ff", border: "#d946ef", text: "#86198f" },
  ADDRESS: { bg: "#ccfbf1", border: "#14b8a6", text: "#115e59" },
  IP_ADDRESS: { bg: "#f3e8ff", border: "#a855f7", text: "#6b21a8" },
  ORGANIZATION: { bg: "#e0f2fe", border: "#0ea5e9", text: "#0369a1" },
  LOCATION: { bg: "#d1fae5", border: "#10b981", text: "#065f46" },
  URL: { bg: "#f1f5f9", border: "#64748b", text: "#334155" },
  MEDICAL_ID: { bg: "#fee2e2", border: "#ef4444", text: "#991b1b" },
  VEHICLE_ID: { bg: "#fff7ed", border: "#f97316", text: "#9a3412" },
  MONEY: { bg: "#ecfdf5", border: "#10b981", text: "#047857" },
};

const DEFAULT_ENTITY_COLOR = { bg: "#f3f4f6", border: "#9ca3af", text: "#374151" };

// ============================================================================
// LocalStorage persistence
// ============================================================================

const LS_KEY = "la_settings";

interface PersistedSettings {
  qualityMode: QualityMode;
  mode: Mode;
  uiLang: LangCode;
  globalWhitelist: string;
  globalBlacklist: string;
  entitiesEnabled: Record<string, boolean>;
  minimumConfidence: number;
  uncertaintyPolicy: UncertaintyPolicy;
  pseudonymStyle: PseudonymStyle;
  languageMode: LanguageMode;
  selectedLanguage: string;
}

const DEFAULT_SETTINGS: PersistedSettings = {
  qualityMode: "fast",
  mode: "text",
  uiLang: "en",
  globalWhitelist: "",
  globalBlacklist: "",
  entitiesEnabled: { ...DEFAULT_ENTITIES },
  minimumConfidence: PRESET_LAYER1_FAST.minimum_confidence,
  uncertaintyPolicy: PRESET_LAYER1_FAST.uncertainty_policy,
  pseudonymStyle: PRESET_LAYER1_FAST.pseudonym_style,
  languageMode: PRESET_LAYER1_FAST.language_mode,
  selectedLanguage: "auto",
};

function loadSettings(): PersistedSettings {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return { ...DEFAULT_SETTINGS, entitiesEnabled: { ...DEFAULT_ENTITIES } };
    const parsed = JSON.parse(raw) as Partial<PersistedSettings>;
    return {
      qualityMode: parsed.qualityMode ?? DEFAULT_SETTINGS.qualityMode,
      mode: parsed.mode ?? DEFAULT_SETTINGS.mode,
      uiLang: (parsed.uiLang ?? DEFAULT_SETTINGS.uiLang) as LangCode,
      globalWhitelist: parsed.globalWhitelist ?? DEFAULT_SETTINGS.globalWhitelist,
      globalBlacklist: parsed.globalBlacklist ?? DEFAULT_SETTINGS.globalBlacklist,
      entitiesEnabled: parsed.entitiesEnabled ?? { ...DEFAULT_ENTITIES },
      minimumConfidence: parsed.minimumConfidence ?? DEFAULT_SETTINGS.minimumConfidence,
      uncertaintyPolicy: parsed.uncertaintyPolicy ?? DEFAULT_SETTINGS.uncertaintyPolicy,
      pseudonymStyle: parsed.pseudonymStyle ?? DEFAULT_SETTINGS.pseudonymStyle,
      languageMode: parsed.languageMode ?? DEFAULT_SETTINGS.languageMode,
      selectedLanguage: parsed.selectedLanguage ?? DEFAULT_SETTINGS.selectedLanguage,
    };
  } catch {
    return { ...DEFAULT_SETTINGS, entitiesEnabled: { ...DEFAULT_ENTITIES } };
  }
}

function saveSettings(settings: PersistedSettings): void {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(settings));
  } catch {
    // Quota exceeded or private mode — silently ignore
  }
}

/** Component to display original text with highlighted PII */
function HighlightView({ originalText, findings, uiLang = "en" }: { originalText: string; findings: FindingItem[]; uiLang?: string }) {
  if (!findings || findings.length === 0) {
    return (
      <div style={highlightStyles.container}>
        <div style={highlightStyles.noFindings}>{t(uiLang as LangCode, "hl_no_findings")}</div>
      </div>
    );
  }

  // Sort by start, then by span length descending so wider spans take priority
  const sortedFindings = [...findings]
    .filter(f => f.start !== null && f.end !== null && (f.end ?? 0) > (f.start ?? 0))
    .sort((a, b) => {
      const startDiff = (a.start ?? 0) - (b.start ?? 0);
      if (startDiff !== 0) return startDiff;
      return (b.end ?? 0) - (a.end ?? 0); // wider span first
    });

  // Resolve overlaps: once a character range is consumed, skip any finding that
  // begins before the current cursor. This prevents corrupted or duplicated text.
  const resolvedFindings: FindingItem[] = [];
  let cursor = 0;
  for (const finding of sortedFindings) {
    const start = finding.start ?? 0;
    const end = finding.end ?? 0;
    if (start < cursor) continue; // fully overlapped — skip
    resolvedFindings.push(finding);
    cursor = end;
  }

  // Build segments: alternating between plain text and highlighted PII
  const segments: Array<{ text: string; finding?: FindingItem }> = [];
  let lastEnd = 0;

  for (const finding of resolvedFindings) {
    const start = finding.start ?? 0;
    const end = finding.end ?? 0;

    if (start > lastEnd) {
      segments.push({ text: originalText.slice(lastEnd, start) });
    }

    segments.push({ text: originalText.slice(start, end), finding });
    lastEnd = end;
  }

  if (lastEnd < originalText.length) {
    segments.push({ text: originalText.slice(lastEnd) });
  }

  return (
    <div style={highlightStyles.container}>
      <div style={highlightStyles.textContainer}>
        {segments.map((segment, idx) => {
          if (segment.finding) {
            const colors = ENTITY_COLORS[segment.finding.entity_type] || DEFAULT_ENTITY_COLOR;
            const label = segment.finding.entity_type.replace(/_/g, " ");
            return (
              <React.Fragment key={idx}>
                <span
                  style={{
                    backgroundColor: colors.bg,
                    border: `1px solid ${colors.border}`,
                    borderRadius: 3,
                    padding: "1px 4px",
                    cursor: "help",
                    display: "inline",
                  }}
                  title={`${label} — ${segment.finding.confidence}% confidence`}
                >
                  {segment.text}
                </span>
                <span
                  style={{
                    display: "inline-block",
                    fontSize: 9,
                    fontWeight: 700,
                    color: "#fff",
                    backgroundColor: colors.border,
                    borderRadius: 3,
                    padding: "1px 4px",
                    marginLeft: 2,
                    marginRight: 3,
                    verticalAlign: "middle",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    lineHeight: 1.6,
                    whiteSpace: "nowrap",
                  }}
                >
                  {label}
                </span>
              </React.Fragment>
            );
          }
          return <span key={idx}>{segment.text}</span>;
        })}
      </div>

      {/* Legend */}
      <div style={highlightStyles.legend}>
        <span style={highlightStyles.legendTitle}>{t(uiLang as LangCode, "hl_legend")}</span>
        {[...new Set(sortedFindings.map(f => f.entity_type))].map(type => {
          const colors = ENTITY_COLORS[type] || DEFAULT_ENTITY_COLOR;
          return (
            <span
              key={type}
              style={{
                ...highlightStyles.legendItem,
                backgroundColor: colors.bg,
                borderColor: colors.border,
                color: colors.text,
              }}
            >
              {type.replace(/_/g, " ")}
            </span>
          );
        })}
      </div>
    </div>
  );
}

const highlightStyles = {
  container: {
    padding: 16,
    background: "#fff",
    borderRadius: 8,
    border: "1px solid #e5e7eb",
    minHeight: 200,
    maxHeight: 420,
    overflow: "auto",
  } as React.CSSProperties,
  textContainer: {
    fontFamily: "system-ui, -apple-system, sans-serif",
    fontSize: 14,
    lineHeight: 1.8,
    whiteSpace: "pre-wrap" as const,
    wordBreak: "break-word" as const,
  } as React.CSSProperties,
  noFindings: {
    color: "#6b7280",
    fontStyle: "italic",
    padding: 20,
    textAlign: "center" as const,
  } as React.CSSProperties,
  legend: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 8,
    marginTop: 16,
    paddingTop: 12,
    borderTop: "1px solid #e5e7eb",
    alignItems: "center",
  } as React.CSSProperties,
  legendTitle: {
    fontSize: 12,
    fontWeight: 600,
    color: "#374151",
    marginRight: 4,
  } as React.CSSProperties,
  legendItem: {
    fontSize: 10,
    fontWeight: 500,
    padding: "2px 8px",
    borderRadius: 4,
    border: "1px solid",
  } as React.CSSProperties,
};

export function App() {
  // Load persisted settings once on mount
  const [_initialSettings] = useState<PersistedSettings>(() => {
    const saved = loadSettings();
    // uiLang: prefer saved value, but fall back to browser detection if never saved
    const rawLs = (() => { try { return localStorage.getItem(LS_KEY); } catch { return null; } })();
    if (!rawLs) saved.uiLang = detectUILanguage();
    return saved;
  });

  const [view, setView] = useState<View>("main");
  const [mode, setMode] = useState<Mode>(_initialSettings.mode);
  const [quality, setQuality] = useState<QualityMode>(_initialSettings.qualityMode);
  const [preset, setPreset] = useState<Preset>({ ...PRESET_LAYER1_FAST });
  const [language, setLanguage] = useState(_initialSettings.selectedLanguage);
  const [text, setText] = useState("");
  const [result, setResult] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [entities, setEntities] = useState<Record<string, boolean>>(_initialSettings.entitiesEnabled);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [modelStatus, setModelStatus] = useState<ModelSetupStatus | null>(null);
  const [showSetupPrompt, setShowSetupPrompt] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [modelsStatusMessage, setModelsStatusMessage] = useState("");
  const [globalWhitelist, setGlobalWhitelist] = useState(_initialSettings.globalWhitelist);
  const [globalBlacklist, setGlobalBlacklist] = useState(_initialSettings.globalBlacklist);
  const [languageWhitelists, setLanguageWhitelists] = useState<Record<string, string>>(
    () => Object.fromEntries(
      Object.entries(DEFAULT_LANGUAGE_WHITELISTS).map(([lang, words]) => [lang, words.join("\n")])
    )
  );
  const [languageBlacklists, setLanguageBlacklists] = useState<Record<string, string>>({});
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [settingsLang, setSettingsLang] = useState("en");
  const [findings, setFindings] = useState<FindingItem[]>([]);
  const [resultView, setResultView] = useState<ResultView>("anonymized");
  const [uiLang, setUiLang] = useState<LangCode>(_initialSettings.uiLang);
  // "auto" means auto-detect; any other code is the fixed default for DOCX/PDF
  const [fileLanguage, setFileLanguage] = useState<string>("auto");

  // Settings that override the base preset values
  const [minimumConfidence, setMinimumConfidence] = useState<number>(_initialSettings.minimumConfidence);
  const [uncertaintyPolicy, setUncertaintyPolicy] = useState<UncertaintyPolicy>(_initialSettings.uncertaintyPolicy);
  const [pseudonymStyle, setPseudonymStyle] = useState<PseudonymStyle>(_initialSettings.pseudonymStyle);
  const [languageMode, setLanguageMode] = useState<LanguageMode>(_initialSettings.languageMode);

  const isDesktop = isDesktopApp();
  const apiMode = getApiMode();
  const [showWebBanner, setShowWebBanner] = useState(apiMode !== "desktop");

  // Check model status on mount
  useEffect(() => {
    (async () => {
      const status = await getModelSetupStatus();
      setModelStatus(status);
      if (!status.ready && status.missingLayers.includes(1)) {
        setShowSetupPrompt(true);
      }
    })();
  }, []);

  // Update preset when quality changes
  useEffect(() => {
    const presetId = QUALITY_TO_PRESET[quality];
    const selected = ALL_PRESETS.find((p) => p.preset_id === presetId);
    if (selected) {
      setPreset({ ...selected });
    }
  }, [quality]);

  // Persist user settings to localStorage whenever they change
  useEffect(() => {
    saveSettings({
      qualityMode: quality,
      mode,
      uiLang,
      globalWhitelist,
      globalBlacklist,
      entitiesEnabled: entities,
      minimumConfidence,
      uncertaintyPolicy,
      pseudonymStyle,
      languageMode,
      selectedLanguage: language,
    });
  }, [quality, mode, uiLang, globalWhitelist, globalBlacklist, entities, minimumConfidence, uncertaintyPolicy, pseudonymStyle, languageMode, language]);

  const getCurrentPreset = useCallback((): Preset => {
    const langWhitelists: Record<string, string[]> = {};
    for (const [lang, text] of Object.entries(languageWhitelists)) {
      const words = text.split("\n").map(s => s.trim()).filter(s => s);
      if (words.length > 0) langWhitelists[lang] = words;
    }

    const langBlacklists: Record<string, string[]> = {};
    for (const [lang, text] of Object.entries(languageBlacklists)) {
      const words = text.split("\n").map(s => s.trim()).filter(s => s);
      if (words.length > 0) langBlacklists[lang] = words;
    }

    // For file mode: use the user's chosen default document language (unless "auto")
    const effectiveLang = mode === "file" && fileLanguage !== "auto" ? fileLanguage : language;

    return {
      ...preset,
      minimum_confidence: minimumConfidence,
      uncertainty_policy: uncertaintyPolicy,
      pseudonym_style: pseudonymStyle,
      language_mode: effectiveLang === "auto" ? "auto" : "fixed",
      language: effectiveLang === "auto" ? undefined : effectiveLang,
      entities_enabled: entities,
      whitelist: globalWhitelist.split("\n").filter((s) => s.trim()),
      blacklist: globalBlacklist.split("\n").filter((s) => s.trim()),
      language_whitelists: langWhitelists,
      language_blacklists: langBlacklists,
    };
  }, [preset, language, mode, fileLanguage, entities, globalWhitelist, globalBlacklist, languageWhitelists, languageBlacklists, minimumConfidence, uncertaintyPolicy, pseudonymStyle]);

  const handleAnalyze = useCallback(async () => {
    if (mode === "text" && !text.trim()) return;
    if (mode === "file" && !selectedFile) return;

    setIsProcessing(true);
    setResult("");
    setSummary({});
    setFindings([]);
    setStatusMessage("");
    // Default to highlight view for text mode so users immediately see what was detected
    setResultView(mode === "text" ? "highlight" : "anonymized");

    try {
      if (mode === "text") {
        const resp: AnalyzeTextResponse = await analyzeText(text, getCurrentPreset());
        setResult(resp.redacted_text);
        setSummary(resp.summary);
        setFindings(resp.findings || []);
        const count = resp.findings_count;
        setStatusMessage(count > 0 ? `${t(uiLang, 'status_found_pre')} ${count} ${count !== 1 ? t(uiLang, 'status_found_items') : t(uiLang, 'status_found_item')}` : t(uiLang, 'status_none'));
      } else {
        const resp: AnalyzeFileResponse = await analyzeFile(selectedFile!, getCurrentPreset());
        setSummary(resp.summary);
        setResult(`${t(uiLang, 'status_file_saved')}\n${resp.output_path}`);
        setStatusMessage(`${t(uiLang, 'status_found_pre')} ${resp.findings_count} ${t(uiLang, 'status_found_items')}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setStatusMessage(`Error: ${msg}`);
      console.error("Analysis failed:", e);
    } finally {
      setIsProcessing(false);
    }
  }, [mode, text, selectedFile, getCurrentPreset, uiLang]);

  const handleSelectFile = useCallback(async () => {
    if (!isDesktop) return;
    try {
      const path = await selectFile();
      if (path) setSelectedFile(path);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setStatusMessage(`${t(uiLang, "err_select_file")} ${msg}`);
    }
  }, [isDesktop, uiLang]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch {
      setStatusMessage(t(uiLang, "err_copy"));
    }
  }, [result, uiLang]);

  const handlePaste = useCallback(async () => {
    try {
      const clipText = await navigator.clipboard.readText();
      setText(clipText);
    } catch {
      setStatusMessage(t(uiLang, "err_paste"));
    }
  }, [uiLang]);

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
    const file = e.dataTransfer.files[0];
    if (!file) return;
    // Tauri provides a real filesystem path on the File object; web only has the name.
    const filePath = (file as { path?: string }).path ?? file.name;
    setSelectedFile(filePath);
    setMode("file");
    setStatusMessage(`${t(uiLang, "status_file_selected")} ${file.name}`);
  }, [uiLang]);

  // Check if current quality mode has models ready
  const isQualityAvailable = (q: QualityMode): boolean => {
    if (!modelStatus) return q === "fast"; // Default fast always works
    const layer = q === "fast" ? 1 : q === "accurate" ? 2 : 3;
    return !modelStatus.missingLayers.includes(layer);
  };

  return (
    <div style={styles.app} className="animated-bg">
      {/* Navigation */}
      <nav style={styles.nav} className="glass">
        <div style={styles.navLeft}>
          <div style={styles.logo}>
            <img src="/logo.png" alt="Redactly Legal" width="32" height="32" style={{ objectFit: "contain" }} />
            <span style={styles.logoText}>Redactly Legal</span>
          </div>
        </div>
        <div style={styles.navCenter} className="app-nav-center">
          <button
            style={styles.navButton(view === "main")}
            onClick={() => setView("main")}
          >
            {t(uiLang, "nav_anonymize")}
          </button>
          <button
            style={styles.navButton(view === "models")}
            onClick={() => setView("models")}
          >
            {t(uiLang, "nav_setup")}
            {modelStatus && !modelStatus.ready && (
              <span style={styles.navBadge}>!</span>
            )}
          </button>
          <button
            style={styles.navButton(view === "settings")}
            onClick={() => setView("settings")}
          >
            {t(uiLang, "nav_settings")}
          </button>
          <button
            style={styles.navButton(view === "info")}
            onClick={() => setView("info")}
          >
            {t(uiLang, "nav_info")}
          </button>
        </div>
        <div style={styles.navRight}>
          {/* UI language picker */}
          <select
            style={styles.uiLangPicker}
            value={uiLang}
            onChange={(e) => {
              const lang = e.target.value as LangCode;
              setUiLang(lang);
              saveUILanguage(lang);
            }}
            title={t(uiLang, "app_lang_label")}
          >
            {UI_LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.code.toUpperCase()} — {l.name}</option>
            ))}
          </select>

          {apiMode === "desktop" && (
            <span style={styles.statusPill}>
              <span style={styles.statusDot} />
              {t(uiLang, "status_offline")}
            </span>
          )}
          {apiMode === "web" && (
            <span style={{ ...styles.statusPill, background: "linear-gradient(135deg, rgba(0,122,255,0.12) 0%, rgba(0,122,255,0.06) 100%)", color: "#007aff" }}>
              <span style={{ ...styles.statusDot, background: "#007aff" }} />
              {t(uiLang, "status_browser")}
            </span>
          )}
          {apiMode === "preview" && (
            <span style={{ ...styles.statusPill, background: "linear-gradient(135deg, rgba(255,149,0,0.12) 0%, rgba(255,149,0,0.06) 100%)", color: "#ff9500" }}>
              <span style={{ ...styles.statusDot, background: "#ff9500" }} />
              {t(uiLang, "status_demo")}
            </span>
          )}
        </div>
      </nav>

      {/* Web / Preview Mode Banner */}
      {showWebBanner && (
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "11px 24px",
          background: apiMode === "web"
            ? "linear-gradient(135deg, rgba(0,122,255,0.07) 0%, rgba(0,122,255,0.03) 100%)"
            : "linear-gradient(135deg, rgba(255,149,0,0.09) 0%, rgba(255,149,0,0.04) 100%)",
          borderBottom: `1px solid ${apiMode === "web" ? "rgba(0,122,255,0.12)" : "rgba(255,149,0,0.18)"}`,
          fontSize: 13.5,
          color: apiMode === "web" ? "#0062cc" : "#b36200",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {apiMode === "web" ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                {t(uiLang, "banner_web")}
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
                {t(uiLang, "banner_demo")} <strong>{t(uiLang, "banner_download")}</strong>
              </>
            )}
          </div>
          <button
            onClick={() => setShowWebBanner(false)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.5, fontSize: 18, lineHeight: 1, padding: "0 4px", flexShrink: 0 }}
            title="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

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
              <h3 style={styles.setupPromptTitle}>{t(uiLang, "setup_title")}</h3>
              <p style={styles.setupPromptDesc}>{t(uiLang, "setup_desc")}</p>
            </div>
            <div style={styles.setupPromptActions}>
              <button
                style={styles.setupButton}
                onClick={() => { setView("models"); setShowSetupPrompt(false); }}
              >
                {t(uiLang, "setup_now")}
              </button>
              <button
                style={styles.setupButtonSecondary}
                onClick={() => setShowSetupPrompt(false)}
              >
                {t(uiLang, "setup_later")}
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
              {t(uiLang, "mode_text")}
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
              {t(uiLang, "mode_file")}
              {!isDesktop && <span style={styles.desktopBadge}>{t(uiLang, "mode_desktop_only")}</span>}
            </button>
          </div>

          {/* Quality Selector */}
          <div style={styles.qualitySelector}>
            <span style={styles.qualityLabel}>{t(uiLang, "quality_level")}</span>
            <div style={styles.qualityOptions} className="app-quality-options">
              {(["fast", "accurate", "thorough"] as QualityMode[]).map((q) => {
                const available = isQualityAvailable(q);
                const subText = available
                  ? q === "fast"
                    ? modelStatus && modelStatus.installedLanguages.length > 0
                      ? `${modelStatus.installedLanguages.length} language${modelStatus.installedLanguages.length !== 1 ? "s" : ""}`
                      : "Pattern matching"
                    : q === "accurate"
                    ? "AI-powered NER"
                    : "Presidio"
                  : t(uiLang, "quality_setup_req");
                return (
                  <button
                    key={q}
                    style={styles.qualityButton(quality === q, available)}
                    onClick={() => available && setQuality(q)}
                    disabled={!available}
                  >
                    <span style={styles.qualityName}>{t(uiLang, QUALITY_NAME_KEY[q])}</span>
                    <span style={available ? styles.qualityDesc : styles.qualitySetup}>{subText}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Main Content Area */}
          <div style={styles.workspace} className="app-workspace">
            {/* Input Panel */}
            <div style={styles.panel} className="card">
              <div style={styles.panelHeader}>
                <span style={styles.panelTitle}>
                  {mode === "text" ? t(uiLang, "panel_paste_text") : t(uiLang, "panel_select_file")}
                </span>
                {mode === "text" && (
                  <button
                    style={styles.pasteButton}
                    onClick={handlePaste}
                  >
                    {t(uiLang, "paste_clipboard")}
                  </button>
                )}
              </div>

              {mode === "text" ? (
                <textarea
                  style={styles.textarea}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={t(uiLang, "textarea_placeholder")}
                  maxLength={200000}
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
                      <span style={styles.changeFile}>{t(uiLang, "drop_change")}</span>
                    </div>
                  ) : (
                    <div style={styles.dropContent}>
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" strokeWidth="1.5">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      <span style={styles.dropText}>{t(uiLang, "drop_click")}</span>
                      <span style={styles.dropHint}>{t(uiLang, "drop_hint")}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Advanced Toggle */}
              <button
                style={styles.advancedToggle}
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <span>{t(uiLang, "advanced_options")}</span>
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
                    <label style={styles.advancedLabel}>{t(uiLang, "lang_label")}</label>
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
            <div style={styles.panel} className="card">
              <div style={styles.panelHeader}>
                <span style={styles.panelTitle}>{t(uiLang, "panel_result")}</span>
                {result && mode === "text" && findings.length > 0 && (
                  <div style={styles.viewToggle}>
                    <button
                      style={styles.viewToggleButton(resultView === "anonymized")}
                      onClick={() => setResultView("anonymized")}
                    >
                      {t(uiLang, "view_anonymized")}
                    </button>
                    <button
                      style={styles.viewToggleButton(resultView === "highlight")}
                      onClick={() => setResultView("highlight")}
                    >
                      {t(uiLang, "view_highlight")}
                    </button>
                  </div>
                )}
                {result && (
                  <div style={styles.headerButtons}>
                    <button
                      style={styles.copyButton(copySuccess)}
                      onClick={handleCopy}
                    >
                      {copySuccess ? t(uiLang, "btn_copied") : t(uiLang, "btn_copy")}
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
                        {t(uiLang, "btn_export")}
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
                            {t(uiLang, "export_txt")}
                          </button>
                          <button style={styles.exportMenuItem} onClick={handleExportDocx}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                              <polyline points="14 2 14 8 20 8" />
                              <line x1="16" y1="13" x2="8" y2="13" />
                              <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                            {t(uiLang, "export_docx")}
                          </button>
                          <button style={styles.exportMenuItem} onClick={handleExportXlsx}>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2">
                              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                              <line x1="3" y1="9" x2="21" y2="9" />
                              <line x1="3" y1="15" x2="21" y2="15" />
                              <line x1="9" y1="3" x2="9" y2="21" />
                            </svg>
                            {t(uiLang, "export_xlsx")}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Conditional view: Anonymized text or Highlight view */}
              {resultView === "highlight" && mode === "text" && findings.length > 0 ? (
                <ErrorBoundary>
                  <HighlightView originalText={text} findings={findings} uiLang={uiLang} />
                </ErrorBoundary>
              ) : (
                <textarea
                  style={{ ...styles.textarea, background: "#fafafa" }}
                  value={result}
                  readOnly
                  placeholder={t(uiLang, "output_placeholder")}
                />
              )}

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
                  {t(uiLang, "btn_processing")}
                </>
              ) : (
                <>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  {t(uiLang, "btn_protect")}
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
        <>
          {modelsStatusMessage && (
            <p style={styles.statusMessage}>{modelsStatusMessage}</p>
          )}
          <ModelManager
            isDesktop={isDesktop}
            uiLang={uiLang}
            onStatusChange={(msg) => setModelsStatusMessage(msg)}
            onSetupComplete={async () => {
              const s = await getModelSetupStatus();
              setModelStatus(s);
              setShowSetupPrompt(false);
            }}
          />
        </>
      )}

      {/* Settings View */}
      {view === "settings" && (
        <main style={styles.settingsMain}>
          <div style={styles.settingsHeader}>
            <h1 style={styles.settingsTitle}>{t(uiLang, "settings_title")}</h1>
            <p style={styles.settingsSubtitle}>{t(uiLang, "settings_subtitle")}</p>
          </div>

          {/* App Language + Document Language Section */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>{t(uiLang, "sect_app_lang")}</h2>
            <p style={styles.sectionDesc}>{t(uiLang, "sect_app_lang_desc")}</p>
            <div style={styles.settingsGrid}>
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#007aff" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  </svg>
                  {t(uiLang, "app_lang_label")}
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "sect_app_lang_desc")}</p>
                <select
                  style={{ ...styles.langDropdown, width: "100%" }}
                  value={uiLang}
                  onChange={(e) => {
                    const lang = e.target.value as LangCode;
                    setUiLang(lang);
                    saveUILanguage(lang);
                  }}
                >
                  {UI_LANGUAGES.map(l => (
                    <option key={l.code} value={l.code}>[{l.code.toUpperCase()}] {l.name}</option>
                  ))}
                </select>
              </div>

              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                  {t(uiLang, "doc_lang_label")}
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "sect_doc_lang_desc")}</p>
                <select
                  style={{ ...styles.langDropdown, width: "100%" }}
                  value={fileLanguage}
                  onChange={(e) => setFileLanguage(e.target.value)}
                >
                  <option value="auto">{t(uiLang, "doc_lang_auto")}</option>
                  {SUPPORTED_LANGUAGES.filter(l => l.code !== "auto").map((lang) => (
                    <option key={lang.code} value={lang.code}>{lang.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Global Lists Section */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>{t(uiLang, "sect_global_lists")}</h2>
            <p style={styles.sectionDesc}>{t(uiLang, "sect_global_desc")}</p>

            <div style={styles.settingsGrid}>
              {/* Global Whitelist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  {t(uiLang, "skip_global_title")}
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "skip_global_desc")}</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={globalWhitelist}
                  onChange={(e) => setGlobalWhitelist(e.target.value)}
                  placeholder={t(uiLang, "skip_global_placeholder")}
                />
              </div>

              {/* Global Blacklist */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                  </svg>
                  {t(uiLang, "hide_global_title")}
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "hide_global_desc")}</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={globalBlacklist}
                  onChange={(e) => setGlobalBlacklist(e.target.value)}
                  placeholder={t(uiLang, "hide_global_placeholder")}
                />
              </div>
            </div>
          </div>

          {/* Language-Specific Lists Section */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>{t(uiLang, "sect_lang_lists")}</h2>
            <p style={styles.sectionDesc}>{t(uiLang, "sect_lang_desc")}</p>

            {/* Language Selector */}
            <div style={styles.langSelectorRow}>
              <label style={styles.langSelectorLabel}>{t(uiLang, "lang_select_label")}</label>
              <select
                style={styles.langDropdown}
                value={settingsLang}
                onChange={(e) => setSettingsLang(e.target.value)}
              >
                {SUPPORTED_LANGUAGES.filter(l => l.code !== "auto").map((lang) => {
                  const count = languageWhitelists[lang.code]?.split("\n").filter(s => s.trim()).length || 0;
                  return (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}{count > 0 ? ` (${count})` : ""}
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
                  {t(uiLang, "skip_global_title").replace("(Global)", "")}
                  ({SUPPORTED_LANGUAGES.find(l => l.code === settingsLang)?.name || settingsLang})
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "skip_lang_desc")}</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={languageWhitelists[settingsLang] || ""}
                  onChange={(e) => setLanguageWhitelists(prev => ({
                    ...prev,
                    [settingsLang]: e.target.value
                  }))}
                  placeholder={t(uiLang, "skip_lang_placeholder")}
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
                  {t(uiLang, "hide_global_title").replace("(Global)", "")}
                  ({SUPPORTED_LANGUAGES.find(l => l.code === settingsLang)?.name || settingsLang})
                </h3>
                <p style={styles.cardDesc}>{t(uiLang, "hide_lang_desc")}</p>
                <textarea
                  style={styles.settingsTextarea}
                  value={(languageBlacklists[settingsLang] || "")}
                  onChange={(e) => setLanguageBlacklists(prev => ({
                    ...prev,
                    [settingsLang]: e.target.value
                  }))}
                  placeholder={t(uiLang, "hide_lang_placeholder")}
                />
              </div>
            </div>
          </div>

          {/* Detection Sensitivity */}
          <div style={styles.settingsSection}>
            <h2 style={styles.sectionTitle}>Detection Sensitivity</h2>
            <p style={styles.sectionDesc}>
              Control how aggressively PII is flagged. Higher confidence thresholds reduce false positives but may miss uncertain cases.
            </p>
            <div style={styles.settingsGrid}>

              {/* Confidence Threshold */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                  </svg>
                  Confidence Threshold
                </h3>
                <p style={styles.cardDesc}>
                  Minimum confidence score (%) for a detection to be included.
                  Default: 75. Raise to reduce false positives; lower to catch more edge cases.
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
                  <input
                    type="range"
                    min={50}
                    max={99}
                    step={5}
                    value={minimumConfidence}
                    onChange={(e) => setMinimumConfidence(Number(e.target.value))}
                    style={{ flex: 1, accentColor: "#10b981" }}
                  />
                  <span style={{
                    minWidth: 42,
                    textAlign: "right",
                    fontWeight: 700,
                    fontSize: 18,
                    color: "#10b981",
                    fontVariantNumeric: "tabular-nums",
                  }}>
                    {minimumConfidence}%
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#9ca3af", marginTop: 2 }}>
                  <span>50 — permissive</span>
                  <span>99 — strict</span>
                </div>
              </div>

              {/* Uncertainty Policy */}
              <div style={styles.settingsCard}>
                <h3 style={styles.cardTitle}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  Uncertain Detections
                </h3>
                <p style={styles.cardDesc}>
                  What to do with detections that fall below the confidence threshold but above 50%.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
                  {(["mask", "redact", "leave_intact", "flag_only"] as const).map((policy) => {
                    const labels: Record<string, string> = {
                      mask: "Mask — partially obscure (jo**@***.com)",
                      redact: "Redact — replace with [ENTITY] tag",
                      leave_intact: "Leave intact — keep original text",
                      flag_only: "Flag only — highlight but don't redact",
                    };
                    const selected = uncertaintyPolicy === policy;
                    return (
                      <button
                        key={policy}
                        onClick={() => setUncertaintyPolicy(policy)}
                        style={{
                          textAlign: "left",
                          padding: "8px 12px",
                          borderRadius: 8,
                          border: selected ? "2px solid #f59e0b" : "1.5px solid #e5e7eb",
                          background: selected ? "#fffbeb" : "#fff",
                          color: selected ? "#92400e" : "#374151",
                          fontWeight: selected ? 600 : 400,
                          fontSize: 13,
                          cursor: "pointer",
                          transition: "all 0.15s",
                        }}
                      >
                        {labels[policy]}
                      </button>
                    );
                  })}
                </div>
              </div>

            </div>
          </div>

          {/* Reset to defaults */}
          <div style={styles.settingsSection}>
            <div style={styles.resetRow}>
              <div>
                <h2 style={styles.sectionTitle}>Reset Settings</h2>
                <p style={styles.sectionDesc}>
                  Clear all saved settings and restore factory defaults. This cannot be undone.
                </p>
              </div>
              <button
                style={styles.resetButton}
                onClick={() => {
                  try { localStorage.removeItem(LS_KEY); } catch { /* ignore */ }
                  const defaults = { ...DEFAULT_SETTINGS, entitiesEnabled: { ...DEFAULT_ENTITIES } };
                  const detectedLang = detectUILanguage();
                  setQuality(defaults.qualityMode);
                  setMode(defaults.mode);
                  setUiLang(detectedLang);
                  saveUILanguage(detectedLang);
                  setGlobalWhitelist(defaults.globalWhitelist);
                  setGlobalBlacklist(defaults.globalBlacklist);
                  setEntities({ ...DEFAULT_ENTITIES });
                  setMinimumConfidence(defaults.minimumConfidence);
                  setUncertaintyPolicy(defaults.uncertaintyPolicy);
                  setPseudonymStyle(defaults.pseudonymStyle);
                  setLanguageMode(defaults.languageMode);
                  setLanguage(defaults.selectedLanguage);
                }}
              >
                Reset to defaults
              </button>
            </div>
          </div>
        </main>
      )}

      {/* Info View */}
      {view === "info" && (
        <main style={styles.settingsMain}>
          <div style={styles.settingsHeader}>
            <h1 style={styles.settingsTitle}>{t(uiLang, "info_title")}</h1>
            <p style={styles.settingsSubtitle}>{t(uiLang, "info_subtitle")}</p>
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

          {/* Data Processing Notice */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                <h2 style={styles.infoCardTitle}>{t(uiLang, "compliance_data_title")}</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>{t(uiLang, "compliance_data_intro")}</p>

                <p style={{ fontWeight: 600, fontSize: 13, color: "#374151", margin: "12px 0 6px" }}>
                  {t(uiLang, "compliance_logged_label")}
                </p>
                <ul style={styles.infoBulletList}>
                  <li>Timestamp, run ID, protection layer, preset name</li>
                  <li>Entity type counts — e.g. <code style={{ background: "#f3f4f6", padding: "1px 4px", borderRadius: 3 }}>{`{"PERSON": 3, "EMAIL": 1}`}</code> (never the actual values)</li>
                  <li>SHA-256 hash of input (not the text itself)</li>
                  <li>Processing duration, confidence threshold, uncertainty policy</li>
                  <li><strong>findings.csv</strong> — detected original values + positions. Treat as sensitive; do not share externally.</li>
                  <li>Anonymised output file, preset snapshot, model inventory</li>
                </ul>

                <p style={{ fontWeight: 600, fontSize: 13, color: "#374151", margin: "12px 0 6px" }}>
                  {t(uiLang, "compliance_not_logged_label")}
                </p>
                <ul style={styles.infoBulletList}>
                  <li>Input text or document content</li>
                  <li>File paths or file names</li>
                  <li>Any personal data in the source document</li>
                  <li>Network calls — none are made</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Detection Layers — How They Work */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardContent}>
                {/* How the detection layers work */}
                <div style={{ marginBottom: 28 }}>
                  <h3 style={{ margin: "0 0 10px", fontSize: 15, fontWeight: 600, color: "#1d1d1f" }}>
                    Detection Layers — How They Work
                  </h3>
                  <p style={{ margin: "0 0 14px", fontSize: 13, color: "#6e6e73", lineHeight: 1.6 }}>
                    Redactly Legal uses three independent detection layers. Choose the one that matches your accuracy and performance needs.
                  </p>
                  <div style={{ display: "flex", flexDirection: "column" as const, gap: 12 }}>
                    {([
                      {
                        label: "Fast — Layer 1",
                        badge: "spaCy NER",
                        color: "#0ea5e9",
                        bg: "#f0f9ff",
                        border: "#bae6fd",
                        what: "Statistical named-entity recognition using spaCy language models.",
                        catches: "Person names, organisations, locations, dates — entities the language model has learned to recognise.",
                        misses: "Structured numbers (SSNs, IBANs, credit cards) unless they happen to be named entities.",
                        speed: "Fastest. No warm-up after model load.",
                      },
                      {
                        label: "Accurate — Layer 2",
                        badge: "BERT / RoBERTa",
                        color: "#8b5cf6",
                        bg: "#faf5ff",
                        border: "#ddd6fe",
                        what: "Transformer-based NER (BERT, RoBERTa). Reads full sentence context to understand meaning, not just patterns.",
                        catches: "Everything Layer 1 catches, with higher recall on ambiguous names, partial names, and cross-sentence references. Best overall accuracy.",
                        misses: "Still primarily entity-focused — structural PII (IBANs, passport numbers) benefits from combining with Layer 3.",
                        speed: "Slower on first run (model load ~5–10 s). Subsequent runs use cached model.",
                      },
                      {
                        label: "Thorough — Layer 3",
                        badge: "Microsoft Presidio",
                        color: "#10b981",
                        bg: "#f0fdf4",
                        border: "#bbf7d0",
                        what: "Microsoft Presidio runs spaCy NER plus a comprehensive library of regex pattern recognisers.",
                        catches: "Everything Layer 1 catches, plus: SSNs, IBANs, credit card numbers, passport numbers, VAT IDs, phone numbers, email addresses — even if the model has never seen that specific format before.",
                        misses: "Less contextual than transformer models — may have slightly lower recall on unusual name formats.",
                        speed: "Moderate. Presidio initialises once per session.",
                      },
                    ] as const).map(layer => (
                      <div key={layer.label} style={{ padding: "14px 16px", borderRadius: 10, background: layer.bg, border: `1px solid ${layer.border}` }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                          <span style={{ fontSize: 14, fontWeight: 600, color: "#1d1d1f" }}>{layer.label}</span>
                          <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 4, background: layer.color, color: "#fff" }}>{layer.badge}</span>
                        </div>
                        <div style={{ fontSize: 13, color: "#374151", lineHeight: 1.6 }}>
                          <div style={{ marginBottom: 4 }}><strong>How:</strong> {layer.what}</div>
                          <div style={{ marginBottom: 4 }}><span style={{ color: "#16a34a", fontWeight: 500 }}>✓ Catches:</span> {layer.catches}</div>
                          <div style={{ marginBottom: 4 }}><span style={{ color: "#6b7280", fontWeight: 500 }}>△ Note:</span> {layer.misses}</div>
                          <div><span style={{ color: "#6b7280", fontWeight: 500 }}>Speed:</span> {layer.speed}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* GDPR Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <h2 style={styles.infoCardTitle}>{t(uiLang, "compliance_gdpr_title")}</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>{t(uiLang, "compliance_gdpr_intro")}</p>

                {/* GDPR article table */}
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 8 }}>
                  <thead>
                    <tr style={{ background: "#f9fafb" }}>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>Article</th>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>Requirement</th>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["Art. 5", "Lawfulness, transparency, data minimisation, accountability", "✓", "#10b981", t(uiLang, "compliance_covered")],
                      ["Art. 17", "Right to erasure — originals never modified; run artifacts deletable", "✓", "#10b981", t(uiLang, "compliance_covered")],
                      ["Art. 25", "Privacy by design & default — Presidio is the recommended default", "✓", "#10b981", t(uiLang, "compliance_covered")],
                      ["Art. 32", "Security of processing — offline-only, no network, originals untouched", "✓", "#10b981", t(uiLang, "compliance_covered")],
                      ["Art. 35", "DPIA for high-risk processing of sensitive categories", "⚠", "#f59e0b", t(uiLang, "compliance_org_req")],
                    ].map(([art, req, icon, color, label]) => (
                      <tr key={art} style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <td style={{ padding: "7px 10px", fontWeight: 600, whiteSpace: "nowrap", color: "#374151" }}>{art}</td>
                        <td style={{ padding: "7px 10px", color: "#6b7280" }}>{req}</td>
                        <td style={{ padding: "7px 10px", whiteSpace: "nowrap" }}>
                          <span style={{ color, fontWeight: 600 }}>{icon}</span>
                          <span style={{ marginLeft: 6, color: "#374151" }}>{label}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div style={styles.infoWarning}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <p>{t(uiLang, "compliance_disclaimer")}</p>
                </div>
              </div>
            </div>
          </div>

          {/* EU AI Act Section */}
          <div style={styles.infoSection}>
            <div style={styles.infoCard}>
              <div style={styles.infoCardHeader}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <h2 style={styles.infoCardTitle}>{t(uiLang, "compliance_ai_title")}</h2>
              </div>
              <div style={styles.infoCardContent}>
                <p style={styles.infoParagraph}>{t(uiLang, "compliance_ai_intro")}</p>

                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, marginTop: 8 }}>
                  <thead>
                    <tr style={{ background: "#f9fafb" }}>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>Layer</th>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>Technology</th>
                      <th style={{ textAlign: "left", padding: "6px 10px", borderBottom: "1px solid #e5e7eb", color: "#6b7280", fontWeight: 600 }}>AI Act Risk Tier</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["1 — Fast", "spaCy NER + regex rules", "Minimal risk", "#10b981"],
                      ["3 — Thorough", "Microsoft Presidio (recommended)", "Minimal risk", "#10b981"],
                      ["2 — Accurate", "BERT transformer (optional download)", "Limited risk — AI model", "#f59e0b"],
                    ].map(([layer, tech, tier, color]) => (
                      <tr key={layer} style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <td style={{ padding: "7px 10px", fontWeight: 600, color: "#374151", whiteSpace: "nowrap" }}>{layer}</td>
                        <td style={{ padding: "7px 10px", color: "#6b7280" }}>{tech}</td>
                        <td style={{ padding: "7px 10px", color, fontWeight: 600 }}>{tier}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div style={{ ...styles.infoList, marginTop: 14 }}>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Human oversight — users review all findings before applying</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>No autonomous decisions — the tool supports, not replaces, human judgement</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Full auditability — per-run <code style={{ background: "#f3f4f6", padding: "1px 4px", borderRadius: 3 }}>model_inventory.json</code> records exact model versions</span>
                  </div>
                  <div style={styles.infoListItem}>
                    <span style={styles.infoCheck}>✓</span>
                    <span>Transparency — Layer 2 AI model use is disclosed here (Art. 13 obligation)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Version Info */}
          <div style={styles.versionInfo}>
            <p>Redactly Legal v{APP_VERSION}</p>
            <p>© {new Date().getFullYear()} Redactly Legal Contributors</p>
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
    padding: "14px 28px",
    borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
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
    gap: 12,
    color: "#1d1d1f",
  } as React.CSSProperties,

  logoText: {
    fontSize: 18,
    fontWeight: 700,
    letterSpacing: "-0.025em",
    background: "linear-gradient(135deg, #1d1d1f 0%, #4a4a4f 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  } as React.CSSProperties,

  navCenter: {
    display: "flex",
    gap: 4,
    background: "rgba(0, 0, 0, 0.04)",
    borderRadius: 12,
    padding: 5,
  } as React.CSSProperties,

  navButton: (active: boolean) => ({
    padding: "9px 22px",
    fontSize: 14,
    fontWeight: 500,
    border: "none",
    borderRadius: 10,
    background: active ? "#fff" : "transparent",
    color: active ? "#1d1d1f" : "#86868b",
    cursor: "pointer",
    transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: active ? "0 2px 8px rgba(0,0,0,0.06)" : "none",
    position: "relative" as const,
    transform: active ? "scale(1.02)" : "scale(1)",
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
    alignItems: "center",
    gap: 10,
  } as React.CSSProperties,

  uiLangPicker: {
    padding: "5px 8px",
    fontSize: 13,
    fontWeight: 500,
    border: "1px solid rgba(0,0,0,0.08)",
    borderRadius: 8,
    background: "rgba(0,0,0,0.03)",
    color: "#3d3d3f",
    outline: "none",
    cursor: "pointer",
    maxWidth: 160,
  } as React.CSSProperties,

  browserButton: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "6px 13px",
    fontSize: 12,
    fontWeight: 500,
    color: "#007aff",
    background: "rgba(0,122,255,0.08)",
    border: "1px solid rgba(0,122,255,0.15)",
    borderRadius: 20,
    cursor: "pointer",
    letterSpacing: "0.01em",
    whiteSpace: "nowrap",
  } as React.CSSProperties,

  statusPill: {
    padding: "7px 14px",
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: "0.01em",
    background: "linear-gradient(135deg, rgba(52, 199, 89, 0.15) 0%, rgba(52, 199, 89, 0.08) 100%)",
    color: "#34c759",
    borderRadius: 20,
    display: "flex",
    alignItems: "center",
    gap: 7,
  } as React.CSSProperties,

  statusDot: {
    width: 7,
    height: 7,
    background: "#34c759",
    borderRadius: "50%",
    boxShadow: "0 0 8px rgba(52, 199, 89, 0.5)",
    animation: "pulse 2s ease-in-out infinite",
  } as React.CSSProperties,

  // Setup Prompt
  setupPrompt: {
    padding: "18px 28px",
    background: "linear-gradient(135deg, rgba(0, 122, 255, 0.08) 0%, rgba(88, 86, 214, 0.06) 100%)",
    borderBottom: "1px solid rgba(0, 122, 255, 0.1)",
    animation: "fadeIn 0.3s ease",
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
    padding: "12px 24px",
    fontSize: 14,
    fontWeight: 600,
    background: "linear-gradient(135deg, #007aff 0%, #5856d6 100%)",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    cursor: "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 4px 14px rgba(0, 122, 255, 0.3)",
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
    gap: 10,
    padding: "14px 28px",
    fontSize: 15,
    fontWeight: 500,
    border: "none",
    borderRadius: 14,
    background: active ? "#fff" : "transparent",
    color: active ? "#1d1d1f" : "#86868b",
    cursor: "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: active ? "0 4px 12px rgba(0,0,0,0.06)" : "none",
    position: "relative" as const,
    transform: active ? "scale(1.02)" : "scale(1)",
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
    padding: "18px 36px",
    fontSize: 15,
    fontWeight: 500,
    border: active ? "2px solid #007aff" : "2px solid rgba(0,0,0,0.06)",
    borderRadius: 14,
    background: active
      ? "linear-gradient(180deg, rgba(0, 122, 255, 0.08) 0%, rgba(0, 122, 255, 0.04) 100%)"
      : "#fff",
    color: available ? (active ? "#007aff" : "#1d1d1f") : "#aeaeb2",
    cursor: available ? "pointer" : "default",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    opacity: available ? 1 : 0.5,
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 6,
    boxShadow: active
      ? "0 4px 16px rgba(0, 122, 255, 0.15)"
      : "0 2px 6px rgba(0,0,0,0.04)",
    transform: active ? "scale(1.02)" : "scale(1)",
  }) as React.CSSProperties,

  qualityName: {
    fontWeight: 600,
  } as React.CSSProperties,

  qualitySetup: {
    fontSize: 11,
    color: "#9ca3af",
  } as React.CSSProperties,

  qualityDesc: {
    fontSize: 11,
    color: "#6e6e73",
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
    borderRadius: 18,
    padding: 28,
    boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
    transition: "box-shadow 0.25s ease, transform 0.25s ease",
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
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 500,
    background: "rgba(0, 0, 0, 0.04)",
    color: "#86868b",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
  } as React.CSSProperties,

  copyButton: (copied: boolean) => ({
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 600,
    background: copied
      ? "linear-gradient(135deg, rgba(52, 199, 89, 0.15) 0%, rgba(52, 199, 89, 0.08) 100%)"
      : "rgba(0,0,0,0.04)",
    color: copied ? "#34c759" : "#6e6e73",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    transform: copied ? "scale(1.02)" : "scale(1)",
  }) as React.CSSProperties,

  viewToggle: {
    display: "flex",
    gap: 2,
    background: "rgba(0, 0, 0, 0.04)",
    borderRadius: 8,
    padding: 3,
  } as React.CSSProperties,

  viewToggleButton: (active: boolean) => ({
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 600,
    border: "none",
    borderRadius: 6,
    background: active ? "#fff" : "transparent",
    color: active ? "#1d1d1f" : "#86868b",
    cursor: "pointer",
    transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: active ? "0 1px 4px rgba(0,0,0,0.08)" : "none",
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
    gap: 7,
    padding: "8px 14px",
    fontSize: 13,
    fontWeight: 600,
    background: "linear-gradient(135deg, #007aff 0%, #5856d6 100%)",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 2px 8px rgba(0, 122, 255, 0.25)",
  } as React.CSSProperties,

  exportMenu: {
    position: "absolute" as const,
    top: "calc(100% + 10px)",
    right: 0,
    background: "#fff",
    borderRadius: 14,
    boxShadow: "0 8px 40px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.06)",
    border: "1px solid rgba(0,0,0,0.06)",
    overflow: "hidden",
    zIndex: 50,
    minWidth: 220,
    animation: "fadeInScale 0.15s ease",
  } as React.CSSProperties,

  exportMenuItem: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    width: "100%",
    padding: "14px 18px",
    fontSize: 14,
    fontWeight: 500,
    background: "transparent",
    color: "#1d1d1f",
    border: "none",
    borderBottom: "1px solid rgba(0,0,0,0.04)",
    cursor: "pointer",
    transition: "background 0.15s ease",
    textAlign: "left" as const,
  } as React.CSSProperties,

  textarea: {
    width: "100%",
    height: 420,
    padding: 18,
    fontSize: 15,
    lineHeight: 1.65,
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif',
    border: "1px solid rgba(0,0,0,0.08)",
    borderRadius: 14,
    resize: "none" as const,
    outline: "none",
    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
    boxSizing: "border-box" as const,
    background: "#fff",
  } as React.CSSProperties,

  // Drop Zone
  dropZone: (dragging: boolean, disabled: boolean) => ({
    height: 420,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    border: `2px dashed ${dragging ? "#007aff" : "rgba(0,0,0,0.1)"}`,
    borderRadius: 16,
    background: dragging
      ? "linear-gradient(135deg, rgba(0, 122, 255, 0.08) 0%, rgba(0, 122, 255, 0.02) 100%)"
      : disabled
      ? "#fafafa"
      : "#fff",
    cursor: disabled ? "default" : "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    opacity: disabled ? 0.5 : 1,
    transform: dragging ? "scale(1.01)" : "scale(1)",
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
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 600,
    background: "linear-gradient(135deg, rgba(52, 199, 89, 0.12) 0%, rgba(52, 199, 89, 0.06) 100%)",
    color: "#34c759",
    borderRadius: 8,
    transition: "transform 0.2s ease",
  } as React.CSSProperties,

  // Action Area
  actionArea: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    gap: 16,
    paddingTop: 8,
  } as React.CSSProperties,

  actionButton: (disabled: boolean) => ({
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: "18px 52px",
    fontSize: 17,
    fontWeight: 600,
    background: disabled
      ? "#e5e5ea"
      : "linear-gradient(135deg, #007aff 0%, #5856d6 100%)",
    backgroundSize: "200% 200%",
    color: disabled ? "#aeaeb2" : "#fff",
    border: "none",
    borderRadius: 16,
    cursor: disabled ? "default" : "pointer",
    transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: disabled ? "none" : "0 8px 32px rgba(0, 122, 255, 0.35)",
    position: "relative" as const,
    overflow: "hidden",
  }) as React.CSSProperties,

  spinner: {
    width: 18,
    height: 18,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTopColor: "#fff",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  } as React.CSSProperties,

  statusMessage: {
    fontSize: 14,
    fontWeight: 500,
    color: "#86868b",
    margin: 0,
    animation: "fadeIn 0.3s ease",
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
    fontSize: 32,
    fontWeight: 700,
    letterSpacing: "-0.025em",
    background: "linear-gradient(135deg, #1d1d1f 0%, #3d3d3f 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
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
    borderRadius: 18,
    padding: 26,
    boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
    transition: "box-shadow 0.25s ease, transform 0.25s ease",
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
    borderRadius: 20,
    padding: 32,
    boxShadow: "0 2px 12px rgba(0,0,0,0.04)",
    transition: "box-shadow 0.25s ease",
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
    color: "#34c759",
    fontWeight: 700,
    fontSize: 16,
    flexShrink: 0,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 20,
    height: 20,
    background: "rgba(52, 199, 89, 0.1)",
    borderRadius: "50%",
  } as React.CSSProperties,

  infoCross: {
    color: "#ff3b30",
    fontWeight: 700,
    fontSize: 16,
    flexShrink: 0,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: 20,
    height: 20,
    background: "rgba(255, 59, 48, 0.1)",
    borderRadius: "50%",
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
    background: "linear-gradient(135deg, #f9fafb 0%, #f5f5f7 100%)",
    borderRadius: 14,
    padding: 20,
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
  } as React.CSSProperties,

  infoGridTitle: {
    margin: "0 0 10px",
    fontSize: 15,
    fontWeight: 600,
    color: "#1d1d1f",
    letterSpacing: "-0.01em",
  } as React.CSSProperties,

  infoGridText: {
    margin: 0,
    fontSize: 13,
    lineHeight: 1.55,
    color: "#86868b",
  } as React.CSSProperties,

  infoWarning: {
    display: "flex",
    alignItems: "flex-start",
    gap: 14,
    marginTop: 24,
    padding: 18,
    background: "linear-gradient(135deg, rgba(255, 149, 0, 0.12) 0%, rgba(255, 149, 0, 0.06) 100%)",
    borderRadius: 14,
    border: "1px solid rgba(255, 149, 0, 0.15)",
    color: "#cc7a00",
    fontSize: 13,
    lineHeight: 1.55,
  } as React.CSSProperties,

  versionInfo: {
    textAlign: "center" as const,
    padding: "48px 0 32px",
    fontSize: 13,
    color: "#aeaeb2",
    letterSpacing: "0.01em",
  } as React.CSSProperties,

  resetRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 24,
    flexWrap: "wrap" as const,
  } as React.CSSProperties,

  resetButton: {
    padding: "10px 22px",
    fontSize: 14,
    fontWeight: 600,
    border: "1.5px solid #ef4444",
    borderRadius: 10,
    background: "rgba(239, 68, 68, 0.06)",
    color: "#dc2626",
    cursor: "pointer",
    transition: "all 0.15s ease",
    letterSpacing: "0.01em",
    whiteSpace: "nowrap" as const,
    flexShrink: 0,
  } as React.CSSProperties,
};

