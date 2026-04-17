import React, { useState, useCallback, useEffect } from "react";
import { invokeBackend, uninstallModel, getDiskUsage, DiskUsage } from "./api";
import { t, LangCode } from "./i18n";
import { listen } from "@tauri-apps/api/event";

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
  modelType: "spacy" | "presidio";
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

export async function getModelSetupStatus(): Promise<ModelSetupStatus> {
  try {
    const status = await invokeBackend<{
      spacy_models: Record<string, string>;
      presidio_available: boolean;
      transformers_available: boolean;
    }>("get_model_status");

    const installedSpacy = Object.entries(status.spacy_models)
      .filter(([, s]) => s === "installed")
      .map(([name]) => name);

    // Deduplicate by language code: en_core_web_sm and en_core_web_lg both represent
    // "English" and should count as one language, not two.
    const uniqueLangCodes = [...new Set(installedSpacy.map(m => m.split("_")[0]))];

    const missingLayers: number[] = [];
    if (installedSpacy.length === 0) missingLayers.push(1);
    if (!status.transformers_available) missingLayers.push(2);
    if (!status.presidio_available) missingLayers.push(3);

    return {
      ready: missingLayers.length === 0,
      missingLayers,
      installedLanguages: uniqueLangCodes,
    };
  } catch {
    // Fallback for browser preview mode
    return {
      ready: false,
      missingLayers: [1, 2, 3],
      installedLanguages: [],
    };
  }
}

// ============================================================================
// Helpers
// ============================================================================

function formatMB(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(1);
}

// ============================================================================
// Component
// ============================================================================

type Props = {
  isDesktop: boolean;
  uiLang?: LangCode;
  onStatusChange?: (message: string) => void;
  onSetupComplete?: () => void;
};

