# Notion Monthly Invoice Prep View Setup Guide
*Task M1.3 - Database Foundation Setup*

## Overview
This guide creates a new database/view that automatically calculates monthly billing amounts by aggregating time entries and applying retainer vs overage logic.

## Approach Options

### Option A: Create New "Monthly Invoice Prep" Database (Recommended)
- Separate database that relates to Clients and Time Tracking
- Cleaner structure for automation
- Better for the n8n integration

### Option B: Add Grouped View to Existing Time Tracking
- Add calculations to existing Time Tracking table
- Simpler but potentially messier

**Recommendation: Option A for cleaner automation**

## Step-by-Step Setup (Option A)

### Step 1: Create New Database

1. **Create new database:**
   - In your Notion workspace, click "Add a page"
   - Select "Database" → "New database"
   - Name: `Monthly Invoice Prep`
   - Choose "Table" layout

### Step 2: Add Core Properties

2. **Add Client relation:**
   - Property Type: Relation
   - Name: `Client`
   - Relate to: Your Clients database
   - Click "Create"

3. **Add Billing Month:**
   - Property Type: Text
   - Name: `Billing Month`
   - Description: Format as "YYYY-MM" (e.g., "2025-10")

4. **Add Billing Type:**
   - Property Type: Select
   - Name: `Billing Type`
   - Options: "Current Retainer", "Previous Overage"
   - Description: Distinguishes retainer billing from overage billing

### Step 3: Add Rollup Fields from Client

5. **Add Monthly Retainer Hours rollup:**
   - Property Type: Rollup
   - Name: `Monthly Retainer Hours`
   - Relation: Client
   - Property: Monthly Retainer Hours
   - Calculate: Show original

6. **Add Retainer Rate rollup:**
   - Property Type: Rollup
   - Name: `Retainer Rate`
   - Relation: Client
   - Property: Retainer Rate
   - Calculate: Show original

7. **Add Overage Rate rollup:**
   - Property Type: Rollup
   - Name: `Overage Rate`
   - Relation: Client
   - Property: Overage Rate
   - Calculate: Show original

### Step 4: Add Time Tracking Calculations

8. **Add Total Hours Worked rollup:**
   - Property Type: Rollup
   - Name: `Total Hours Worked`
   - Relation: Client
   - Property: Hours Worked (from Time Tracking)
   - Calculate: Sum
   - Filter: Month equals prop("Billing Month")

**Note:** The filter in step 8 is complex. Alternative approach below if filtering doesn't work.

### Step 5: Add Calculation Formulas

9. **Add Overage Hours formula:**
   - Property Type: Formula
   - Name: `Overage Hours`
   - Formula: 
   ```
   max(0, prop("Total Hours Worked") - prop("Monthly Retainer Hours"))
   ```

10. **Add Overage Amount formula:**
    - Property Type: Formula
    - Name: `Overage Amount`
    - Formula:
    ```
    prop("Overage Hours") * prop("Overage Rate")
    ```

11. **Add Invoice Amount formula:**
    - Property Type: Formula
    - Name: `Invoice Amount`
    - Formula:
    ```
    if(prop("Billing Type") == "Current Retainer", 
       prop("Retainer Rate"), 
       prop("Overage Amount"))
    ```

12. **Add Invoice Description formula:**
    - Property Type: Formula
    - Name: `Invoice Description`
    - Formula:
    ```
    if(prop("Billing Type") == "Current Retainer",
       "Monthly retainer for " + prop("Billing Month"),
       "Overage hours for " + prop("Billing Month") + " (" + format(prop("Overage Hours")) + " hrs)")
    ```

## Alternative Simplified Approach

If the rollup filtering is complex, use this simpler manual approach:

### Simplified Step 4: Manual Hours Entry
Instead of automatic rollup, add:
- **Property Type:** Number
- **Name:** `Hours This Month`
- **Description:** Manually enter total hours from Time Tracking for this month

Then the formulas in Steps 9-12 work the same way using `prop("Hours This Month")` instead of `prop("Total Hours Worked")`.

## Sample Data Structure

Your Monthly Invoice Prep database should look like:

| Client | Billing Month | Billing Type | Hours This Month | Monthly Retainer Hours | Retainer Rate | Overage Hours | Overage Amount | Invoice Amount |
|--------|---------------|--------------|------------------|----------------------|---------------|---------------|----------------|----------------|
| Acme Corp | 2025-10 | Current Retainer | 75 | 80 | $8,000 | 0 | $0 | $8,000 |
| Acme Corp | 2025-09 | Previous Overage | 85 | 80 | $8,000 | 5 | $750 | $750 |
| Beta LLC | 2025-10 | Current Retainer | 35 | 40 | $5,000 | 0 | $0 | $5,000 |

## Monthly Process

### Creating Records for Current Month:
1. **Around the 15th of each month:**
   - Create new records for each client
   - Set Billing Month to current month (e.g., "2025-10")
   - Set Billing Type to "Current Retainer"
   - Invoice Amount will auto-calculate to Retainer Rate

2. **For previous month overages:**
   - Create additional records for clients with overages
   - Set Billing Month to previous month (e.g., "2025-09")
   - Set Billing Type to "Previous Overage"
   - Enter actual hours worked last month
   - Invoice Amount will auto-calculate overage charges

## Button for Invoice Generation (M4.1 Preview)

Later in M4.1, we'll add a button property that:
- Triggers the n8n webhook
- Passes this data to QuickBooks
- Only appears on current month records

## Validation Checklist

After setup, verify:
- [ ] All properties are created and working
- [ ] Formulas calculate correctly
- [ ] Overage Hours shows 0 when under retainer limit
- [ ] Overage Hours shows correct excess when over limit
- [ ] Invoice Amount switches correctly based on Billing Type
- [ ] Invoice Description provides clear context

## Next Steps

Once this setup is complete:
1. Test with sample data (M1.4)
2. Verify all calculations work correctly
3. Understand the monthly record creation process
4. Proceed to QuickBooks integration (Week 2)

## Notes

- This database becomes the "source of truth" for monthly billing
- Each record represents one line item on the final invoice
- The n8n automation will read from this database
- Manual record creation gives you control over what gets billed
- Formulas ensure calculation accuracy

---

**Status:** Ready for implementation  
**Time Required:** 20-30 minutes  
**Dependencies:** M1.1 and M1.2 must be completed first