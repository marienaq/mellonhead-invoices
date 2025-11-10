# QuickBooks Data Fetcher Setup

This script fetches customer IDs and service/item IDs from your QuickBooks account for the invoice automation setup.

## Quick Start

1. **Copy the config template:**
   ```bash
   cp config.example.json config.json
   ```

2. **Add your QuickBooks credentials to `config.json`:**
   ```json
   {
     "quickbooks": {
       "clientId": "your_client_id",
       "clientSecret": "your_client_secret", 
       "realmId": "your_company_id",
       "accessToken": "your_access_token",
       "refreshToken": "your_refresh_token",
       "environment": "sandbox",
       "baseUrl": "https://sandbox-quickbooks.api.intuit.com"
     }
   }
   ```

3. **Install dependencies:**
   ```bash
   pip install requests
   ```

4. **Run the script:**
   ```bash
   python qb_fetch.py
   ```

## What It Does

The script will:
- ✅ Fetch all customers from QuickBooks
- ✅ Fetch all active items/services  
- ✅ Look for matches to your Notion clients (ABA, HumanGood)
- ✅ Display formatted results
- ✅ Save data to timestamped JSON file for reference

## Expected Output

```
🚀 QuickBooks Data Fetcher
========================================
🌍 Environment: sandbox
🏢 Company ID: 123456789

📋 Fetching customers...
✅ Found 5 customers

🛍️ Fetching items/services...  
✅ Found 12 active items/services

============================================================
💼 CUSTOMERS
============================================================
Name: American Bankers Association
ID: 123
Company: ABA
Status: Active
------------------------------

============================================================
🎯 MAPPING TO NOTION CLIENTS
============================================================
🔍 Searching for: ABA
   ✅ MATCH: American Bankers Association (ID: 123)

🔍 Searching for: HumanGood  
   ✅ MATCH: HumanGood Services (ID: 456)

============================================================
🛍️ ITEMS/SERVICES
============================================================
Name: Monthly Retainer - Basic
ID: 789
Type: Service
Unit Price: $5000
------------------------------
```

## Security Notes

- ✅ `config.json` is in `.gitignore` (secrets won't be committed)
- ✅ Use sandbox environment for testing
- ✅ Switch to production URLs when going live

## Next Steps

1. **Update Notion with Customer IDs:**
   - ABA client → QB Customer ID: `123`
   - HumanGood client → QB Customer ID: `456`

2. **Update Notion with Item IDs:**
   - Map Fixed Line Items to QuickBooks item IDs
   - Set Overage SKU for each client

3. **For Production:**
   - Change environment to "production"
   - Update baseUrl to "https://quickbooks.api.intuit.com"
   - Get production customer/item IDs

## Troubleshooting

**Config file not found:**
```
❌ Config file not found: config.json
💡 Copy config.example.json to config.json and add your credentials
```

**Invalid credentials:**
```
❌ API request failed: 401 Unauthorized
```
- Check your access token is valid
- Ensure realmId matches your QuickBooks company

**No customers found:**
- Verify you're connecting to the right environment (sandbox vs production)
- Check that customers exist in your QuickBooks account