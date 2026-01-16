import React, { useState, useCallback } from "react";

// ============================================================================
// Types
// ============================================================================

type DownloadStatus = "not_installed" | "downloading" | "installed" | "error";

type SpacyModel = {
  id: string;
  name: string;
  flag: string;
  size: string;
  status: DownloadStatus;
  progress?: number;
};

type HuggingFaceModel = {
  id: string;
  name: string;
  description: string;
  size: string;
  languages: string[];
  recommended?: boolean;
  status: DownloadStatus;
  progress?: number;
};

type PresidioComponent = {
  id: string;
  name: string;
  description: string;
  size: string;
  status: DownloadStatus;
  progress?: number;
  required?: boolean;
};

export type ModelSetupStatus = {
  ready: boolean;
  missingLayers: number[];
  installedLanguages: string[];
};

// ============================================================================
// Hardware Requirements
// ============================================================================

const HARDWARE_REQUIREMENTS = {
  fast: {
    ram: "2 GB",
    disk: "50 MB per language",
    gpu: "Not required",
    cpu: "Any modern CPU",
    note: "Runs on any standard corporate laptop from the last 10 years. No special hardware needed.",
  },
  accurate: {
    ram: "8 GB minimum, 16 GB recommended",
    disk: "500 MB - 1.5 GB per model",
    gpu: "Optional (NVIDIA with 4+ GB VRAM speeds up 10x)",
    cpu: "4+ cores recommended",
    note: "CPU-only works fine but is slower. A dedicated GPU dramatically speeds up processing of large documents.",
  },
  thorough: {
    ram: "4 GB",
    disk: "600 MB total",
    gpu: "Not required",
    cpu: "Any modern CPU",
    note: "Similar requirements to Fast mode. Any standard corporate laptop will work.",
  },
};

// ============================================================================
// Status Check
// ============================================================================

export function getModelSetupStatus(): ModelSetupStatus {
  // TODO: Implement actual check via Tauri backend
  // This would call Python to check installed packages
  return {
    ready: false,
    missingLayers: [1, 2, 3],
    installedLanguages: [],
  };
}

// ============================================================================
// Component
// ============================================================================

type Props = {
  isDesktop: boolean;
  onStatusChange?: (message: string) => void;
  onSetupComplete?: () => void;
};

