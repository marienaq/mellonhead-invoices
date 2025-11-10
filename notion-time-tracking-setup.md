# Notion Time Tracking Table Enhancement Guide
*Task M1.2 - Database Foundation Setup*

## Overview
This guide verifies your existing Time Tracking table and adds the required fields for automated invoice calculations.

## Required Fields (Verify/Add)

### Existing Fields (Should Already Exist)
✅ **Date** (Date property)
✅ **Client** (Relation to Clients table)  
✅ **Hours Worked** (Number property)
✅ **Notes/Description** (Text property - optional)

### New Fields to Add

#### 1. Month Formula Field
- **Property Type:** Formula
- **Property Name:** `Month`
- **Formula:** `formatDate(prop("Date"), "YYYY-MM")`
- **Purpose:** Groups time entries by billing period (e.g., "2025-09", "2025-10")

#### 2. Client Retainer Hours (Rollup)
- **Property Type:** Rollup
- **Property Name:** `Client Retainer Hours`
- **Relation:** Client (your existing relation field)
- **Property:** Monthly Retainer Hours
- **Calculate:** Show original
- **Purpose:** Shows the monthly hour allocation for quick reference

#### 3. Daily Amount (Formula) - Optional Enhancement
- **Property Type:** Formula  
- **Property Name:** `Daily Amount`
- **Formula:** `prop("Hours Worked") * prop("Client").prop("Overage Rate")`
- **Purpose:** Quick calculation of daily billing amount for reference

## Step-by-Step Setup Instructions

### Step 1: Verify Existing Fields

1. **Open your Time Tracking table in Notion**
2. **Confirm these fields exist:**
   - Date (Date)
   - Client (Relation to Clients table)
   - Hours Worked (Number)
   - Notes/Description (Text)

### Step 2: Add Month Formula Field

1. **Add Month field:**
   - Click the "+" button to add a property
   - Select "Formula" property type
   - Name: `Month`
   - Formula: `formatDate(prop("Date"), "YYYY-MM")`
   - Click "Create"

### Step 3: Add Client Retainer Hours Rollup

1. **Add Client Retainer Hours rollup:**
   - Click the "+" button to add a property
   - Select "Rollup" property type
   - Name: `Client Retainer Hours`
   - Relation: Select your "Client" relation field
   - Property: Select "Monthly Retainer Hours"
   - Calculate: "Show original"
   - Click "Create"

### Step 4: Add Daily Amount Formula (Optional)

1. **Add Daily Amount field:**
   - Click the "+" button to add a property
   - Select "Formula" property type
   - Name: `Daily Amount`
   - Formula: `prop("Hours Worked") * prop("Client").prop("Overage Rate")`
   - Click "Create"

## Formula Explanations

### Month Formula
```
formatDate(prop("Date"), "YYYY-MM")
```
- Converts any date to "YYYY-MM" format (e.g., "2025-10")
- Essential for grouping time entries by billing period
- Used in M1.3 for monthly calculations

### Daily Amount Formula
```
prop("Hours Worked") * prop("Client").prop("Overage Rate")
```
- Calculates daily billing amount using overage rate
- Provides quick reference for daily value
- Note: This is just for reference; actual billing logic handles retainer vs overage

## Sample Data After Enhancement

Your time entries should now look like this:

| Date | Client | Hours | Notes | Month | Client Retainer Hours | Daily Amount |
|------|---------|-------|-------|-------|---------------------|--------------|
| 2025-10-01 | Acme Corp | 8 | Strategy meeting | 2025-10 | 80 | $1,200 |
| 2025-10-02 | Beta LLC | 4 | Code review | 2025-10 | 40 | $800 |

## Validation Checklist

After setup, verify:
- [ ] Month field shows "YYYY-MM" format for all entries
- [ ] Client Retainer Hours shows correct values from Clients table
- [ ] Daily Amount calculates correctly (Hours × Overage Rate)
- [ ] All existing time entries are preserved
- [ ] New time entries auto-populate Month field

## Next Steps

Once this setup is complete:
1. Test adding a new time entry to verify formulas work
2. Check that Month field auto-calculates
3. Proceed to M1.3: Create Monthly Invoice Prep view

## Notes

- The Month field is critical for the invoice prep calculations in M1.3
- Client Retainer Hours rollup provides context while logging time
- Daily Amount is for reference only; invoice logic handles retainer vs overage properly
- All formulas are read-only and auto-calculate

---

**Status:** Ready for implementation  
**Time Required:** 10-15 minutes  
**Dependencies:** M1.1 (Clients table) must be completed first