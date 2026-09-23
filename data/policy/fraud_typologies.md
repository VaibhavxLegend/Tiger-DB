# Fraud Typology Descriptions

These are the five documented fraud patterns the bank's analysts recognize. Source: data/raw/README.md

## 1. Card Testing

**Description**: A stolen card number is checked before use: three or more tiny online authorizations, often under $5, then a larger purchase.

**Indicators**:
- Multiple small authorizations (< $5) in quick succession (< 1 hour)
- Followed by a larger purchase
- Often online transactions
- New device profile for the account

**Confirmation**: The sequence itself confirms the pattern

**Policy Reference**: R5

---

## 2. Card-Not-Present Fraud

**Description**: The number is used online without the card. Amounts and products that don't fit the cardholder's history, often in a burst of two to four within 48 hours.

**Indicators**:
- Online transactions
- Products/amounts inconsistent with history
- Burst of 2-4 transactions within 48 hours
- May not be at new device

**Ambiguity**: On its own, one unusual online purchase is ambiguous - verify

**Policy Reference**: R1-R4

---

## 3. Card-Not-Present Fraud from New Device

**Description**: Same as pattern 2, but with the identity record marking the device as "New" for this account, sometimes behind a proxy.

**Indicators**:
- All indicators from pattern 2
- Plus: Device marked as "New" in identity record
- May show proxy usage (transparent, anonymous, hidden)

**Strength**: Stronger than pattern 2, but still not proof (people buy new phones)

**Policy Reference**: R1-R4

---

## 4. Out-of-Region Use

**Description**: Card-present purchases in a billing region the cardholder has no history in, while their normal activity continues at home.

**Indicators**:
- Card-present transactions (ProductCD = 'W')
- In billing region (addr1) with no prior history
- Normal activity continues in home region (suggests cloned card)

**Important**: Several days of purchases in one new region is a trip, not fraud

**Policy Reference**: R2, R3

---

## 5. Account Takeover

**Description**: Mixed-channel activity inconsistent with the cardholder, often with device and match-flag anomalies, pointing to stolen credentials rather than a stolen number.

**Indicators**:
- Mixed in-person and online activity
- Inconsistent with cardholder patterns
- Device anomalies (new devices, proxy usage)
- Match flag anomalies (M1-M9 showing mismatches)
- Suggests credential compromise, not just card number theft

**Policy Reference**: R2, R6

---

## Undocumented Patterns

**Important**: These five patterns are NOT the only fraud in the data. Activity that fits none of them but shows coordinated or repeated abuse should be:
- Described in your own words in `pattern_description`
- Recommended for `CREATE_CASE` + `FILE_REPORT` + `ESCALATE_TO_ANALYST`
- Never forced into a known category

**Policy Reference**: R9

---

## Pattern Matching Guidelines

1. **Match against evidence, not assumptions**: Base pattern identification on actual graph evidence
2. **Cite specific signals**: Which transactions, devices, regions, match flags support the pattern
3. **Note ambiguity**: If evidence is weak or conflicting, mark as "uncertain" not "fraud"
4. **Prior cases matter**: Similar patterns in closed_cases_history.csv strengthen the match
5. **Novel patterns count**: Noticing undocumented patterns is scored positively