export function ModelManager({ isDesktop, onStatusChange, onSetupComplete }: Props) {
  const [activeTab, setActiveTab] = useState<"fast" | "accurate" | "thorough">("fast");
  const [showHardwareInfo, setShowHardwareInfo] = useState(false);

  // ========== FAST MODE: spaCy Models ==========
  const [spacyModels, setSpacyModels] = useState<SpacyModel[]>([
    { id: "en_core_web_sm", name: "English", flag: "🇬🇧", size: "12 MB", status: "not_installed" },
    { id: "nl_core_news_sm", name: "Dutch", flag: "🇳🇱", size: "12 MB", status: "not_installed" },
    { id: "de_core_news_sm", name: "German", flag: "🇩🇪", size: "12 MB", status: "not_installed" },
    { id: "fr_core_news_sm", name: "French", flag: "🇫🇷", size: "12 MB", status: "not_installed" },
    { id: "es_core_news_sm", name: "Spanish", flag: "🇪🇸", size: "12 MB", status: "not_installed" },
    { id: "it_core_news_sm", name: "Italian", flag: "🇮🇹", size: "12 MB", status: "not_installed" },
    { id: "pt_core_news_sm", name: "Portuguese", flag: "🇵🇹", size: "12 MB", status: "not_installed" },
    { id: "pl_core_news_sm", name: "Polish", flag: "🇵🇱", size: "12 MB", status: "not_installed" },
  ]);

  // ========== ACCURATE MODE: HuggingFace Models ==========
  const [hfModels, setHfModels] = useState<HuggingFaceModel[]>([
    // Multilingual
    {
      id: "Davlan/bert-base-multilingual-cased-ner-hrl",
      name: "Multilingual BERT NER",
      description: "Covers 10 languages: EN, NL, DE, FR, ES, IT, PT, PL, RU, ZH",
      size: "680 MB",
      languages: ["en", "nl", "de", "fr", "es", "it", "pt", "pl", "ru", "zh"],
      recommended: true,
      status: "not_installed",
    },
    {
      id: "xlm-roberta-large-finetuned-conll03-english",
      name: "XLM-RoBERTa Large",
      description: "High-accuracy multilingual model, 100+ languages",
      size: "2.2 GB",
      languages: ["multilingual"],
      status: "not_installed",
    },
    // English
    {
      id: "dslim/bert-base-NER",
      name: "BERT NER (English)",
      description: "Fast and accurate English NER",
      size: "420 MB",
      languages: ["en"],
      status: "not_installed",
    },
    {
      id: "Jean-Baptiste/roberta-large-ner-english",
      name: "RoBERTa Large (English)",
      description: "State-of-the-art English NER, highest accuracy",
      size: "1.3 GB",
      languages: ["en"],
      status: "not_installed",
    },
    // Dutch
    {
      id: "wietsedv/bert-base-dutch-cased-finetuned-conll2002-ner",
      name: "BERT NER (Dutch)",
      description: "Specialized Dutch NER, trained on CoNLL-2002",
      size: "420 MB",
      languages: ["nl"],
      status: "not_installed",
    },
    // German
    {
      id: "mschiesser/ner-bert-german",
      name: "BERT NER (German)",
      description: "German NER model trained on CoNLL-2003",
      size: "420 MB",
      languages: ["de"],
      status: "not_installed",
    },
    {
      id: "flair/ner-german-large",
      name: "Flair NER (German)",
      description: "High-accuracy German NER from Zalando Research",
      size: "1.4 GB",
      languages: ["de"],
      status: "not_installed",
    },
    // French
    {
      id: "Jean-Baptiste/camembert-ner",
      name: "CamemBERT NER (French)",
      description: "French NER based on CamemBERT",
      size: "420 MB",
      languages: ["fr"],
      status: "not_installed",
    },
    // Spanish
    {
      id: "mrm8488/bert-spanish-cased-finetuned-ner",
      name: "BETO NER (Spanish)",
      description: "Spanish BERT fine-tuned for NER",
      size: "420 MB",
      languages: ["es"],
      status: "not_installed",
    },
    // Italian + Others
    {
      id: "Babelscape/wikineural-multilingual-ner",
      name: "WikiNEuRal (9 languages)",
      description: "IT, DE, ES, FR, NL, PL, PT, RU, EN - trained on Wikipedia",
      size: "1.1 GB",
      languages: ["it", "de", "es", "fr", "nl", "pl", "pt", "ru", "en"],
      status: "not_installed",
    },
  ]);

  // ========== THOROUGH MODE: Presidio Components ==========
  const [presidioComponents, setPresidioComponents] = useState<PresidioComponent[]>([
    {
      id: "presidio-analyzer",
      name: "Presidio Analyzer",
      description: "Core PII detection engine from Microsoft",
      size: "15 MB",
      status: "not_installed",
      required: true,
    },
    {
      id: "presidio-anonymizer",
      name: "Presidio Anonymizer",
      description: "Anonymization and pseudonymization engine",
      size: "5 MB",
      status: "not_installed",
      required: true,
    },
    {
      id: "en_core_web_lg",
      name: "spaCy English (Large)",
      description: "Large English model for best Presidio accuracy",
      size: "560 MB",
      status: "not_installed",
      required: true,
    },
  ]);

  // Counts
  const spacyInstalledCount = spacyModels.filter(m => m.status === "installed").length;
  const hfInstalledCount = hfModels.filter(m => m.status === "installed").length;
  const presidioInstalledCount = presidioComponents.filter(c => c.status === "installed").length;
  const presidioRequiredCount = presidioComponents.filter(c => c.required).length;

  // Download handlers
  // NOTE: These are MOCK implementations for UI preview
  // Real implementation requires Tauri backend commands

  const handleDownloadSpacy = useCallback(async (modelId: string) => {
    if (!isDesktop) {
      onStatusChange?.("Downloads require the desktop app");
      return;
    }

    // TODO: invoke('download_spacy_model', { modelId })
    setSpacyModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "downloading", progress: 0 } : m
    ));

    for (let i = 0; i <= 100; i += 5) {
      await new Promise(resolve => setTimeout(resolve, 80));
      setSpacyModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, progress: i } : m
      ));
    }

    setSpacyModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "installed", progress: undefined } : m
    ));

    onStatusChange?.("Language model installed");
    onSetupComplete?.();
  }, [isDesktop, onStatusChange, onSetupComplete]);

  const handleDownloadHF = useCallback(async (modelId: string) => {
    if (!isDesktop) {
      onStatusChange?.("Downloads require the desktop app");
      return;
    }

    // TODO: invoke('download_hf_model', { modelId })
    setHfModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "downloading", progress: 0 } : m
    ));

    for (let i = 0; i <= 100; i += 2) {
      await new Promise(resolve => setTimeout(resolve, 80));
      setHfModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, progress: i } : m
      ));
    }

    setHfModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "installed", progress: undefined } : m
    ));

    onStatusChange?.("AI model installed");
    onSetupComplete?.();
  }, [isDesktop, onStatusChange, onSetupComplete]);

  const handleDownloadPresidio = useCallback(async (componentId: string) => {
    if (!isDesktop) {
      onStatusChange?.("Downloads require the desktop app");
      return;
    }

    // TODO: invoke('install_presidio', { componentId })
    setPresidioComponents(prev => prev.map(c =>
      c.id === componentId ? { ...c, status: "downloading", progress: 0 } : c
    ));

    for (let i = 0; i <= 100; i += 3) {
      await new Promise(resolve => setTimeout(resolve, 80));
      setPresidioComponents(prev => prev.map(c =>
        c.id === componentId ? { ...c, progress: i } : c
      ));
    }

    setPresidioComponents(prev => prev.map(c =>
      c.id === componentId ? { ...c, status: "installed", progress: undefined } : c
    ));

    onStatusChange?.("Component installed");
    onSetupComplete?.();
  }, [isDesktop, onStatusChange, onSetupComplete]);

  const handleInstallAllPresidio = useCallback(async () => {
    for (const component of presidioComponents.filter(c => c.status === "not_installed")) {
      await handleDownloadPresidio(component.id);
    }
  }, [presidioComponents, handleDownloadPresidio]);

  const currentHardware = HARDWARE_REQUIREMENTS[activeTab];

  return (
    <main style={styles.main}>
      <div style={styles.header}>
        <h1 style={styles.title}>Setup</h1>
        <p style={styles.subtitle}>Download models for each protection level</p>
      </div>

      {/* Hardware Requirements */}
      <div style={styles.hardwareBanner}>
        <button style={styles.hardwareToggle} onClick={() => setShowHardwareInfo(!showHardwareInfo)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          <span>Hardware Requirements for {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Mode</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ transform: showHardwareInfo ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s", marginLeft: "auto" }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        {showHardwareInfo && (
          <div style={styles.hardwareDetails}>
            <div style={styles.hardwareGrid}>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>RAM</span>
                <span style={styles.hardwareValue}>{currentHardware.ram}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>Disk Space</span>
                <span style={styles.hardwareValue}>{currentHardware.disk}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>GPU</span>
                <span style={styles.hardwareValue}>{currentHardware.gpu}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>CPU</span>
                <span style={styles.hardwareValue}>{currentHardware.cpu}</span>
              </div>
            </div>
            <p style={styles.hardwareNote}>{currentHardware.note}</p>
          </div>
        )}
      </div>

      {/* Mode Cards */}
      <div style={styles.statusRow}>
        <div style={styles.statusCard(activeTab === "fast")} onClick={() => setActiveTab("fast")}>
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>⚡</span><span style={styles.statusName}>Fast</span></div>
          <div style={styles.statusCount}>{spacyInstalledCount}/{spacyModels.length} languages</div>
          <div style={styles.statusBadge(spacyInstalledCount > 0)}>{spacyInstalledCount > 0 ? "Ready" : "Setup needed"}</div>
        </div>
        <div style={styles.statusCard(activeTab === "accurate")} onClick={() => setActiveTab("accurate")}>
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>🎯</span><span style={styles.statusName}>Accurate</span></div>
          <div style={styles.statusCount}>{hfInstalledCount}/{hfModels.length} AI models</div>
          <div style={styles.statusBadge(hfInstalledCount > 0)}>{hfInstalledCount > 0 ? "Ready" : "Setup needed"}</div>
        </div>
        <div style={styles.statusCard(activeTab === "thorough")} onClick={() => setActiveTab("thorough")}>
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>🛡️</span><span style={styles.statusName}>Thorough</span></div>
          <div style={styles.statusCount}>{presidioInstalledCount}/{presidioRequiredCount} components</div>
          <div style={styles.statusBadge(presidioInstalledCount === presidioRequiredCount)}>{presidioInstalledCount === presidioRequiredCount ? "Ready" : "Setup needed"}</div>
        </div>
      </div>

      {/* FAST TAB */}
      {activeTab === "fast" && (
        <div style={styles.tabContent}>
          <div style={styles.tabHeader}>
            <h2 style={styles.tabTitle}>Fast Mode — spaCy Language Models</h2>
            <p style={styles.tabDesc}>Pattern-based detection. Each language requires its own model. <strong>Nothing bundled</strong> — download what you need.</p>
          </div>
          <div style={styles.modelGrid}>
            {spacyModels.map((m) => (
              <div key={m.id} style={styles.modelCard}>
                <div style={styles.modelCardHeader}>
                  <span style={styles.flag}>{m.flag}</span>
                  <div style={styles.modelInfo}><span style={styles.modelName}>{m.name}</span><span style={styles.modelSize}>{m.size}</span></div>
                  {m.status === "installed" ? <div style={styles.installedBadge}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg></div>
                    : m.status === "downloading" ? <div style={styles.downloadingBadge}>{m.progress}%</div>
                    : <button style={styles.downloadBtn} onClick={() => handleDownloadSpacy(m.id)} disabled={!isDesktop}>Download</button>}
                </div>
                {m.status === "downloading" && <div style={styles.progressBar}><div style={{ ...styles.progressFill, width: `${m.progress}%` }} /></div>}
              </div>
            ))}
          </div>
          <div style={styles.techNote}><strong>Technical:</strong> spaCy NER models. Command: <code>python -m spacy download en_core_web_sm</code></div>
        </div>
      )}

      {/* ACCURATE TAB */}
      {activeTab === "accurate" && (
        <div style={styles.tabContent}>
          <div style={styles.tabHeader}>
            <h2 style={styles.tabTitle}>Accurate Mode — HuggingFace AI Models</h2>
            <p style={styles.tabDesc}>Transformer-based AI for higher accuracy. Choose models for your languages.</p>
          </div>
          <div style={styles.hfModelList}>
            {hfModels.map((m) => (
              <div key={m.id} style={styles.hfModelCard(m.recommended)}>
                <div style={styles.hfModelHeader}>
                  <div style={styles.hfModelInfo}>
                    <span style={styles.hfModelName}>{m.name}{m.recommended && <span style={styles.recommendedTag}>Recommended</span>}</span>
                    <span style={styles.hfModelDesc}>{m.description}</span>
                    <div style={styles.hfModelMeta}><span style={styles.hfModelSize}>{m.size}</span><span style={styles.hfModelLangs}>{m.languages.join(", ").toUpperCase()}</span></div>
                  </div>
                  {m.status === "installed" ? <div style={styles.installedBadgeLarge}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>Installed</div>
                    : m.status === "downloading" ? <div style={styles.downloadingBadgeLarge}>{m.progress}%</div>
                    : <button style={styles.downloadBtnLarge} onClick={() => handleDownloadHF(m.id)} disabled={!isDesktop}>Download</button>}
                </div>
                {m.status === "downloading" && <div style={styles.progressBarLarge}><div style={{ ...styles.progressFill, width: `${m.progress}%` }} /></div>}
              </div>
            ))}
          </div>
          <div style={styles.techNote}><strong>Technical:</strong> HuggingFace Transformers. Cached in <code>~/.cache/huggingface</code></div>
        </div>
      )}

      {/* THOROUGH TAB */}
      {activeTab === "thorough" && (
        <div style={styles.tabContent}>
          <div style={styles.tabHeader}>
            <h2 style={styles.tabTitle}>Thorough Mode — Microsoft Presidio</h2>
            <p style={styles.tabDesc}>Enterprise-grade PII detection from Microsoft with pattern matching.</p>
          </div>
          <div style={styles.presidioHeader}>
            <span>All components required</span>
            {presidioInstalledCount < presidioRequiredCount && <button style={styles.installAllBtn} onClick={handleInstallAllPresidio} disabled={!isDesktop}>Install All</button>}
          </div>
          <div style={styles.presidioList}>
            {presidioComponents.map((c) => (
              <div key={c.id} style={styles.presidioCard}>
                <div style={styles.presidioCardHeader}>
                  <div style={styles.presidioInfo}>
                    <span style={styles.presidioName}>{c.name}{c.required && <span style={styles.requiredTag}>Required</span>}</span>
                    <span style={styles.presidioDesc}>{c.description}</span>
                    <span style={styles.presidioSize}>{c.size}</span>
                  </div>
                  {c.status === "installed" ? <div style={styles.installedBadgeLarge}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>Installed</div>
                    : c.status === "downloading" ? <div style={styles.downloadingBadgeLarge}>{c.progress}%</div>
                    : <button style={styles.downloadBtnLarge} onClick={() => handleDownloadPresidio(c.id)} disabled={!isDesktop}>Download</button>}
                </div>
                {c.status === "downloading" && <div style={styles.progressBarLarge}><div style={{ ...styles.progressFill, width: `${c.progress}%` }} /></div>}
              </div>
            ))}
          </div>
          <div style={styles.techNote}><strong>Technical:</strong> <code>pip install presidio-analyzer presidio-anonymizer</code></div>
        </div>
      )}

      <div style={styles.implNote}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <span><strong>Note:</strong> Downloads are UI preview only. Backend implementation required.</span>
      </div>

      <div style={styles.privacyNote}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span><strong>100% Offline.</strong> All models run locally. Documents never leave your device.</span>
      </div>
    </main>
  );
}

