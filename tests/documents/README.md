# Test Documents

Synthetic test documents for validating PII detection and anonymization.

**All data in these files is entirely fabricated.** Names, addresses, ID numbers, financial details, and all other personal information are fictional and generated solely to exercise the anonymizer engine.

## Files

| File | Purpose | PII Categories |
|------|---------|----------------|
| `sample_en_legal_brief.txt` | US civil litigation brief | SSN, credit card, IBAN, phone, email, passport, address, DOB, vehicle, IP |
| `sample_eu_compliance_report.txt` | EU GDPR data audit | EU national IDs, IBANs, EU phones, EU addresses, passports, emails |
| `sample_medical_legal_report.txt` | UK medical malpractice case | NHS numbers, medical IDs, dates, names, addresses, phone numbers |

## How to Use

```bash
cd engine/python

# Analyze a single file (Layer 1 — fast)
echo '{
  "input_path": "../../tests/documents/sample_en_legal_brief.txt",
  "preset": {
    "preset_id": "layer1", "name": "Fast", "layer": 1,
    "minimum_confidence": 60, "uncertainty_policy": "mask",
    "pseudonym_style": "neutral", "language_mode": "auto",
    "entities_enabled": {}
  }
}' | python scripts/sidecar_entrypoint.py analyze_file

# Analyze text inline
echo '{
  "text": "John Smith, SSN 234-56-7890, can be reached at john.smith@acme.com",
  "preset": {
    "preset_id": "layer1", "name": "Fast", "layer": 1,
    "minimum_confidence": 60, "uncertainty_policy": "mask",
    "pseudonym_style": "neutral", "language_mode": "auto",
    "entities_enabled": {}
  }
}' | python scripts/sidecar_entrypoint.py analyze_text
```

## Expected Coverage

The documents collectively exercise:

- `PERSON` — first/last names, full names with middle names
- `EMAIL` — business, personal, and institutional addresses
- `PHONE_NUMBER` — US, UK, German, French, and international formats
- `NATIONAL_ID` — US SSN, UK NI, German Steuer-ID, French NIR, Dutch BSN
- `PASSPORT_NUMBER` — US, UK, German, Dutch passports
- `CREDIT_CARD` — Visa, Mastercard (Luhn-valid numbers)
- `BANK_ACCOUNT` — IBAN (DE, FR, NL, GB), US routing/account
- `IP_ADDRESS` — IPv4 and IPv6
- `DATE_OF_BIRTH` — multiple date formats
- `ADDRESS` — US, UK, German, French street addresses
- `VEHICLE_ID` — US and EU license plates
- `MEDICAL_ID` — NHS numbers, US MRN, NPI
- `ACCOUNT_USERNAME` — @handles and login names
- `ORGANIZATION` — company names, law firms, hospitals
- `MONEY` — USD, EUR, GBP amounts
- `TAX_ID` — US EIN, UK UTR, German Steuernummer
