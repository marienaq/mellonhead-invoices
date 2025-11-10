# Notion Clients Table Enhancement Guide
*Task M1.1 - Database Foundation Setup*

## Overview
This guide walks through adding the required fields to your existing Notion Clients table to support automated invoice generation.

## Required Fields to Add

### 1. Monthly Retainer Hours
- **Property Type:** Number
- **Property Name:** `Monthly Retainer Hours`
- **Description:** Total hours allocated per month under the retainer agreement
- **Example Values:** 40, 60, 80, 120

### 2. Retainer Rate  
- **Property Type:** Number
- **Format:** Currency (USD)
- **Property Name:** `Retainer Rate`
- **Description:** Fixed monthly retainer amount charged regardless of hours used
- **Example Values:** $5000, $8000, $12000

### 3. Overage Rate
- **Property Type:** Number  
- **Format:** Currency (USD)
- **Property Name:** `Overage Rate`
- **Description:** Hourly rate charged for hours beyond monthly allocation
- **Example Values:** $150, $200, $250

### 4. QuickBooks Customer ID
- **Property Type:** Text
- **Property Name:** `QB Customer ID`
- **Description:** QuickBooks customer reference ID for API integration
- **Example Values:** "123", "456", "789"
- **Note:** These will be populated in M2.2 after mapping existing QB customers

### 5. Fixed Invoice Line Items
- **Property Type:** Multi-select OR Relation (depending on complexity)
- **Property Name:** `Fixed Line Items`
- **Description:** Standard SKUs that appear on every invoice for this client
- **Example Options:** 
  - "Monthly Retainer - Basic"
  - "Platform Fee" 
  - "Support Package"
  - "Advisory Services"

### 6. Overage SKU
- **Property Type:** Text
- **Property Name:** `Overage SKU`  
- **Description:** QuickBooks item ID used for billing overage hours
- **Example Values:** "OVERAGE-CONSULTING", "ADDITIONAL-HOURS"
- **Note:** These will be populated in M2.3 after mapping QB items

## Step-by-Step Setup Instructions

### Phase 1: Add Basic Billing Fields

1. **Open your existing Clients table in Notion**

2. **Add Monthly Retainer Hours field:**
   - Click the "+" button at the end of your properties
   - Select "Number" property type
   - Name: `Monthly Retainer Hours`
   - Click "Create"

3. **Add Retainer Rate field:**
   - Click the "+" button again
   - Select "Number" property type
   - Name: `Retainer Rate`
   - In the number format dropdown, select "Dollar"
   - Click "Create"

4. **Add Overage Rate field:**
   - Click the "+" button again
   - Select "Number" property type
   - Name: `Overage Rate`
   - In the number format dropdown, select "Dollar"
   - Click "Create"

### Phase 2: Add QuickBooks Integration Fields

5. **Add QuickBooks Customer ID field:**
   - Click the "+" button
   - Select "Text" property type
   - Name: `QB Customer ID`
   - Click "Create"

6. **Add Overage SKU field:**
   - Click the "+" button
   - Select "Text" property type
   - Name: `Overage SKU`
   - Click "Create"

### Phase 3: Add Fixed Line Items Field

7. **Add Fixed Line Items field:**
   
   **Option A - Multi-select (Simpler setup):**
   - Click the "+" button
   - Select "Multi-select" property type
   - Name: `Fixed Line Items`
   - Add common options like:
     - "Monthly Retainer"
     - "Platform Fee"
     - "Support Package"
     - "Advisory Services"
   - Click "Create"
   
   **Option B - Relation (More flexible):**
   - First create a separate "Line Items" database
   - Then add a Relation property pointing to that database
   - *Recommend Option A for simplicity*

## Sample Data Entry

For each existing client, you'll need to populate these fields. Here's a sample:

**Client: Acme Corp**
- Monthly Retainer Hours: `80`
- Retainer Rate: `$8,000`
- Overage Rate: `$150`
- QB Customer ID: `[Leave blank for now - will populate in M2.2]`
- Fixed Line Items: `["Monthly Retainer", "Platform Fee"]`
- Overage SKU: `[Leave blank for now - will populate in M2.3]`

## Validation Checklist

After adding all fields, verify:
- [ ] All 6 new properties are visible in your Clients table
- [ ] Number fields are formatted as currency where appropriate
- [ ] Text fields accept sample data without errors
- [ ] Multi-select field has relevant options for your business
- [ ] Existing client data is preserved and visible

## Next Steps

Once this setup is complete:
1. Populate retainer hours and rates for all existing clients
2. Configure Fixed Line Items for each client
3. Leave QB Customer ID and Overage SKU blank for now (populated in M2.2 and M2.3)
4. Proceed to M1.2: Time Tracking table verification

## Notes

- These fields support the automated calculation formulas we'll create in M1.3
- QB Customer ID and Overage SKU will be populated after QuickBooks mapping
- Fixed Line Items can be modified per client as needed
- All currency amounts should match your current billing practices

---

**Status:** Ready for implementation  
**Time Required:** 15-20 minutes  
**Dependencies:** Access to Notion workspace with admin permissions