export function ModelManager({ isDesktop, uiLang = "en", onStatusChange, onSetupComplete }: Props) {
  const [activeTab, setActiveTab] = useState<"fast" | "accurate" | "thorough">("fast");
  const [showHardwareInfo, setShowHardwareInfo] = useState(false);
  const [hfLangFilter, setHfLangFilter] = useState("all");

  // Disk usage state
  const [diskUsage, setDiskUsage] = useState<DiskUsage | null>(null);

  // Inline uninstall confirmation: stores the model id awaiting confirmation, or null
  const [confirmUninstallId, setConfirmUninstallId] = useState<string | null>(null);

  // Page is immediately usable — we pre-populate known bundled state below.
  // The async fetch only updates additionally-downloaded models.
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  // Transformers (torch + HuggingFace) are bundled in the binary — default to true.
  // The async sidecar fetch will correct this if something is wrong with the install.
  const [transformersAvailable, setTransformersAvailable] = useState(true);

  // ========== FAST MODE: spaCy Models ==========
  // Large models (lg) where available — used by both Fast (Layer 1) and Thorough (Layer 3 Presidio).
  // hr and ko have no lg release; en_core_web_sm is bundled in the binary.
  const [spacyModels, setSpacyModels] = useState<SpacyModel[]>([
    // EU official languages (alphabetical by English name)
    { id: "bg_core_news_lg", name: "Bulgarian",      flag: "BG", size: "~500 MB", status: "not_installed" },
    { id: "hr_core_news_sm", name: "Croatian",       flag: "HR", size: "13 MB",   status: "not_installed" }, // no lg
    { id: "cs_core_news_lg", name: "Czech",          flag: "CS", size: "~500 MB", status: "not_installed" },
    { id: "da_core_news_lg", name: "Danish",         flag: "DA", size: "~500 MB", status: "not_installed" },
    { id: "nl_core_news_lg", name: "Dutch",          flag: "NL", size: "~500 MB", status: "not_installed" },
    { id: "en_core_web_sm",  name: "English",        flag: "EN", size: "12 MB",   status: "installed"     }, // bundled
    { id: "en_core_web_lg",  name: "English (Large)",flag: "EN", size: "560 MB",  status: "not_installed" },
    { id: "fi_core_news_lg", name: "Finnish",        flag: "FI", size: "~500 MB", status: "not_installed" },
    { id: "fr_core_news_lg", name: "French",         flag: "FR", size: "~500 MB", status: "not_installed" },
    { id: "de_core_news_lg", name: "German",         flag: "DE", size: "~500 MB", status: "not_installed" },
    { id: "el_core_news_lg", name: "Greek",          flag: "EL", size: "~500 MB", status: "not_installed" },
    { id: "it_core_news_lg", name: "Italian",        flag: "IT", size: "~500 MB", status: "not_installed" },
    { id: "lt_core_news_lg", name: "Lithuanian",     flag: "LT", size: "~500 MB", status: "not_installed" },
    { id: "pl_core_news_lg", name: "Polish",         flag: "PL", size: "~500 MB", status: "not_installed" },
    { id: "pt_core_news_lg", name: "Portuguese",     flag: "PT", size: "~500 MB", status: "not_installed" },
    { id: "ro_core_news_lg", name: "Romanian",       flag: "RO", size: "~500 MB", status: "not_installed" },
    { id: "sk_core_news_lg", name: "Slovak",         flag: "SK", size: "~500 MB", status: "not_installed" },
    { id: "sl_core_news_lg", name: "Slovenian",      flag: "SL", size: "~500 MB", status: "not_installed" },
    { id: "es_core_news_lg", name: "Spanish",        flag: "ES", size: "~500 MB", status: "not_installed" },
    { id: "sv_core_news_lg", name: "Swedish",        flag: "SV", size: "~500 MB", status: "not_installed" },
    // Additional languages
    { id: "ru_core_news_lg", name: "Russian",        flag: "RU", size: "~500 MB", status: "not_installed" },
    { id: "zh_core_web_lg",  name: "Chinese",        flag: "ZH", size: "~700 MB", status: "not_installed" },
    { id: "ja_core_news_lg", name: "Japanese",       flag: "JA", size: "~500 MB", status: "not_installed" },
    { id: "ko_core_news_sm", name: "Korean",         flag: "KO", size: "12 MB",   status: "not_installed" }, // no lg
  ]);

  // ========== ACCURATE MODE: HuggingFace Models ==========
  const [hfModels, setHfModels] = useState<HuggingFaceModel[]>([
    // -- Multilingual (recommended starting point) --
    {
      id: "Davlan/bert-base-multilingual-cased-ner-hrl",
      name: "Multilingual BERT NER",
      description: "EN, NL, DE, FR, ES, IT, PT, PL, RU, ZH -- fast, 680 MB",
      size: "680 MB",
      languages: ["en", "nl", "de", "fr", "es", "it", "pt", "pl", "ru", "zh"],
      recommended: true,
      status: "not_installed",
    },
    {
      id: "Davlan/xlm-roberta-large-ner-hrl",
      name: "XLM-RoBERTa Large NER",
      description: "All 24 EU official languages + more -- highest accuracy, 2.2 GB",
      size: "2.2 GB",
      languages: ["multilingual"],
      status: "not_installed",
    },
    {
      id: "Babelscape/wikineural-multilingual-ner",
      name: "WikiNEuRal (9 languages)",
      description: "IT, DE, ES, FR, NL, PL, PT, RU, EN -- trained on Wikipedia",
      size: "1.1 GB",
      languages: ["it", "de", "es", "fr", "nl", "pl", "pt", "ru", "en"],
      status: "not_installed",
    },
    // -- Western European --
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
    {
      id: "wietsedv/bert-base-dutch-cased-finetuned-conll2002-ner",
      name: "BERT NER (Dutch)",
      description: "Specialized Dutch NER, trained on CoNLL-2002",
      size: "420 MB",
      languages: ["nl"],
      status: "not_installed",
    },
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
    {
      id: "Jean-Baptiste/camembert-ner",
      name: "CamemBERT NER (French)",
      description: "French NER based on CamemBERT",
      size: "420 MB",
      languages: ["fr"],
      status: "not_installed",
    },
    {
      id: "mrm8488/bert-spanish-cased-finetuned-ner",
      name: "BETO NER (Spanish)",
      description: "Spanish BERT fine-tuned for NER",
      size: "420 MB",
      languages: ["es"],
      status: "not_installed",
    },
    {
      id: "neuraly/bert-base-italian-cased-ner",
      name: "BERT NER (Italian)",
      description: "Italian NER fine-tuned BERT",
      size: "420 MB",
      languages: ["it"],
      status: "not_installed",
    },
    {
      id: "lxyuan/distilbert-base-multilingual-cased-ner-hrl",
      name: "DistilBERT NER (Portuguese)",
      description: "Lightweight multilingual NER including Portuguese",
      size: "250 MB",
      languages: ["pt"],
      status: "not_installed",
    },
    // -- Northern European --
    {
      id: "KB/bert-base-swedish-cased-ner",
      name: "BERT NER (Swedish)",
      description: "Swedish NER by the National Library of Sweden",
      size: "420 MB",
      languages: ["sv"],
      status: "not_installed",
    },
    {
      id: "saattrupdan/nbailab-base-ner-scandi",
      name: "ScandiBERT NER",
      description: "Covers Danish, Norwegian, and Swedish NER",
      size: "420 MB",
      languages: ["da", "sv"],
      status: "not_installed",
    },
    {
      id: "Finnish-NLP/bert-large-finnish-cased-ner",
      name: "BERT NER (Finnish)",
      description: "Finnish NER by the Finnish NLP group",
      size: "420 MB",
      languages: ["fi"],
      status: "not_installed",
    },
    // -- Central & Eastern European --
    {
      id: "clarin-pl/roberta-base-ner",
      name: "RoBERTa NER (Polish)",
      description: "Polish NER by CLARIN-PL",
      size: "420 MB",
      languages: ["pl"],
      status: "not_installed",
    },
    {
      id: "dumitrescustefan/bert-base-romanian-ner-v1",
      name: "BERT NER (Romanian)",
      description: "Romanian NER by Stefan Dumitrescu",
      size: "420 MB",
      languages: ["ro"],
      status: "not_installed",
    },
    {
      id: "fav-kky/ElectraCzech",
      name: "Electra NER (Czech)",
      description: "Czech NER based on Electra",
      size: "420 MB",
      languages: ["cs"],
      status: "not_installed",
    },
    {
      id: "gerulata/SlovakBERT",
      name: "SlovakBERT NER",
      description: "Slovak language model for NER",
      size: "420 MB",
      languages: ["sk"],
      status: "not_installed",
    },
    {
      id: "classla/bcms-bertic",
      name: "BERTic NER (Croatian/Slovenian)",
      description: "Covers Croatian (hr) and Slovenian (sl) NER",
      size: "420 MB",
      languages: ["hr", "sl"],
      status: "not_installed",
    },
    {
      id: "SZTAKI-HLT/hubert-base-cc",
      name: "HuBERT (Hungarian)",
      description: "Hungarian language model for NER",
      size: "420 MB",
      languages: ["hu"],
      status: "not_installed",
    },
    // -- Southern European --
    {
      id: "gealexandri/greek-bert-model",
      name: "BERT NER (Greek)",
      description: "Greek language model for NER",
      size: "420 MB",
      languages: ["el"],
      status: "not_installed",
    },
    // -- Baltic --
    {
      id: "EMBEDDIA/litlat-bert",
      name: "LitLat BERT (Lithuanian/Latvian)",
      description: "Covers Lithuanian (lt) and Latvian (lv) NER",
      size: "420 MB",
      languages: ["lt", "lv"],
      status: "not_installed",
    },
    // -- Slavic / Additional --
    {
      id: "DeepPavlov/rubert-base-cased-ner",
      name: "RuBERT NER (Russian)",
      description: "Russian NER by DeepPavlov",
      size: "680 MB",
      languages: ["ru"],
      status: "not_installed",
    },
    {
      id: "uer/roberta-base-finetuned-cluener2020-chinese-simplified",
      name: "RoBERTa NER (Chinese)",
      description: "Chinese NER fine-tuned on CLUE NER",
      size: "420 MB",
      languages: ["zh"],
      status: "not_installed",
    },
    {
      id: "cl-tohoku/bert-base-japanese-v3",
      name: "BERT NER (Japanese)",
      description: "Japanese BERT base model for NER",
      size: "420 MB",
      languages: ["ja"],
      status: "not_installed",
    },
  ]);

  // ========== THOROUGH MODE: Presidio Components ==========
  const [presidioComponents, setPresidioComponents] = useState<PresidioComponent[]>([
    {
      id: "presidio-analyzer",
      name: "Presidio Analyzer",
      description: "Core PII detection engine from Microsoft",
      size: "Bundled",
      status: "installed",
      required: true,
      modelType: "presidio",
    },
    {
      id: "presidio-anonymizer",
      name: "Presidio Anonymizer",
      description: "Anonymization and pseudonymization engine",
      size: "Bundled",
      status: "installed",
      required: true,
      modelType: "presidio",
    },
  ]);

  // ========== Disk Usage ==========

  const refreshDiskUsage = useCallback(async () => {
    if (!isDesktop) return;
    try {
      const usage = await getDiskUsage();
      setDiskUsage(usage);
    } catch {
      // Ignore if sidecar not running
    }
  }, [isDesktop]);

  // Listen for real-time download progress events from the Rust sidecar
  useEffect(() => {
    if (!isDesktop) return;
    const unlisten = listen<{ model_id: string; percent: number }>(
      "download-progress",
      (event) => {
        const { model_id, percent } = event.payload;
        setSpacyModels(prev =>
          prev.map(m => m.id === model_id ? { ...m, progress: percent } : m)
        );
        setHfModels(prev =>
          prev.map(m => m.id === model_id ? { ...m, progress: percent } : m)
        );
        setPresidioComponents(prev =>
          prev.map(c => c.id === model_id ? { ...c, progress: percent } : c)
        );
      }
    );
    return () => { unlisten.then(fn => fn()); };
  }, [isDesktop]);

  // Fetch installed status and disk usage on mount
  useEffect(() => {
    if (!isDesktop) {
      setIsLoadingStatus(false);
      return;
    }

    type ModelStatusPayload = {
      spacy_models: Record<string, string>;
      presidio_available: boolean;
      transformers_available: boolean;
    };

    const applyStatus = (status: ModelStatusPayload) => {
      setSpacyModels(prev => prev.map(m => ({
        ...m,
        status: status.spacy_models[m.id] === "installed" ? "installed" as const : "not_installed" as const,
      })));
      if (status.presidio_available) {
        setPresidioComponents(prev => prev.map(c => ({ ...c, status: "installed" as const })));
      }
      setTransformersAvailable(status.transformers_available);
    };

    // Show cached status immediately so the page appears instant
    const CACHE_KEY = "redactly_model_status_v1";
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        applyStatus(JSON.parse(cached));
        setIsLoadingStatus(false);
      }
    } catch { /* corrupt cache — ignore */ }

    (async () => {
      try {
        const status = await invokeBackend<ModelStatusPayload>("get_model_status");
        applyStatus(status);
        try { localStorage.setItem(CACHE_KEY, JSON.stringify(status)); } catch { /* quota */ }
      } catch {
        // Non-desktop or sidecar not running -- keep defaults
      } finally {
        setIsLoadingStatus(false);
      }

      // Load initial disk usage
      await refreshDiskUsage();
    })();
  }, [isDesktop, refreshDiskUsage]);

  // Counts
  const spacyInstalledCount = spacyModels.filter(m => m.status === "installed").length;
  const hfInstalledCount = hfModels.filter(m => m.status === "installed").length;
  const presidioInstalledCount = presidioComponents.filter(c => c.status === "installed").length;
  const presidioRequiredCount = presidioComponents.filter(c => c.required).length;

  // Download handlers -- call real Tauri backend

  const handleDownloadSpacy = useCallback(async (modelId: string) => {
    if (!isDesktop) {
      onStatusChange?.(t(uiLang, "mm_desktop_only"));
      return;
    }

    setSpacyModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "downloading", progress: 0 } : m
    ));

    try {
      await invokeBackend("download_model", { modelType: "spacy", modelId });

      setSpacyModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "installed", progress: undefined } : m
      ));
      onStatusChange?.(t(uiLang, "mm_lang_installed"));
      onSetupComplete?.();
      await refreshDiskUsage();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setSpacyModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "error", progress: undefined } : m
      ));
      onStatusChange?.(`${t(uiLang, "mm_download_failed")} ${msg}`);
    }
  }, [isDesktop, uiLang, onStatusChange, onSetupComplete, refreshDiskUsage]);

  const handleDownloadHF = useCallback(async (modelId: string) => {
    if (!isDesktop) {
      onStatusChange?.(t(uiLang, "mm_desktop_only"));
      return;
    }

    setHfModels(prev => prev.map(m =>
      m.id === modelId ? { ...m, status: "downloading", progress: 0 } : m
    ));

    try {
      await invokeBackend("download_model", { modelType: "huggingface", modelId });

      setHfModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "installed", progress: undefined } : m
      ));
      onStatusChange?.(t(uiLang, "mm_ai_installed"));
      onSetupComplete?.();
      await refreshDiskUsage();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setHfModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "error", progress: undefined } : m
      ));
      onStatusChange?.(`${t(uiLang, "mm_download_failed")} ${msg}`);
    }
  }, [isDesktop, uiLang, onStatusChange, onSetupComplete, refreshDiskUsage]);

  const handleDownloadPresidio = useCallback(async (componentId: string) => {
    if (!isDesktop) {
      onStatusChange?.(t(uiLang, "mm_desktop_only"));
      return;
    }

    setPresidioComponents(prev => prev.map(c =>
      c.id === componentId ? { ...c, status: "downloading", progress: 0 } : c
    ));

    try {
      const component = presidioComponents.find(c => c.id === componentId);
      const modelType = component?.modelType ?? "presidio";
      await invokeBackend("download_model", { modelType, modelId: componentId });

      setPresidioComponents(prev => prev.map(c =>
        c.id === componentId ? { ...c, status: "installed", progress: undefined } : c
      ));
      onStatusChange?.(t(uiLang, "mm_comp_installed"));
      onSetupComplete?.();
      await refreshDiskUsage();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setPresidioComponents(prev => prev.map(c =>
        c.id === componentId ? { ...c, status: "error", progress: undefined } : c
      ));
      onStatusChange?.(`${t(uiLang, "mm_install_failed")} ${msg}`);
    }
  }, [isDesktop, uiLang, onStatusChange, onSetupComplete, refreshDiskUsage, presidioComponents]);

  // Uninstall handlers

  const handleUninstallSpacy = useCallback(async (modelId: string) => {
    setConfirmUninstallId(null);
    try {
      await uninstallModel("spacy", modelId);
      setSpacyModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "not_installed", progress: undefined } : m
      ));
      onStatusChange?.(t(uiLang, "mm_uninstalled"));
      await refreshDiskUsage();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      onStatusChange?.(`${t(uiLang, "mm_uninstall_failed")} ${msg}`);
    }
  }, [uiLang, onStatusChange, refreshDiskUsage]);

  const handleUninstallHF = useCallback(async (modelId: string) => {
    setConfirmUninstallId(null);
    try {
      await uninstallModel("huggingface", modelId);
      setHfModels(prev => prev.map(m =>
        m.id === modelId ? { ...m, status: "not_installed", progress: undefined } : m
      ));
      onStatusChange?.(t(uiLang, "mm_uninstalled"));
      await refreshDiskUsage();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      onStatusChange?.(`${t(uiLang, "mm_uninstall_failed")} ${msg}`);
    }
  }, [uiLang, onStatusChange, refreshDiskUsage]);

  const currentHardware = HARDWARE_REQUIREMENTS[activeTab];

  // Disk usage banner values
  const spacyMB = diskUsage ? formatMB(diskUsage.spacy_models_bytes) : null;
  const hfMB = diskUsage ? formatMB(diskUsage.hf_cache_bytes) : null;
  const totalMB = diskUsage
    ? formatMB(diskUsage.spacy_models_bytes + diskUsage.hf_cache_bytes)
    : null;

  return (
    <main style={styles.main}>
      <div style={styles.header}>
        <h1 style={styles.title}>{t(uiLang, "nav_setup")}</h1>
        <p style={styles.subtitle}>{t(uiLang, "mm_subtitle")}</p>
      </div>

      {/* Disk Usage Banner */}
      {isDesktop && diskUsage !== null && (
        <div style={styles.diskBanner}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
          <span style={styles.diskBannerText}>
            Disk usage:
            <span style={styles.diskBannerSegment}>spaCy {spacyMB} MB</span>
            <span style={styles.diskBannerDivider}>|</span>
            <span style={styles.diskBannerSegment}>HuggingFace {hfMB} MB</span>
            <span style={styles.diskBannerDivider}>|</span>
            <strong>Total {totalMB} MB</strong>
          </span>
        </div>
      )}

      {/* Hardware Requirements */}
      <div style={styles.hardwareBanner}>
        <button style={styles.hardwareToggle} onClick={() => setShowHardwareInfo(!showHardwareInfo)}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          <span>{t(uiLang, "mm_hardware_req").replace("{mode}", t(uiLang, activeTab === "accurate" ? "quality_accurate" : activeTab === "thorough" ? "quality_thorough" : "quality_fast"))}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ transform: showHardwareInfo ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s", marginLeft: "auto" }}>
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        {showHardwareInfo && (
          <div style={styles.hardwareDetails}>
            <div style={styles.hardwareGrid}>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>{t(uiLang, "mm_ram")}</span>
                <span style={styles.hardwareValue}>{currentHardware.ram}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>{t(uiLang, "mm_disk")}</span>
                <span style={styles.hardwareValue}>{currentHardware.disk}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>{t(uiLang, "mm_gpu")}</span>
                <span style={styles.hardwareValue}>{currentHardware.gpu}</span>
              </div>
              <div style={styles.hardwareItem}>
                <span style={styles.hardwareLabel}>{t(uiLang, "mm_cpu")}</span>
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
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>⚡</span><span style={styles.statusName}>{t(uiLang, "quality_fast")}</span></div>
          <div style={styles.statusCount}>{isLoadingStatus ? "…" : `${spacyInstalledCount}/${spacyModels.length}`} {t(uiLang, "mm_languages")}</div>
          <div style={styles.statusBadge(spacyInstalledCount > 0)}>{spacyInstalledCount > 0 ? t(uiLang, "mm_ready") : t(uiLang, "quality_setup_req")}</div>
        </div>
        <div style={styles.statusCard(activeTab === "accurate")} onClick={() => setActiveTab("accurate")}>
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>🎯</span><span style={styles.statusName}>{t(uiLang, "quality_accurate")}</span></div>
          <div style={styles.statusCount}>{isLoadingStatus ? "…" : `${hfInstalledCount}/${hfModels.length}`} {t(uiLang, "mm_ai_models")}</div>
          <div style={styles.statusBadge(hfInstalledCount > 0)}>{hfInstalledCount > 0 ? t(uiLang, "mm_ready") : t(uiLang, "quality_setup_req")}</div>
        </div>
        <div style={styles.statusCard(activeTab === "thorough")} onClick={() => setActiveTab("thorough")}>
          <div style={styles.statusHeader}><span style={styles.statusEmoji}>🛡️</span><span style={styles.statusName}>{t(uiLang, "quality_thorough")}</span></div>
          <div style={styles.statusCount}>{presidioInstalledCount}/{presidioRequiredCount} {t(uiLang, "mm_components")}</div>
          <div style={styles.statusBadge(presidioInstalledCount === presidioRequiredCount)}>{presidioInstalledCount === presidioRequiredCount ? t(uiLang, "mm_ready") : t(uiLang, "quality_setup_req")}</div>
        </div>
      </div>

      {/* FAST TAB */}
      {activeTab === "fast" && (
        <div style={styles.tabContent}>
          <div style={styles.tabHeader}>
            <h2 style={styles.tabTitle}>Fast Mode — spaCy Language Models</h2>
            <p style={styles.tabDesc}>Downloads the <strong>large</strong> spaCy model for each language (~500 MB each). Large models are used by both Fast (Layer 1) and Thorough (Layer 3) — one download covers both. English small model is bundled; Croatian and Korean have no large release.</p>
          </div>
          <div style={styles.modelGrid}>
            {spacyModels.map((m) => (
              <div key={m.id} style={styles.modelCard}>
                <div style={styles.modelCardHeader}>
                  <span style={styles.flag}>{m.id.slice(0, 2).toUpperCase()}</span>
                  <div style={styles.modelInfo}><span style={styles.modelName}>{m.name}</span><span style={styles.modelSize}>{m.size}</span></div>
                  {m.status === "installed" ? (
                    <div style={styles.installedGroup}>
                      <div style={styles.installedBadge}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                      </div>
                      {confirmUninstallId === m.id ? (
                        <div style={styles.confirmRow}>
                          <span style={styles.confirmText}>Remove?</span>
                          <button style={styles.confirmYesBtn} onClick={() => handleUninstallSpacy(m.id)}>Yes</button>
                          <button style={styles.confirmNoBtn} onClick={() => setConfirmUninstallId(null)}>No</button>
                        </div>
                      ) : (
                        <button
                          style={styles.uninstallBtn}
                          onClick={() => setConfirmUninstallId(m.id)}
                          title="Uninstall model"
                          disabled={!isDesktop}
                        >
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v6M14 11v6" />
                            <path d="M9 6V4h6v2" />
                          </svg>
                        </button>
                      )}
                    </div>
                  ) : m.status === "downloading" ? <div style={styles.downloadingBadge}>{m.progress ?? 0}%</div>
                    : m.status === "error" ? <button style={styles.retryBtn} onClick={() => handleDownloadSpacy(m.id)} title={t(uiLang, "mm_download_failed")}>↺</button>
                    : <button style={styles.downloadBtn} onClick={() => handleDownloadSpacy(m.id)} disabled={!isDesktop}>{t(uiLang, "mm_download")}</button>}
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
          {!transformersAvailable && (
            <div style={styles.notAvailableNote}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v4M12 16h.01" />
                </svg>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: "#1e1b4b", marginBottom: 4 }}>
                    AI-Powered Mode
                  </div>
                  <div style={{ fontSize: 13, color: "#4338ca", lineHeight: 1.5 }}>
                    Transformer inference is available — download a model below to activate it. Models are cached on your device and used automatically on subsequent runs. For most legal documents, <strong>Layer 3 (Presidio)</strong> — already installed — provides excellent coverage without any additional downloads.
                  </div>
                </div>
              </div>
            </div>
          )}
          {/* Language filter */}
          <div style={styles.hfFilterRow}>
            <span style={styles.hfFilterLabel}>Filter by language:</span>
            <div style={styles.hfFilterChips}>
              {["all", ...Array.from(new Set(hfModels.flatMap(m => m.languages))).sort()].map(lang => (
                <button
                  key={lang}
                  style={styles.hfFilterChip(hfLangFilter === lang)}
                  onClick={() => setHfLangFilter(lang)}
                >
                  {lang === "all" ? "All" : lang === "multilingual" ? "Multilingual" : lang.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div style={styles.hfModelList}>
            {hfModels.filter(m =>
              hfLangFilter === "all" ||
              m.languages.includes(hfLangFilter) ||
              m.languages.includes("multilingual")
            ).map((m) => (
              <div key={m.id} style={styles.hfModelCard(m.recommended)}>
                <div style={styles.hfModelHeader}>
                  <div style={styles.hfModelInfo}>
                    <span style={styles.hfModelName}>{m.name}{m.recommended && <span style={styles.recommendedTag}>{t(uiLang, "mm_recommended")}</span>}</span>
                    <span style={styles.hfModelDesc}>{m.description}</span>
                    <div style={styles.hfModelMeta}><span style={styles.hfModelSize}>{m.size}</span><span style={styles.hfModelLangs}>{m.languages.join(", ").toUpperCase()}</span></div>
                  </div>
                  {m.status === "installed" ? (
                    <div style={styles.installedGroupLarge}>
                      <div style={styles.installedBadgeLarge}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                        {t(uiLang, "mm_installed")}
                      </div>
                      {confirmUninstallId === m.id ? (
                        <div style={styles.confirmRow}>
                          <span style={styles.confirmText}>Remove?</span>
                          <button style={styles.confirmYesBtn} onClick={() => handleUninstallHF(m.id)}>Yes</button>
                          <button style={styles.confirmNoBtn} onClick={() => setConfirmUninstallId(null)}>No</button>
                        </div>
                      ) : (
                        <button
                          style={styles.uninstallBtnLarge}
                          onClick={() => setConfirmUninstallId(m.id)}
                          title="Uninstall model"
                          disabled={!isDesktop}
                        >
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v6M14 11v6" />
                            <path d="M9 6V4h6v2" />
                          </svg>
                          Uninstall
                        </button>
                      )}
                    </div>
                  ) : m.status === "downloading" ? <div style={styles.downloadingBadgeLarge}>{m.progress ?? 0}%</div>
                    : m.status === "error" ? <button style={styles.retryBtnLarge} onClick={() => handleDownloadHF(m.id)} title={t(uiLang, "mm_download_failed")}>↺ {t(uiLang, "mm_download")}</button>
                    : <button style={styles.downloadBtnLarge} onClick={() => isDesktop && handleDownloadHF(m.id)} disabled={!isDesktop}>{t(uiLang, "mm_download")}</button>}
                </div>
                {m.status === "downloading" && <div style={styles.progressBarLarge}><div style={{ ...styles.progressFill, width: `${m.progress ?? 0}%` }} /></div>}
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
            <p style={styles.tabDesc}>
              Enterprise-grade PII detection powered by <strong>Microsoft Presidio</strong>.
              Presidio uses <strong>spaCy</strong> as its NLP backbone — install a spaCy model for any
              language to enable native detection for that language.
            </p>
          </div>

          {/* Core engine — always bundled */}
          <div style={{ fontSize: 12, fontWeight: 600, color: "#6e6e73", textTransform: "uppercase" as const, letterSpacing: "0.06em", marginBottom: 10 }}>
            Core Engine — Always Bundled
          </div>
          <div style={styles.presidioList}>
            {presidioComponents.map((c) => (
              <div key={c.id} style={styles.presidioCard}>
                <div style={styles.presidioCardHeader}>
                  <div style={styles.presidioInfo}>
                    <span style={styles.presidioName}>{c.name}<span style={styles.requiredTag}>{t(uiLang, "mm_required")}</span></span>
                    <span style={styles.presidioDesc}>{c.description}</span>
                  </div>
                  {c.status === "installed" ? (
                    <div style={styles.installedGroupLarge}>
                      <div style={styles.installedBadgeLarge}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>
                        {t(uiLang, "mm_installed")}
                      </div>
                      <div style={styles.bundledNote}>Bundled — always available</div>
                    </div>
                  ) : c.status === "downloading" ? (
                    <div style={styles.downloadingBadgeLarge}>{c.progress ?? 0}%</div>
                  ) : c.status === "error" ? (
                    <button style={styles.retryBtnLarge} onClick={() => handleDownloadPresidio(c.id)}>↺ {t(uiLang, "mm_download")}</button>
                  ) : (
                    <button style={styles.downloadBtnLarge} onClick={() => handleDownloadPresidio(c.id)} disabled={!isDesktop}>{t(uiLang, "mm_download")}</button>
                  )}
                </div>
                {c.status === "downloading" && <div style={styles.progressBarLarge}><div style={{ ...styles.progressFill, width: `${c.progress}%` }} /></div>}
              </div>
            ))}
          </div>

          {/* Language models */}
          <div style={{ marginTop: 24, marginBottom: 10, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#6e6e73", textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>
              spaCy Language Models
            </div>
            <button
              style={{ fontSize: 12, fontWeight: 500, color: "#3b82f6", background: "transparent", border: "1px solid #bfdbfe", borderRadius: 6, padding: "4px 10px", cursor: "pointer" }}
              onClick={() => setActiveTab("fast")}
            >
              Download models →
            </button>
          </div>
          <p style={{ margin: "0 0 12px", fontSize: 13, color: "#6e6e73", lineHeight: 1.6 }}>
            Thorough mode automatically picks the best installed model for each language (large preferred over small).
            If no model is installed for a language, it falls back to English. All EU languages, plus Russian,
            Chinese, Japanese, and Korean are supported — install their model from the <strong>Fast Languages</strong> tab.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 8 }}>
            {spacyModels.map(m => (
              <div key={m.id} style={{ padding: "8px 10px", borderRadius: 8, background: m.status === "installed" ? "#f0fdf4" : "#f9fafb", border: m.status === "installed" ? "1px solid #bbf7d0" : "1px solid #e5e5e5", display: "flex", alignItems: "center", gap: 8 }}>
                <span style={styles.flag}>{m.flag}</span>
                <span style={{ flex: 1, fontSize: 12, fontWeight: 500, color: "#1d1d1f", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const }}>{m.name}</span>
                {m.status === "installed" ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="3" style={{ flexShrink: 0 }}><polyline points="20 6 9 17 4 12" /></svg>
                ) : (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="2" style={{ flexShrink: 0 }}><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                )}
              </div>
            ))}
          </div>

          <div style={{ ...styles.techNote, marginTop: 20 }}>
            <strong>How it works:</strong> Presidio (<code>presidio-analyzer</code> + <code>presidio-anonymizer</code>) runs the detection pipeline. spaCy provides the NLP backbone — swap in any language model to support that language natively.
          </div>
        </div>
      )}

      <div style={styles.privacyNote}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>{t(uiLang, "mm_privacy")}</span>
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

  diskBanner: { display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", background: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: 10, marginBottom: 16, fontSize: 13, color: "#0369a1" } as React.CSSProperties,
  diskBannerText: { display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" as const } as React.CSSProperties,
  diskBannerSegment: { fontWeight: 500 } as React.CSSProperties,
  diskBannerDivider: { color: "#7dd3fc", fontWeight: 400 } as React.CSSProperties,

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
  flag: { fontSize: 11, fontWeight: 700, letterSpacing: "0.5px", background: "rgba(0,0,0,0.07)", borderRadius: 4, padding: "3px 6px", color: "#555", minWidth: 28, textAlign: "center" } as React.CSSProperties,
  modelInfo: { flex: 1 } as React.CSSProperties,
  modelName: { display: "block", fontSize: 14, fontWeight: 500, color: "#1d1d1f" } as React.CSSProperties,
  modelSize: { fontSize: 12, color: "#9ca3af" } as React.CSSProperties,

  installedGroup: { display: "flex", alignItems: "center", gap: 6 } as React.CSSProperties,
  installedBadge: { width: 28, height: 28, display: "flex", alignItems: "center", justifyContent: "center", background: "#dcfce7", color: "#166534", borderRadius: "50%" } as React.CSSProperties,
  uninstallBtn: { width: 28, height: 28, display: "flex", alignItems: "center", justifyContent: "center", background: "#fee2e2", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: 6, cursor: "pointer", padding: 0, flexShrink: 0 } as React.CSSProperties,

  downloadingBadge: { padding: "6px 10px", fontSize: 12, fontWeight: 500, background: "#fef3c7", color: "#92400e", borderRadius: 6 } as React.CSSProperties,
  downloadBtn: { padding: "6px 14px", fontSize: 13, fontWeight: 500, background: "#3b82f6", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" } as React.CSSProperties,
  progressBar: { height: 4, background: "#e5e5e5", borderRadius: 2, marginTop: 10, overflow: "hidden" } as React.CSSProperties,
  progressFill: { height: "100%", background: "linear-gradient(90deg, #3b82f6, #60a5fa)", transition: "width 0.2s" } as React.CSSProperties,

  confirmRow: { display: "flex", alignItems: "center", gap: 4 } as React.CSSProperties,
  confirmText: { fontSize: 12, fontWeight: 500, color: "#dc2626", whiteSpace: "nowrap" as const } as React.CSSProperties,
  confirmYesBtn: { padding: "3px 8px", fontSize: 12, fontWeight: 600, background: "#dc2626", color: "#fff", border: "none", borderRadius: 5, cursor: "pointer" } as React.CSSProperties,
  confirmNoBtn: { padding: "3px 8px", fontSize: 12, fontWeight: 500, background: "#f3f4f6", color: "#374151", border: "1px solid #d1d5db", borderRadius: 5, cursor: "pointer" } as React.CSSProperties,

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

  installedGroupLarge: { display: "flex", flexDirection: "column" as const, alignItems: "flex-end", gap: 6, flexShrink: 0 } as React.CSSProperties,
  installedBadgeLarge: { display: "flex", alignItems: "center", gap: 6, padding: "8px 14px", fontSize: 13, fontWeight: 500, background: "#dcfce7", color: "#166534", borderRadius: 8, whiteSpace: "nowrap" as const } as React.CSSProperties,
  uninstallBtnLarge: { display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", fontSize: 13, fontWeight: 600, background: "#fee2e2", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: 8, cursor: "pointer", whiteSpace: "nowrap" as const } as React.CSSProperties,
  bundledNote: { display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", fontSize: 12, fontWeight: 500, background: "#f8fafc", color: "#64748b", border: "1px solid #e2e8f0", borderRadius: 8, whiteSpace: "nowrap" as const, cursor: "default" } as React.CSSProperties,

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

  retryBtn: { padding: "6px 10px", fontSize: 13, fontWeight: 600, background: "#fee2e2", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: 6, cursor: "pointer" } as React.CSSProperties,
  retryBtnLarge: { padding: "10px 20px", fontSize: 14, fontWeight: 600, background: "#fee2e2", color: "#dc2626", border: "1px solid #fca5a5", borderRadius: 8, cursor: "pointer", whiteSpace: "nowrap" as const } as React.CSSProperties,

  hfFilterRow: { display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" as const } as React.CSSProperties,
  hfFilterLabel: { fontSize: 13, fontWeight: 500, color: "#6e6e73", flexShrink: 0 } as React.CSSProperties,
  hfFilterChips: { display: "flex", flexWrap: "wrap" as const, gap: 6 } as React.CSSProperties,
  hfFilterChip: (active: boolean) => ({ padding: "4px 12px", fontSize: 12, fontWeight: 600, border: active ? "1.5px solid #3b82f6" : "1.5px solid #e5e5e5", borderRadius: 20, background: active ? "#eff6ff" : "#fff", color: active ? "#1d4ed8" : "#6e6e73", cursor: "pointer", transition: "all 0.15s" }) as React.CSSProperties,

  techNote: { padding: 12, background: "#f1f5f9", borderRadius: 8, fontSize: 12, color: "#475569" } as React.CSSProperties,
  notAvailableNote: { padding: "12px 16px", background: "#fef3c7", border: "1px solid #fbbf24", borderRadius: 8, fontSize: 13, color: "#92400e", marginBottom: 16 } as React.CSSProperties,
  privacyNote: { display: "flex", alignItems: "center", gap: 12, padding: 16, background: "#ecfdf5", borderRadius: 12, fontSize: 14, color: "#065f46" } as React.CSSProperties,
};

export default ModelManager;
