"""
Real-world test documents for legal-anonymizer testing.

This module contains realistic legal documents with various PII types
for comprehensive testing of anonymization capabilities.
"""

# Legal contracts with multiple PII types
SAMPLE_SERVICE_AGREEMENT = """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of January 15, 2024
(the "Effective Date") by and between:

CLIENT:
Name: John Robert Smith
Email: john.r.smith@example.com
Phone: (555) 123-4567
Address: 123 Main Street, New York, NY 10001
SSN: 123-45-6789

SERVICE PROVIDER:
Company: ABC Legal Services LLC
Email: contact@abclegal.com
Phone: +1 (555) 987-6543
Tax ID: 12-3456789

SCOPE OF SERVICES:
The Provider shall provide legal consultation services as requested by Client.

FEES AND PAYMENT:
Monthly Fee: $5,000 USD
Payment Method: Bank Transfer to DE89370400440532013000
Credit Card Payment: 4111111111111111 (Visa)

CONFIDENTIALITY:
Both parties agree to maintain confidentiality of all information exchanged.

TERM AND TERMINATION:
This Agreement shall commence on the Effective Date and continue for one (1) year.

Signed:
_________________________  _________________________
Client                     Service Provider
John Robert Smith         Jane Margaret Johnson
"""

# Settlement agreement with financial details
SAMPLE_SETTLEMENT_AGREEMENT = """
CONFIDENTIAL SETTLEMENT AGREEMENT

This Settlement Agreement ("Agreement") is made this 20th day of February, 2024,
between:

CLAIMANT:
Name: Mary Elizabeth Johnson
DOB: 06/15/1975
SSN: 987-65-4321
Email: mary.johnson@example.com
Phone: +1 (555) 234-5678
Address: 456 Oak Avenue, Los Angeles, CA 90001

RESPONDENT:
Company: XYZ Manufacturing Inc.
Address: 789 Industrial Blvd, Los Angeles, CA 90002
Contact: contact@xyzmfg.com
Phone: (555) 876-5432
EIN: 98-7654321

SETTLEMENT TERMS:

1. Payment Amount: $250,000 USD
   Payment Method: Wire Transfer
   Bank: Bank of America
   Account: 123456789012
   Routing: 011000015

2. Medical Expenses: $50,000 USD
   Bill to: mary.johnson@example.com

3. Confidential Payment:
   Credit Card: 5555555555554444
   IBAN: GB82WEST12345698765432

REPRESENTATIVE INFORMATION:
Claimant's Attorney:
Name: Robert Charles Williams
License: CA123456
Email: rwilliams@lawfirm.com
Phone: (555) 345-6789

Respondent's Counsel:
Name: Patricia Anne Davis
License: CA654321
Email: pdavis@corplaw.com
Phone: (555) 567-8901
"""

# Medical record with sensitive health information
SAMPLE_MEDICAL_RECORD = """
CONFIDENTIAL MEDICAL RECORD

Patient Information:
Name: James Michael Anderson
DOB: 03/22/1965
Patient ID: MED-2024-001234
SSN: 456-78-9012
Gender: Male

Contact Information:
Primary Phone: (555) 456-7890
Mobile: +1 (555) 567-8901
Email: james.anderson@example.com
Address: 321 Pine Road, Chicago, IL 60601

Insurance Information:
Provider: United Healthcare
Policy Number: 123-45-6789
Group Number: ABC123
Subscriber: james.anderson@example.com

Emergency Contact:
Name: Susan Mary Anderson
Relationship: Spouse
Phone: (555) 678-9012
Email: susan.anderson@example.com

Medical History:
Date: January 15, 2024
Provider: Dr. John Smith, MD
License: IL654321
Contact: dr.smith@medicalcenter.com

Prescriptions:
Card: 4532015112830366
Pharmacy: (555) 789-0123
"""

# Invoice with business details
SAMPLE_INVOICE = """
INVOICE

Invoice #2024-001-ABC
Date: January 10, 2024
Due Date: February 10, 2024

FROM:
Company: ABC Consulting LLC
Owner: David John Thompson
Email: david@abcconsulting.com
Phone: (555) 111-2222
Tax ID: 34-5678901
IBAN: IT60X0542811101000000123456

TO:
Client Name: Sarah Elizabeth Brown
Company: Brown & Associates Inc.
Email: sarah.brown@brownassoc.com
Phone: (555) 222-3333
Address: 111 Business Park, Boston, MA 02101
Tax ID: 45-6789012

SERVICES:
- Consulting services (40 hours @ $250/hr): $10,000
- Project management fee: $2,000
- Travel expenses: $1,500
- Total: $13,500

PAYMENT TERMS:
Net 30 days
Payment Method: Wire Transfer to DE89370400440532013000
Or Credit Card: 378282246310005
Contact: david@abcconsulting.com
Phone: (555) 111-2222
"""

