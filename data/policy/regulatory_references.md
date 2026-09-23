# Regulatory References for Fraud Investigation

Source: data/raw/README.md - Public documents from US and international regulators

## FinCEN (US Treasury Financial Crimes Enforcement Network)

### SAR Filing Requirements

**Key Resources**:
- SAR Filing FAQs (October 2025)
- SAR Narrative Guidance - Standard for writing `sar.narrative`
- Preparing a Complete and Sufficient SAR Narrative
- SAR Supporting Documentation (FIN-2007-G003)

**Filing Thresholds**:
- Confirmed or strongly suspected fraud
- Exposure exceeds $1,000, OR
- Shared device/region links multiple victims, OR
- Coordinated/undocumented pattern

**Narrative Requirements** (Who, What, When, Where, How, Why):
- **Who**: Customer IDs, card IDs, merchants, devices involved
- **What**: Specific transactions and amounts
- **When**: Activity dates (first to last)
- **Where**: Locations, channels (in-person vs online), billing regions
- **How**: Pattern/method used (e.g., card testing, device sharing)
- **Why suspicious**: What makes this fraudulent vs legitimate

### Red Flags

**SAR Activity Review - Trends, Tips, and Issues**:
- Multiple small authorizations (testing)
- Burst activity inconsistent with history
- Shared device profiles across unrelated accounts
- New devices with proxy usage
- Out-of-region activity while home activity continues

### Account Takeover

**Advisory on Account Takeover Activity (FIN-2011-A016)**:
- Credential compromise indicators
- Mixed-channel anomalies
- Device and match-flag mismatches

### Identity-Related Fraud

**Identity-Related Suspicious Activity (2021)**:
- Device fingerprinting
- Email domain patterns
- Identity record anomalies

---

## FATF (Financial Action Task Force)

### Cyber-Enabled Fraud

**Illicit Financial Flows from Cyber-Enabled Fraud**:
- Card-not-present patterns
- Device-based fraud rings
- Cross-border coordination

### Money Laundering Methods

**Money Laundering Using New Payment Methods**:
- How stolen card proceeds are laundered
- Payment method risk indicators

---

## FFIEC (Federal Financial Institutions Examination Council)

### Red Flags for Suspicious Activity

**Money Laundering and Terrorist Financing Red Flags**:
- Transaction patterns inconsistent with customer profile
- Shared attributes across multiple accounts
- Velocity anomalies

**Suspicious Activity Reporting Guidelines**:
- When to file
- What to include
- Supporting documentation requirements

---

## Key Takeaways for Agent Implementation

1. **SAR Narrative Must Stand Alone**: Regulator should understand the case without context
2. **Specific Dates and Amounts Required**: Not just summaries
3. **Pattern Description Essential**: Explain how the fraud was carried out
4. **Subject Identification**: List all customers, cards, devices involved
5. **Why Suspicious**: Clear explanation of why this is fraud, not legitimate activity

---

## Policy Cross-References

- **R2**: Customer denies transaction → SAR if exposure > $1,000 or shared device
- **R6**: Shared origin (device/region) → SAR required
- **R9**: Undocumented patterns → SAR + escalate

---

## Implementation Note

Load these documents into the vector store (rag/policy_ingest.py) for retrieval during:
- SAR requirement determination (should_file_sar)
- SAR narrative generation (explain node)
- Policy compliance checks (recommend_action node)