// ============================================================================
// Styles
// ============================================================================

const styles = {
  main: { maxWidth: 900, margin: "0 auto", padding: "40px 24px" } as React.CSSProperties,
  header: { marginBottom: 24 } as React.CSSProperties,
  title: { margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em", color: "#1d1d1f" } as React.CSSProperties,
  subtitle: { margin: "8px 0 0", fontSize: 15, color: "#6e6e73" } as React.CSSProperties,

  hardwareBanner: { background: "#fff", borderRadius: 12, marginBottom: 24, overflow: "hidden", border: "1px solid #e5e5e5" } as React.CSSProperties,
  hardwareToggle: { display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "14px 16px", fontSize: 14, fontWeight: 500, color: "#1d1d1f", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" as const } as React.CSSProperties,
  hardwareDetails: { padding: "0 16px 16px", borderTop: "1px solid #f0f0f0" } as React.CSSProperties,
  hardwareGrid: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, padding: "16px 0" } as React.CSSProperties,
  hardwareItem: { display: "flex", flexDirection: "column" as const, gap: 4 } as React.CSSProperties,
  hardwareLabel: { fontSize: 11, fontWeight: 600, color: "#6e6e73", textTransform: "uppercase" as const, letterSpacing: "0.05em" } as React.CSSProperties,
  hardwareValue: { fontSize: 13, fontWeight: 500, color: "#1d1d1f" } as React.CSSProperties,
  hardwareNote: { margin: 0, padding: 12, fontSize: 13, color: "#6e6e73", background: "#f9fafb", borderRadius: 8 } as React.CSSProperties,

  statusRow: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 } as React.CSSProperties,
  statusCard: (active: boolean) => ({ padding: 20, background: "#fff", borderRadius: 16, border: active ? "2px solid #3b82f6" : "2px solid transparent", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", cursor: "pointer", transition: "all 0.2s" }) as React.CSSProperties,
  statusHeader: { display: "flex", alignItems: "center", gap: 8, marginBottom: 8 } as React.CSSProperties,
  statusEmoji: { fontSize: 20 } as React.CSSProperties,
  statusName: { fontSize: 16, fontWeight: 600, color: "#1d1d1f" } as React.CSSProperties,
  statusCount: { fontSize: 13, color: "#6e6e73", marginBottom: 8 } as React.CSSProperties,
  statusBadge: (ready: boolean) => ({ display: "inline-block", padding: "4px 10px", fontSize: 12, fontWeight: 500, borderRadius: 6, background: ready ? "#dcfce7" : "#fef3c7", color: ready ? "#166534" : "#92400e" }) as React.CSSProperties,

  tabContent: { background: "#fff", borderRadius: 16, padding: 24, boxShadow: "0 1px 3px rgba(0,0,0,0.05)", marginBottom: 16 } as React.CSSProperties,
  tabHeader: { marginBottom: 20 } as React.CSSProperties,
  tabTitle: { margin: "0 0 8px", fontSize: 18, fontWeight: 600, color: "#1d1d1f" } as React.CSSProperties,
  tabDesc: { margin: 0, fontSize: 14, lineHeight: 1.6, color: "#6e6e73" } as React.CSSProperties,

  modelGrid: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12, marginBottom: 16 } as React.CSSProperties,
  modelCard: { padding: 14, background: "#f9fafb", borderRadius: 10, border: "1px solid #e5e5e5" } as React.CSSProperties,
  modelCardHeader: { display: "flex", alignItems: "center", gap: 12 } as React.CSSProperties,
  flag: { fontSize: 24 } as React.CSSProperties,
  modelInfo: { flex: 1 } as React.CSSProperties,
  modelName: { display: "block", fontSize: 14, fontWeight: 500, color: "#1d1d1f" } as React.CSSProperties,
  modelSize: { fontSize: 12, color: "#9ca3af" } as React.CSSProperties,
  installedBadge: { width: 28, height: 28, display: "flex", alignItems: "center", justifyContent: "center", background: "#dcfce7", color: "#166534", borderRadius: "50%" } as React.CSSProperties,
  downloadingBadge: { padding: "6px 10px", fontSize: 12, fontWeight: 500, background: "#fef3c7", color: "#92400e", borderRadius: 6 } as React.CSSProperties,
  downloadBtn: { padding: "6px 14px", fontSize: 13, fontWeight: 500, background: "#3b82f6", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" } as React.CSSProperties,
  progressBar: { height: 4, background: "#e5e5e5", borderRadius: 2, marginTop: 10, overflow: "hidden" } as React.CSSProperties,
  progressFill: { height: "100%", background: "linear-gradient(90deg, #3b82f6, #60a5fa)", transition: "width 0.2s" } as React.CSSProperties,

  hfModelList: { display: "flex", flexDirection: "column" as const, gap: 12, marginBottom: 16 } as React.CSSProperties,
  hfModelCard: (rec?: boolean) => ({ padding: 16, background: rec ? "#f0fdf4" : "#f9fafb", borderRadius: 10, border: rec ? "2px solid #10b981" : "1px solid #e5e5e5" }) as React.CSSProperties,
  hfModelHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 } as React.CSSProperties,
  hfModelInfo: { flex: 1 } as React.CSSProperties,
  hfModelName: { display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 600, color: "#1d1d1f", marginBottom: 4 } as React.CSSProperties,
  recommendedTag: { padding: "2px 8px", fontSize: 10, fontWeight: 600, background: "#10b981", color: "#fff", borderRadius: 4 } as React.CSSProperties,
  hfModelDesc: { display: "block", fontSize: 13, color: "#6e6e73", marginBottom: 8 } as React.CSSProperties,
  hfModelMeta: { display: "flex", gap: 16 } as React.CSSProperties,
  hfModelSize: { fontSize: 12, color: "#9ca3af" } as React.CSSProperties,
  hfModelLangs: { fontSize: 12, color: "#3b82f6", fontWeight: 500 } as React.CSSProperties,
  installedBadgeLarge: { display: "flex", alignItems: "center", gap: 6, padding: "8px 14px", fontSize: 13, fontWeight: 500, background: "#dcfce7", color: "#166534", borderRadius: 8, whiteSpace: "nowrap" as const } as React.CSSProperties,
  downloadingBadgeLarge: { padding: "8px 14px", fontSize: 13, fontWeight: 500, background: "#fef3c7", color: "#92400e", borderRadius: 8, whiteSpace: "nowrap" as const } as React.CSSProperties,
  downloadBtnLarge: { padding: "10px 20px", fontSize: 14, fontWeight: 600, background: "#3b82f6", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer", whiteSpace: "nowrap" as const } as React.CSSProperties,
  progressBarLarge: { height: 6, background: "#e5e5e5", borderRadius: 3, marginTop: 12, overflow: "hidden" } as React.CSSProperties,

  presidioHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, fontSize: 13, color: "#6e6e73" } as React.CSSProperties,
  installAllBtn: { padding: "8px 16px", fontSize: 13, fontWeight: 600, background: "#10b981", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer" } as React.CSSProperties,
  presidioList: { display: "flex", flexDirection: "column" as const, gap: 12, marginBottom: 16 } as React.CSSProperties,
  presidioCard: { padding: 16, background: "#f9fafb", borderRadius: 10, border: "1px solid #e5e5e5" } as React.CSSProperties,
  presidioCardHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 } as React.CSSProperties,
  presidioInfo: { flex: 1 } as React.CSSProperties,
  presidioName: { display: "flex", alignItems: "center", gap: 8, fontSize: 15, fontWeight: 600, color: "#1d1d1f", marginBottom: 4 } as React.CSSProperties,
  requiredTag: { padding: "2px 6px", fontSize: 10, fontWeight: 600, background: "#fee2e2", color: "#dc2626", borderRadius: 4 } as React.CSSProperties,
  presidioDesc: { display: "block", fontSize: 13, color: "#6e6e73", marginBottom: 4 } as React.CSSProperties,
  presidioSize: { fontSize: 12, color: "#9ca3af" } as React.CSSProperties,

  techNote: { padding: 12, background: "#f1f5f9", borderRadius: 8, fontSize: 12, color: "#475569" } as React.CSSProperties,
  implNote: { display: "flex", alignItems: "center", gap: 10, padding: 14, background: "#fffbeb", borderRadius: 10, fontSize: 13, color: "#92400e", marginBottom: 16 } as React.CSSProperties,
  privacyNote: { display: "flex", alignItems: "center", gap: 12, padding: 16, background: "#ecfdf5", borderRadius: 12, fontSize: 14, color: "#065f46" } as React.CSSProperties,
};

export default ModelManager;