# Employment contract with salary information
SAMPLE_EMPLOYMENT_CONTRACT = """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is made this 1st day of March, 2024
between:

EMPLOYER:
Company: Tech Solutions Inc.
Address: 999 Silicon Valley Drive, San Jose, CA 95110
HR Contact: Emily Rachel Green
Email: egreen@techsol.com
Phone: (555) 333-4444
EIN: 56-7890123

EMPLOYEE:
Name: Christopher Michael Taylor
DOB: 09/12/1988
SSN: 789-01-2345
Email: ctaylor@techsol.com
Phone: +1 (555) 444-5555
Address: 222 Elm Street, San Jose, CA 95110

POSITION: Senior Software Engineer

COMPENSATION:
- Annual Salary: $150,000
- Performance Bonus: Up to 25%
- Benefits Enrollment Date: March 15, 2024

DIRECT DEPOSIT:
Bank: Chase Bank
Account Number: 987654321098
Routing Number: 021000021
IBAN: US12CHASUS987654321098

EMERGENCY CONTACT:
Name: Lisa Anne Taylor
Relationship: Spouse
Phone: (555) 555-6666
Email: lisa.taylor@example.com

CONFIDENTIALITY:
Employee agrees to maintain confidentiality of all proprietary information.

SIGNATURE:

___________________________      ___________________________
Employee                         HR Director
Christopher Michael Taylor       Emily Rachel Green
Date: 3/1/2024                   Date: 3/1/2024
"""

# Multilingual document
SAMPLE_MULTILINGUAL_DOCUMENT = """
INTERNATIONAL AGREEMENT / ACUERDO INTERNACIONAL / ACCORD INTERNATIONAL

ENGLISH SECTION:
Client: John Patrick Miller
Email: john.miller@example.com
Phone: +1 (555) 666-7777
SSN: 321-54-9876

SPANISH SECTION (SECCIÓN EN ESPAÑOL):
Cliente: Juan García López
Email: juan.garcia@example.es
Teléfono: +34 91 123 4567
DNI: 12345678A

FRENCH SECTION (SECTION FRANÇAISE):
Client: Pierre Martin Dubois
Email: pierre.dubois@example.fr
Téléphone: +33 1 42 34 56 78
INSEE: 1 70 12 75 123 456 78

GERMAN SECTION (DEUTSCHER ABSCHNITT):
Klient: Hans Mueller Schmidt
Email: hans.mueller@example.de
Telefon: +49 30 12345678
Steuer-ID: 98765432109

DUTCH SECTION (NEDERLANDSE SECTIE):
Cliënt: Jan Janssen van Amsterdam
Email: jan.janssen@example.nl
Telefoon: +31 6 12345678
BSN: 123456789
"""

# Data containing common false positive patterns
SAMPLE_FALSE_POSITIVES = """
SOFTWARE RELEASE NOTES

Version: 2.3.4.5
Build: 5.6.7.8
API Version: 10.20.30.40
Protocol: 192.168.1.1:8080

CHANGELOG:
Date: 01-23-45 - Initial Release
Date: 12-31-99 - Y2K Fix
Date: 03-15-2024 - Current Version

MATHEMATICAL CALCULATIONS:
Result: 123 456.78 EUR
Formula: 98 76 54 - 32 10 = 98 43 44
Calculation: 11 22 33 44 55 (not a phone)

CODE REFERENCES:
Hash: ABC-123-DEF-456
Reference: XYZ-789-UVW-012
Code: 123-456-7890

IP ADDRESSES:
Server 1: 192.168.1.1
Server 2: 10.0.0.1
Server 3: 172.16.0.1

TIME STAMPS:
Event logged at 10:30:45
Time: 23:59:59
Duration: 01:23:45
"""

# High-priority PII test data
SAMPLE_HIGH_PRIORITY_PII = """
CRITICAL CONFIDENTIAL DOCUMENT

United States:
- SSN: 123-45-6789
- EIN: 98-7654321
- Credit Card: 4111111111111111
- Passport: A12345678

United Kingdom:
- NI Number: AB123456C
- Sort Code: 20-00-00
- Account: 12345678

European Union:
- Germany Tax ID: 12345678901
- France INSEE: 1 70 12 75 123 456 78
- Spain DNI: 12345678A
- Spain NIE: X1234567L
- Belgium Number: 85.07.15-033.45
- Italy Codice: RSSMRA85M05F205F
- Netherlands BSN: 123456789

Asia:
- China ID: 110101199003077515
- Japan My Number: 1234 5678 9012
- Korea RRN: 900101-1234567
- India PAN: AAAAA1234A
- Singapore NRIC: S1234567A

Middle East & Africa:
- UAE Emirates ID: 784-1234-5678901-5
- Saudi Arabia ID: 0000000000
- South Africa ID: 8001015009087

International:
- IBAN: DE89370400440532013000
- SWIFT: DEUTDEDD500
- Passport: A12345678
"""

# Dictionary of all sample documents
SAMPLE_DOCUMENTS = {
    "service_agreement": SAMPLE_SERVICE_AGREEMENT,
    "settlement_agreement": SAMPLE_SETTLEMENT_AGREEMENT,
    "medical_record": SAMPLE_MEDICAL_RECORD,
    "invoice": SAMPLE_INVOICE,
    "employment_contract": SAMPLE_EMPLOYMENT_CONTRACT,
    "multilingual": SAMPLE_MULTILINGUAL_DOCUMENT,
    "false_positives": SAMPLE_FALSE_POSITIVES,
    "high_priority_pii": SAMPLE_HIGH_PRIORITY_PII,
}

__all__ = [
    "SAMPLE_SERVICE_AGREEMENT",
    "SAMPLE_SETTLEMENT_AGREEMENT",
    "SAMPLE_MEDICAL_RECORD",
    "SAMPLE_INVOICE",
    "SAMPLE_EMPLOYMENT_CONTRACT",
    "SAMPLE_MULTILINGUAL_DOCUMENT",
    "SAMPLE_FALSE_POSITIVES",
    "SAMPLE_HIGH_PRIORITY_PII",
    "SAMPLE_DOCUMENTS",
]
