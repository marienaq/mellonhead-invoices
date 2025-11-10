# Monthly Invoice Generation - Operations Guide

## 🗓️ Monthly Billing Schedule

**When to run:** 15th of each month  
**What it does:** Generate invoices for current month retainer + previous month overages  
**Time required:** 10-15 minutes (down from 60-90 minutes manual process)

---

## 📋 Monthly Checklist

### **Before Running (5 minutes)**
1. ✅ **Review Notion time entries** for the previous month
2. ✅ **Verify client hours** are accurately logged
3. ✅ **Check client configurations** in Notion Companies database
4. ✅ **Ensure all time entries have proper client assignments**

### **Generate Invoices (5 minutes)**
1. ✅ **Activate virtual environment**
2. ✅ **Run invoice generation command**
3. ✅ **Review generated invoices in QuickBooks**

### **After Running (5 minutes)**
1. ✅ **Review draft invoices** in QuickBooks for accuracy
2. ✅ **Send invoices** from QuickBooks
3. ✅ **Update any billing notes** if needed

---

## 🚀 How to Run Monthly Invoice Generation

### **Step 1: Activate Virtual Environment**
```bash
cd /path/to/mellonhead-invoices
source venv/bin/activate
```

### **Step 2: Run Invoice Generation**

**Standard Monthly Run (December 15th example):**
```bash
python populate_invoice_prep.py \
  --production \
  --overage-start 2025-10-01 \
  --overage-end 2025-10-31 \
  --bill-month 2025-12
```

**Breaking down the parameters:**
- `--production` → Use production QuickBooks (REQUIRED for real invoices)
- `--overage-start` → First day of PREVIOUS month (overages period)
- `--overage-end` → Last day of PREVIOUS month (overages period) 
- `--bill-month` → CURRENT month (retainer billing period)

### **Step 3: Monthly Parameter Guide**

| Invoice Date | Overage Period (Previous) | Retainer Period (Current) | Command |
|--------------|---------------------------|---------------------------|---------|
| Jan 15, 2026 | Dec 2025 | Jan 2026 | `--overage-start 2025-12-01 --overage-end 2025-12-31 --bill-month 2026-01` |
| Feb 15, 2026 | Jan 2026 | Feb 2026 | `--overage-start 2026-01-01 --overage-end 2026-01-31 --bill-month 2026-02` |
| Mar 15, 2026 | Feb 2026 | Mar 2026 | `--overage-start 2026-02-01 --overage-end 2026-02-29 --bill-month 2026-03` |

---

## 🎯 What The System Does

### **Data Collection**
1. **Fetches active clients** from Notion Companies database
2. **Retrieves time entries** for the overage period from Notion Time Tracking
3. **Calculates overage hours** (actual hours - retainer hours)
4. **Fetches service pricing** from QuickBooks for accurate amounts

### **Invoice Generation**
1. **Creates retainer line items** for current month (fixed services)
2. **Adds overage line items** for previous month (if applicable)
3. **Applies professional descriptions** with dynamic month formatting
4. **Includes payment instructions** (ACH/Wire contact info)
5. **Generates draft invoices** in QuickBooks

### **Expected Output**
```
🎯 Monthly Invoice Prep Population + QuickBooks Invoice Generation
===============================================================================
📅 Overage period: 2025-10-01 to 2025-10-31
📅 Retainer billing month: 2025-12  
📅 Invoice date: 2025-12-15
🔐 Initializing QuickBooks authentication (production)...
✅ QuickBooks authentication validated

📊 STEP 1: Fetching data from Notion...
Found data for 3 clients

📋 STEP 3: Processing client data for QuickBooks invoices...

🧾 STEP 4: Generating QuickBooks invoices...

📧 Creating consolidated invoice for ABA...
   ✅ Invoice created: #1052 (ID: 123)

📧 Creating consolidated invoice for HumanGood...
   ✅ Invoice created: #1053 (ID: 124)

📧 Creating consolidated invoice for TWG...
   ✅ Invoice created: #1054 (ID: 125)

🎯 Results: 3/3 invoices created
💰 Total amount: $12,750
📝 Invoice prep records: 6

🎉 Complete workflow successful!
```

---

## 🔧 Advanced Options

### **Dry Run (Test Mode)**
```bash
python populate_invoice_prep.py \
  --production \
  --dry-run \
  --overage-start 2025-10-01 \
  --overage-end 2025-10-31 \
  --bill-month 2025-12
```
**Use this to:** Preview what would be created without generating actual invoices

### **Debug Mode**
```bash
python populate_invoice_prep.py \
  --production \
  --debug \
  --overage-start 2025-10-01 \
  --overage-end 2025-10-31 \
  --bill-month 2025-12
```
**Use this to:** See detailed breakdown of calculations and data

### **Custom Invoice Date**
```bash
python populate_invoice_prep.py \
  --production \
  --overage-start 2025-10-01 \
  --overage-end 2025-10-31 \
  --bill-month 2025-12 \
  --invoice-date 2025-12-20
```
**Use this to:** Generate invoices with a specific date (not 15th)

---

## ⚠️ Important Notes

### **Client Configuration Requirements**
Each client in Notion Companies database must have:
- **Client Status:** "Active"
- **Monthly Retainer Hours:** Number of included hours
- **Retainer Rate:** Monthly retainer amount  
- **Overage Rate:** Per-hour overage rate
- **QB Customer ID:** QuickBooks customer ID
- **Retainer Service IDs:** Multi-select field with QB service IDs
- **Overage SKU:** QuickBooks item ID for overage billing

### **Time Entry Requirements**
Each time entry in Notion Time Tracking must have:
- **Date:** Within the overage period
- **Client:** Relation to Companies database OR title containing "for [ClientName]"
- **Hours:** Number of hours worked
- **Description:** Work description

### **What Happens to Different Scenarios**
- **Client under retainer hours:** Only retainer invoice (no overage)
- **Client over retainer hours:** Retainer + overage invoice
- **Client with 0 retainer hours:** All hours billed as overage
- **Missing time entries:** Only retainer invoice generated

---

## 🛠️ Troubleshooting

### **Authentication Issues**
```bash
python check_environment.py
```
**If tokens expired:** The system will provide OAuth playground instructions

### **Missing Invoices**
- Check client has "Active" status in Notion
- Verify QB Customer ID is correct
- Confirm Retainer Service IDs are populated

### **Incorrect Amounts**
- Verify service IDs match QuickBooks items
- Check overage rate in Notion client configuration
- Review time entries for accuracy

### **Connection Issues**
- Check internet connection
- Verify QuickBooks credentials haven't expired
- Review logs in `logs/qb_api_production.log`

### **Need Help?**
- 📧 **Support:** billing@mellonhead.co
- 📁 **Logs:** Check `logs/qb_api_production.log`
- 🔧 **Environment:** Run `python check_environment.py`

---

## 📊 ROI Achievement

**Before automation:** 60-90 minutes monthly  
**After automation:** 10-15 minutes monthly  
**Time savings:** 75-85% reduction  
**Annual savings:** ~50 hours/year

---

## 🔒 Security Reminders

- **Never commit** credential files to version control
- **Keep tokens secure** and rotate regularly  
- **Monitor API usage** for unusual activity
- **Use production mode only** for real invoices
- **Always review invoices** before sending to clients

---

*System designed and implemented November 2025*  
*🧮 Generated with Claude Code*