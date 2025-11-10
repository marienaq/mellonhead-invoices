# Mellon Head Invoice Automation
## Time Tracking & Invoicing Solution

---

## Business Context

**Company:** Mellon Head (AI education and advisory services)  
**Team Size:** 3 employees  
**Client Base:** Handful of clients on retainer model  
**Current Systems:** Google Workspace, Slack, Notion, QuickBooks

---

## Requirements

### Current State
- Manual time tracking in Notion database (date, hours, client, rate, daily amount)
- Monthly manual rollup and calculation
- Manual invoice creation in QuickBooks
- Billing cycle: 15th of month for upcoming retainer + previous month overages

### Business Model
- **Retainer Structure:** Fixed monthly rate for allocated hours per client
- **Overage Billing:** Separate rate for hours beyond monthly allocation
- **Reality:** Most clients do NOT go over their monthly hours
- **Invoice Timing:** Bill on 15th for next month's retainer plus any prior month overages

### Pain Points
1. Time-consuming monthly calculations
2. Risk of forgetting overage rates for different clients
3. Manual data entry into QuickBooks
4. No systematic tracking of retainer hours vs actual hours

### Must-Haves
- Track client retainer hours and rates
- Track overage rates per client
- Calculate monthly retainer charges
- Calculate previous month overage charges
- Support multiple fixed SKUs per client on invoice
- Add optional overage SKU only when overages exist
- Integrate with QuickBooks for invoice generation
- Manual review before invoices are sent
- Slack notification when invoices are ready

---

## Proposed Solution

### Strategy
Enhance existing Notion setup with automation rather than building custom software. Leverage Notion AI and native automations (included in Business plan).

### Architecture
**Notion (Data & Calculation)** → **n8n (Integration Layer)** → **QuickBooks (Invoice Generation)** → **Slack (Notification)**

### Key Components

#### 1. Enhanced Notion Database Structure
- **Clients Table** (enhanced existing table)
- **Time Tracking Table** (existing, with improvements)
- **Invoice Prep View** (new automated calculation view)

#### 2. Automation Flow
- Manual trigger button in Notion
- Automated calculation of charges
- QuickBooks draft invoice creation via API
- Slack notification with review link

#### 3. User Control
- Manual trigger prevents accidental invoice generation
- Review step in QuickBooks before sending
- Clear visibility of all calculations in Notion

---

## Implementation Plan

### Phase 1: Notion Database Enhancement

#### Step 1.1: Update Clients Table
Add the following properties to existing Clients table:

- **Monthly Retainer Hours** (Number)
- **Retainer Rate** (Number, currency formatted)
- **Overage Rate** (Number, currency formatted)
- **QuickBooks Customer ID** (Text - for API integration)
- **Invoice Line Items** (Multi-select or Relation to Line Items table)
  - This will store the fixed SKUs that appear on every invoice for this client
  - Example: "Monthly Retainer - Basic", "Platform Fee", "Support Package"
- **Overage SKU** (Text - QuickBooks item ID for overage billing)
  - Example: "Additional Hours" or "Overage Consulting"

#### Step 1.2: Enhance Time Tracking Table
Verify/add these properties:

- **Date** (Date)
- **Client** (Relation to Clients table)
- **Hours Worked** (Number)
- **Notes/Description** (Text, optional)
- **Month** (Formula: `formatDate(prop("Date"), "YYYY-MM")`)
- **Client Retainer Hours** (Rollup from Client relation)

#### Step 1.3: Create Monthly Summary View
Create a new database or view for monthly calculations:

**Monthly Invoice Prep** (can be a grouped view or separate linked database)
- Group by: Client
- Filter by: Current billing period
- Calculated fields:
  - Total hours (this month)
  - Retainer charge (fixed from client table)
  - Overage hours (formula: `if(prop("Total Hours") > prop("Retainer Hours"), prop("Total Hours") - prop("Retainer Hours"), 0)`)
  - Overage charge (formula: `prop("Overage Hours") * prop("Overage Rate")`)
  - Total due this invoice (Retainer + Overage from previous month)

### Phase 2: QuickBooks Integration Setup

#### Step 2.1: QuickBooks API Access
1. Create QuickBooks developer account at https://developer.intuit.com
2. Create a new app in "My Apps" section
3. Generate API credentials (Client ID, Client Secret)
4. Set up OAuth 2.0 authentication
5. Document QuickBooks customer IDs for each Mellon Head client
6. Document all SKU/Item IDs used across clients (for fixed line items and overages)

**Important API Notes:**
- QuickBooks API uses SQL-like query syntax for filtering
- CustomerRef must be in single quotes in queries
- Invoice properties must be marked "filterable" to use in WHERE clauses
- EmailStatus: "NotSet" keeps invoices as drafts (not sent to customer)

