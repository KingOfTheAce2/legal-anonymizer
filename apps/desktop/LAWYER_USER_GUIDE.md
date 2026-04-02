# Legal Anonymizer - User Guide for Legal Professionals

**Version:** 1.0.0
**Last Updated:** February 2026

---

## 🎯 What is Legal Anonymizer?

Legal Anonymizer is a **privacy-first desktop application** that automatically detects and redacts personally identifiable information (PII) from legal documents.

**Key Features:**
- ✅ **Offline-First:** No internet required, complete privacy
- ✅ **GDPR Compliant:** Meets Article 5 transparency requirements
- ✅ **Multi-Format:** Supports .docx, .pdf, and .txt files
- ✅ **50+ Countries:** Global PII pattern support
- ✅ **Audit Trail:** Complete findings report for compliance

---

## 🚀 Installation

### Windows Installation

1. **Download** `Legal-Anonymizer-Setup.msi` from your IT department or firm portal
2. **Double-click** the installer file
3. **Click "Next"** through the installation wizard
4. **Launch** the app from your Desktop or Start Menu

### macOS Installation

1. **Download** `Legal-Anonymizer.dmg`
2. **Double-click** to open the disk image
3. **Drag** the "Legal Anonymizer" icon to your Applications folder
4. **Launch** from Applications or Spotlight search

### First Launch

On macOS, you may see a security warning:
1. Go to **System Settings → Privacy & Security**
2. Click **"Open Anyway"** next to the Legal Anonymizer message
3. Confirm by clicking **"Open"**

*Note: This only happens the first time. The app is safe and does not require internet access.*

---

## 📋 Quick Start (3 Steps)

### Step 1: Add Documents

**Three ways to add files:**

1. **Drag & Drop:** Drag files directly into the app window
2. **Browse:** Click "Add Files" button → Select documents
3. **Folder:** Click "Add Folder" to process multiple files at once

**Supported formats:**
- Microsoft Word (.docx)
- PDF Documents (.pdf)
- Plain Text (.txt)

### Step 2: Choose Anonymization Level

**Three detection layers:**

| Layer | Speed | Accuracy | Best For |
|-------|-------|----------|----------|
| **Layer 1: Fast Legal Scrub** | ⚡ Fastest | Good | Large batches, first review |
| **Layer 2: Accurate Legal Review** | 🎯 Moderate | Excellent | Most legal work (recommended) |
| **Layer 3: Regulatory Standard** | 🛡️ Conservative | Strictest | Regulatory filings, compliance |

**Recommendation:** Start with **Layer 2** for most legal work.

### Step 3: Anonymize & Review

1. Click **"Anonymize Documents"** button
2. Wait for processing (progress bar shown)
3. **Review findings report** (opens automatically)
4. **Save anonymized files** to desired location

---

## 📊 Understanding the Results

### Findings Report (findings.csv)

Each detection includes:

| Column | Description | Example |
|--------|-------------|---------|
| **Entity Type** | Type of PII detected | PERSON, EMAIL, SSN |
| **Detected Text** | Original text found | "John Smith" |
| **Context** | Surrounding text | "...represents John Smith in..." |
| **Confidence** | Detection certainty (%) | 95 |
| **Action Taken** | What was done | Redacted, Pseudonymised |
| **Page/Location** | Where it was found | Page 3, Line 45 |

### Entity Types Detected

**Always Redacted (Priority 90-100):**
- Social Security Numbers (SSN)
- Passport Numbers
- National ID Numbers
- Bank Account Numbers
- Credit Card Numbers
- Medical IDs

**Usually Pseudonymised (Priority 80):**
- Person Names
- Dates of Birth
- Email Addresses
- Phone Numbers

**Configurable (Priority 60-70):**
- Addresses
- Organizations
- IP Addresses
- Account Usernames

**Optional (Priority 40):**
- Dates
- Locations
- URLs

---

## 🎨 Redaction Methods

### 1. Redact (Irreversible)
```
Before: John Smith lives at 123 Main Street
After:  ████████████ lives at ██████████████████
```
**Use when:** Complete removal required (regulatory filings)

### 2. Pseudonymise (Consistent)
```
Before: John Smith... later, John Smith appeared...
After:  PERSON_001... later, PERSON_001 appeared...
```
**Use when:** Document readability matters (internal review)

### 3. Mask (Partial)
```
Before: john.smith@lawfirm.com
After:  jo**********om
```
**Use when:** Format verification needed

---

## ⚙️ Advanced Settings

### Entity Selection

**Customize which entities to detect:**

1. Click **"Settings"** → **"Entity Configuration"**
2. **Toggle ON/OFF** specific entity types:
   - ☑ Person Names
   - ☑ Email Addresses
   - ☑ Phone Numbers
   - ☐ Dates (optional)
   - ☐ Organizations (optional)

**Tip:** Disable "Dates" if your documents have many date references that don't need redaction.

### Confidence Threshold

**Adjust detection sensitivity:**
- **60% (Default):** Balanced - catches most PII
- **80% (High):** Strict - only high-confidence detections
- **40% (Low):** Aggressive - flags more potential PII

**Lower threshold = More detections, more false positives**

### Uncertainty Policy

