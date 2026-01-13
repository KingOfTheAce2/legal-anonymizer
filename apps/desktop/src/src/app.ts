import React, { useMemo, useState } from "react";
import { analyzeText, Preset } from "./api";

const defaultPreset: Preset = {
  preset_id: "layer1_fast_legal_scrub",
  name: "Fast Legal Scrub (Layer 1)",
  layer: 1,
  minimum_confidence: 60,
  uncertainty_policy: "mask",
  pseudonym_style: "neutral",
  language_mode: "auto",
  entities_enabled: {
    NATIONAL_ID: true,
    PASSPORT_NUMBER: true,
    MEDICAL_ID: true,
    BANK_ACCOUNT: true,
    CREDIT_CARD: true,
    PERSON: true,
    DATE_OF_BIRTH: true,
    EMAIL: true,
    PHONE_NUMBER: true,
    VEHICLE_ID: true,
    ADDRESS: true,
    IP_ADDRESS: true,
    ORGANIZATION: true,
    LOCATION: true,
    ACCOUNT_USERNAME: true,
    DATE: true
  }
};

export function App() {
  const [text, setText] = useState(
    "Client John Smith (john.smith@example.com) has IBAN NL91ABNA0417164300 and phone +31 6 12345678."
  );
  const [result, setResult] = useState<string>("");
  const [runInfo, setRunInfo] = useState<string>("");

  const preset = useMemo(() => defaultPreset, []);

  async function onRun() {
    setRunInfo("Running...");
    setResult("");
    try {
      const resp = await analyzeText(text, preset);
      setResult(resp.redacted_text);
      setRunInfo(`Run ${resp.run_id}. Artifacts in: ${resp.run_folder}`);
    } catch (e: any) {
      setRunInfo(`Error: ${e?.toString?.() ?? "unknown"}`);
    }
  }

  return (
    <div style={{ padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <h2>Legal Anonymizer (Layer 1 Text)</h2>

      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <h3>Input</h3>
          <textarea
            style={{ width: "100%", height: 180 }}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div style={{ marginTop: 8 }}>
            <button onClick={onRun}>Anonymize</button>
          </div>
          <div style={{ marginTop: 8, fontSize: 12 }}>{runInfo}</div>
        </div>

        <div style={{ flex: 1 }}>
          <h3>Redacted output</h3>
          <textarea style={{ width: "100%", height: 180 }} readOnly value={result} />
        </div>
      </div>
    </div>
  );
}