#### Step 2.2: n8n Workflow
Self-hosted or cloud n8n instance required. This workflow creates fresh draft invoices rather than updating recurring templates, which is simpler and more reliable.

**Trigger:** Webhook from Notion (when button clicked)

**Workflow Steps:**

1. **Receive Webhook** 
   - Accept trigger from Notion with client IDs to process
   - Parse billing period (current month for retainer, previous month for overages)

2. **For Each Client - Get Client Data** (Loop)
   - Notion node to retrieve:
     - Client name and QuickBooks Customer ID
     - Fixed line items/SKUs with amounts
     - Overage SKU ID
     - Monthly retainer hours
     - Overage rate

3. **Get Previous Month Time Tracking Data**
   - Notion node to query time entries:
     - Filter: Previous month's hours for this client
     - Calculate: Total hours worked
   - Formula: `overageHours = Math.max(0, totalHours - retainerHours)`
   - Formula: `overageAmount = overageHours * overageRate`

4. **Check for Existing Draft Invoices** (Cleanup)
   - QuickBooks HTTP Request node:
   - Method: GET
   - Endpoint: `/v3/company/{realmId}/query`
   - Query: `SELECT * FROM Invoice WHERE CustomerRef = '{customerId}' AND EmailStatus = 'NotSet'`
   - This finds any draft invoices from previous runs

5. **Delete Existing Drafts** (If Found)
   - IF node: Check if any drafts exist
   - QuickBooks HTTP Request node (for each draft found):
     - Method: POST  
     - Endpoint: `/v3/company/{realmId}/invoice?operation=delete`
     - Include invoice Id and SyncToken in body

6. **Build Line Items Array** - Function node:
   ```javascript
   // Build complete line items array
   const lineItems = [];
   
   // Add all fixed SKUs from client configuration
   items.fixedLineItems.forEach(sku => {
     lineItems.push({
       Amount: parseFloat(sku.amount),
       DetailType: "SalesItemLineDetail",
       SalesItemLineDetail: {
         ItemRef: {
           value: sku.qbItemId,
           name: sku.name
         }
       },
       Description: sku.description || sku.name
     });
   });
   
   // Add overage SKU ONLY if overages exist
   if (items.overageHours > 0) {
     lineItems.push({
       Amount: items.overageAmount,
       DetailType: "SalesItemLineDetail",
       SalesItemLineDetail: {
         ItemRef: {
           value: items.overageSKU,
           name: "Additional Hours"
         },
         Qty: items.overageHours,
         UnitPrice: items.overageRate
       },
       Description: `Additional hours from ${items.previousMonth} (${items.overageHours} hrs @ ${items.overageRate}/hr)`
     });
   }
   
   return { lineItems, totalAmount: lineItems.reduce((sum, item) => sum + item.Amount, 0) };
   ```

7. **Create New Draft Invoice** - QuickBooks HTTP Request node:
   - Method: POST
   - Endpoint: `/v3/company/{realmId}/invoice`
   - Body:
   ```json
   {
     "CustomerRef": {
       "value": "{{customerId}}"
     },
     "TxnDate": "{{invoiceDate}}",
     "DueDate": "{{dueDate}}",
     "Line": {{lineItems}},
     "EmailStatus": "NotSet",
     "BillEmail": {
       "Address": "{{customerEmail}}"
     },
     "PrivateNote": "Generated automatically via n8n - {{currentDate}}"
   }
   ```

8. **Get Invoice URL** 
   - QuickBooks invoice URLs follow pattern:
   - `https://app.qbo.intuit.com/app/invoice?txnId={{invoiceId}}`
   - Build URL from returned invoice ID

9. **Aggregate Results** (After Loop)
   - Collect all created invoices
   - Build summary for Slack notification

10. **Send Slack Notification** - Slack node with formatted message
    - Include invoice totals, breakdown, and links

**Error Handling:**
- Add Error Trigger workflow for failed QB API calls
- Catch errors at each QuickBooks interaction step
- Notify via Slack if any step fails with error details
- Log errors to Notion database for tracking

### Phase 3: Slack Notification Setup