**What to do with low-confidence detections:**
- **Mask:** Partially hide (recommended)
- **Redact:** Fully redact (conservative)
- **Flag Only:** Log but don't modify
- **Leave Intact:** Don't modify

---

## 📁 Batch Processing

### Process Multiple Files

1. Click **"Add Folder"**
2. Select folder containing documents
3. All compatible files will be added
4. Click **"Anonymize All"**

**Progress tracking:**
- Real-time progress bar
- Current file being processed
- Estimated time remaining

**Output structure:**
```
RUN_20260214_143000/
├── preset_used.json        # Settings used
├── findings.csv            # All detections
├── run_report.json         # Summary
└── output/                 # Anonymized files
    ├── document1_redacted.docx
    ├── document2_redacted.pdf
    └── ...
```

---

## 🔒 Privacy & Security

### Data Protection

✅ **Completely Offline:** No internet connection required
✅ **No Cloud:** All processing happens on your computer
✅ **No Telemetry:** We don't collect any usage data
✅ **Local Storage:** Files never leave your machine
✅ **Secure Deletion:** Original files untouched

### GDPR Compliance

Legal Anonymizer helps you comply with:

- **Article 5:** Lawfulness, fairness, transparency
- **Article 25:** Data protection by design
- **Article 32:** Security of processing

**Audit trail:** Every run produces findings.csv for accountability

---

## 🆘 Troubleshooting

### App Won't Open

**Windows:**
1. Right-click → "Run as Administrator"
2. Check Windows Defender didn't block it
3. Add exception in antivirus software

**macOS:**
1. System Settings → Privacy & Security
2. Click "Open Anyway"
3. Or: Right-click app → "Open"

### Files Not Processing

**Check file format:**
- Must be .docx, .pdf, or .txt
- Scanned PDFs require OCR (optional feature)
- Corrupted files will be skipped

**Check file size:**
- Very large files (>100MB) may take time
- Progress bar shows current status

### Unexpected Results

**Too many detections:**
- Use Layer 1 (Fast) for fewer detections
- Increase confidence threshold to 80%
- Disable optional entities (dates, organizations)

**Missing detections:**
- Use Layer 3 (Regulatory) for maximum coverage
- Lower confidence threshold to 40%
- Check findings.csv for flagged items

---

## 💡 Tips for Legal Professionals

### Best Practices

1. **Always review findings.csv** before finalizing
2. **Use Layer 2** for most work (balanced)
3. **Test on sample** before batch processing
4. **Keep run folders** for audit trail
5. **Version control** original files

### Common Use Cases

**Client Disclosure (GDPR DSAR):**
- Use Layer 3 (strictest)
- Enable all entity types
- Full redaction method
- Provide findings report

**Internal Document Review:**
- Use Layer 2 (balanced)
- Pseudonymisation method
- Keep document readable
- Fast review process

**Regulatory Filing:**
- Use Layer 3 (conservative)
- Low confidence threshold (40%)
- Full redaction
- Complete audit trail

**Court Filings:**
- Layer 2 or 3
- Review findings manually
- Preserve case citations
- Redact only PII

---

## 📞 Support

### Getting Help

**Email Support:** support@yourfirm.com
**Documentation:** https://docs.yourfirm.com/legal-anonymizer
**Updates:** Check Help → About for version

### Reporting Issues

Include in your report:
1. Version number (Help → About)
2. Operating system (Windows/macOS/Linux)
3. Error message (screenshot)
4. Steps to reproduce
5. Sample file (if possible, anonymized)

---

## 📝 Keyboard Shortcuts

| Action | Windows | macOS |
|--------|---------|-------|
| Add Files | Ctrl+O | Cmd+O |
| Anonymize | Ctrl+Enter | Cmd+Enter |
| Settings | Ctrl+, | Cmd+, |
| Help | F1 | Cmd+? |
| Quit | Alt+F4 | Cmd+Q |

---

## 🎓 Training Resources

**Video Tutorials:**
1. Quick Start (5 min)
2. Batch Processing (10 min)
3. Advanced Settings (15 min)

**Sample Documents:**
- test_agreement.docx (practice file)
- sample_findings.csv (example output)

**Webinars:**
- Monthly Q&A sessions
- New feature announcements

---

## ✅ Quick Reference Card

```
┌─────────────────────────────────────────┐
│ LEGAL ANONYMIZER - QUICK REFERENCE      │
├─────────────────────────────────────────┤
│ 1. Add Files (Drag & Drop or Browse)    │
│ 2. Choose Layer (2 = Recommended)       │
│ 3. Click "Anonymize Documents"          │
│ 4. Review findings.csv                  │
│ 5. Save anonymized files                │
├─────────────────────────────────────────┤
│ ENTITY PRIORITIES:                      │
│ • SSN/ID: Always redacted (Priority 100)│
│ • Names: Pseudonymised (Priority 80)    │
│ • Dates: Optional (Priority 40)         │
├─────────────────────────────────────────┤
│ SUPPORT: support@yourfirm.com           │
│ DOCS: docs.yourfirm.com                 │
└─────────────────────────────────────────┘
```

Print this card and keep it at your desk!

---

**© 2026 Your Law Firm | Version 1.0.0 | MIT License**