#### Step 3.1: Slack Webhook Configuration
1. Create incoming webhook in Slack workspace
2. Choose notification channel (e.g., #finance or DM)
3. Configure message template

#### Step 3.2: Notification Message Format
```
📊 Monthly Invoices Ready for Review

Invoices generated for [Month Year]:
• [Client 1]: $[amount] 
  - Fixed charges: $X ([count] line items)
  - Overage: $Y ([hours] hrs) ← only if overages exist
• [Client 2]: $[amount] 
  - Fixed charges: $X ([count] line items)
  - No overages

Review and approve in QuickBooks:
[Link to QuickBooks Invoices]

Generated: [timestamp]
```

### Phase 4: Notion Automation Button

#### Step 4.1: Create Invoice Generation Button
In Notion Monthly Invoice Prep view:
1. Add button property: "Generate QB Invoices"
2. Configure button to trigger n8n webhook
3. Add confirmation dialog: "Generate invoices for [count] clients?"

#### Step 4.2: Notion Webhook Setup
1. Get webhook URL from n8n workflow
2. Configure Notion button to call webhook with client data payload
3. Pass necessary parameters: client IDs, billing period

#### Step 4.3: Post-Generation Tracking
Optional: Add checkbox or status field to track:
- Invoice generated (yes/no)
- Invoice sent date
- Payment received date

### Phase 5: Testing & Validation

#### Step 5.1: Test Data
1. Create test client in both Notion and QuickBooks
2. Add test time entries
3. Run through complete workflow
4. Verify calculations match expected values
5. Check QuickBooks draft invoice accuracy
6. Confirm Slack notification arrives

#### Step 5.2: Edge Cases
Test scenarios:
- Client with no overage (overage SKU should NOT appear)
- Client with overage (overage SKU should appear with correct calculation)
- Client with multiple fixed SKUs (all should appear in correct order)
- Client with single fixed SKU
- Client with zero hours tracked (only fixed SKUs, no overage)
- Multiple clients in single run
- **Re-running invoice generation on same day** (should delete old drafts and create fresh ones)
- **QuickBooks API rate limiting** (ensure proper error handling)
- **Missing SKU IDs** (workflow should fail gracefully with clear error)

#### Step 5.3: Go-Live Checklist
- [ ] All clients have retainer hours and rates configured
- [ ] Fixed SKUs mapped for each client in Notion
- [ ] Overage SKUs configured per client
- [ ] QuickBooks customer IDs mapped correctly
- [ ] n8n workflow tested end-to-end
- [ ] Slack notifications working
- [ ] Manual trigger button functional
- [ ] Documentation created for monthly process

---

## Monthly Workflow (Post-Implementation)

### Around the 15th of Each Month:

1. **Review time entries** in Notion (ensure all hours logged for previous month)
2. **Open Monthly Invoice Prep view** in Notion
3. **Review calculations** for each client:
   - Verify retainer amount is correct
   - Check overage hours and charges
4. **Click "Generate QB Invoices" button**
5. **Wait for Slack notification** (typically 1-2 minutes)
6. **Review draft invoices in QuickBooks**
7. **Make any manual adjustments** if needed
8. **Send invoices** from QuickBooks

**Time savings:** From ~60-90 minutes to ~10-15 minutes per month

---

## Technical Details

## Technical Details

### Integration Requirements
- **Notion API:** Business plan (already have)
- **QuickBooks API:** Access via QuickBooks Online account
  - Uses OAuth 2.0 authentication
  - Supports SQL-like query syntax for filtering invoices
  - Rate limits apply (typically 500 requests per minute per app)
- **n8n:** Self-hosted (free, requires server) OR n8n Cloud ($20-50/month)
  - Recommended: n8n Cloud for easier setup and maintenance
  - Alternative: Self-host on DigitalOcean/AWS (~$5-10/month + setup time)
- **Slack Webhook:** Free, included with workspace

### Workflow Architecture
The solution creates fresh draft invoices each time rather than updating templates or recurring invoices. This approach:
- **Avoids complexity** of QuickBooks recurring invoice API limitations
- **Provides cleanup** by deleting any existing drafts before creating new ones
- **Ensures consistency** - every invoice generation creates a clean, complete invoice
- **Allows re-runs** on the same day without creating duplicates

### Data Security
- All data remains in existing systems (Notion, QuickBooks)
- API credentials stored securely in n8n
- n8n Cloud: SOC 2 Type II compliant, encrypted at rest
- Self-hosted n8n: You control all security measures
- OAuth tokens refresh automatically

### Maintenance
- **Monthly:** None required for normal operations
- **Quarterly:** Review n8n execution logs for errors
- **Annually:** Update QuickBooks OAuth tokens if needed
- **As needed:** Add new clients and their fixed SKUs to system
- **n8n updates:** Cloud handles automatically; self-hosted requires manual updates

---

## Estimated Implementation Time

**Total: 4-5 hours**

- Phase 1 (Notion setup): 45-60 minutes (additional time for SKU mapping)
- Phase 2 (QuickBooks API + n8n workflow): 90-120 minutes (includes draft cleanup logic)
- Phase 3 (Slack setup): 15 minutes
- Phase 4 (Webhook + button): 20-30 minutes
- Phase 5 (Testing): 45-60 minutes (additional edge cases, cleanup testing)

---

## Future Enhancements (Optional)

### Nice-to-Haves (Not Immediate Priority)
- Automatic payment tracking when QB invoices marked paid
- Dashboard showing YTD revenue by client
- Automated reminder if time not logged for current week
- Export capability for annual financial reports

### If Business Scales
Consider custom application if:
- Client count exceeds 20-30
- Multiple team members need separate time tracking
- Complex project-based billing required
- Need for client portal or self-service

---

## Success Metrics

- **Time saved:** 75-85% reduction in monthly invoicing time
- **Accuracy:** Zero calculation errors
- **Adoption:** All team members logging time consistently
- **Client satisfaction:** Invoices sent on-time every 15th

---

## Support & Documentation

### Resources Needed
- Notion database templates (created during setup)
- n8n workflow JSON export (for backup/versioning)
- QuickBooks customer ID reference sheet
- QuickBooks SKU/item ID mapping per client
- Monthly workflow checklist (above)

### Point of Contact
Primary administrator: [To be assigned]

---

## Risk Mitigation

### Potential Issues & Solutions

**Issue:** QuickBooks API authentication expires  
**Solution:** n8n handles OAuth refresh automatically; set calendar reminder to check quarterly

**Issue:** Calculation discrepancy discovered  
**Solution:** Manual review step in QuickBooks allows catching errors before sending

**Issue:** n8n workflow fails  
**Solution:** Check execution logs in n8n; error notifications sent to Slack; workflow includes retry logic

**Issue:** Client's fixed SKUs change  
**Solution:** Update Notion client record; changes apply to next invoice generation

**Issue:** Accidentally run invoice generation twice on same day  
**Solution:** Workflow automatically deletes existing drafts before creating new ones; safe to re-run

**Issue:** Notion database structure changes  
**Solution:** Document all property names and formulas; test in duplicate database first

**Issue:** Client rate changes mid-month  
**Solution:** Update client table immediately; add note in time tracking for affected period

**Issue:** Wrong SKU appears on invoice  
**Solution:** Review QuickBooks item IDs in Notion; verify mapping is correct; check n8n execution log

**Issue:** QuickBooks API rate limit hit  
**Solution:** n8n can implement retry logic with exponential backoff; typical limits are 500 req/min which should be sufficient

**Issue:** Missing customer in QuickBooks  
**Solution:** n8n error handler catches this; Slack notification identifies which customer is missing; add to QuickBooks manually

---

## Next Steps

## Next Steps

1. **Approve this implementation plan**
2. **Decide on n8n hosting:** Cloud ($20/mo) vs Self-hosted ($5-10/mo + setup)
3. **Map all client SKUs in QuickBooks** (identify item IDs for fixed charges and overages)
4. **Gather QuickBooks customer IDs** for each Mellon Head client
5. **Set up QuickBooks developer app** and obtain API credentials
6. **Set up n8n instance** (if not already running)
7. **Schedule 5-hour implementation block**
8. **Begin Phase 1: Notion database enhancement**

---

## Appendix: QuickBooks API Reference

### Key API Endpoints Used

**Query Invoices:**
```
GET /v3/company/{realmId}/query?query=SELECT * FROM Invoice WHERE CustomerRef = '{customerId}' AND EmailStatus = 'NotSet'
```

**Create Invoice:**
```
POST /v3/company/{realmId}/invoice
```

**Delete Invoice:**
```
POST /v3/company/{realmId}/invoice?operation=delete
```

### Important API Notes

1. **Query Syntax:** QuickBooks uses SQL-like syntax but with specific limitations
   - String values must use single quotes: `CustomerRef = '123'`
   - Only "filterable" properties can be used in WHERE clauses
   - Common filterable fields: CustomerRef, TxnDate, Balance, EmailStatus

2. **Draft Invoice Creation:**
   - Set `EmailStatus: "NotSet"` to create draft (not sent to customer)
   - Invoice appears in QuickBooks but is not emailed automatically
   - Can be edited and sent manually from QuickBooks UI

3. **Line Items:**
   - Each line requires `DetailType` (typically "SalesItemLineDetail")
   - ItemRef must reference valid QuickBooks Item/Service ID
   - Amount is required; Qty and UnitPrice are optional but recommended for clarity

4. **OAuth 2.0:**
   - Access tokens expire after 1 hour
   - Refresh tokens valid for 100 days
   - n8n handles token refresh automatically

5. **Rate Limits:**
   - 500 requests per minute per app (typical)
   - 10,000 requests per day per company (typical)
   - Mellon Head workflow well within limits (~3-10 API calls per month)

---

*Document Version: 1.0*  
*Last Updated: October 1, 2025*  
*Owner: Mellon Head*