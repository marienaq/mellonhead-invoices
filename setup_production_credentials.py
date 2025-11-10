#!/usr/bin/env python3
"""
Production Credentials Setup Helper
Interactive script to help set up production QuickBooks credentials
"""

import os
import sys


def get_user_input(prompt: str, required: bool = True) -> str:
    """Get user input with validation."""
    while True:
        value = input(f"{prompt}: ").strip()
        if value or not required:
            return value
        print("❌ This field is required. Please try again.")


def setup_production_credentials():
    """Interactive setup for production credentials."""
    print("🚀 PRODUCTION CREDENTIALS SETUP")
    print("=" * 50)
    print("")
    print("This script will help you configure your production QuickBooks credentials.")
    print("You'll need your production app credentials from developer.intuit.com")
    print("")
    
    # Check if production config already exists
    prod_config = "credentials.production.config"
    if os.path.exists(prod_config):
        overwrite = input(f"⚠️  {prod_config} already exists. Overwrite? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("❌ Setup cancelled.")
            return
    
    print("📋 Please provide your production QuickBooks credentials:")
    print("")
    
    # Get QuickBooks credentials
    client_id = get_user_input("🔑 Production Client ID")
    client_secret = get_user_input("🔐 Production Client Secret")
    access_token = get_user_input("🎫 Production Access Token")
    refresh_token = get_user_input("🔄 Production Refresh Token")
    realm_id = get_user_input("🏢 Production Company/Realm ID")
    
    print("")
    print("📊 Notion credentials (copying from existing config)...")
    
    # Copy Notion credentials from sandbox config
    notion_token = ""
    notion_client_hours_db = ""
    notion_companies_db = ""
    notion_monthly_prep_db = ""
    
    sandbox_config = "credentials.sandbox.config"
    if os.path.exists(sandbox_config):
        with open(sandbox_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('NOTION_TOKEN='):
                    notion_token = line.split('=', 1)[1]
                elif line.startswith('NOTION_CLIENT_HOURS_DB='):
                    notion_client_hours_db = line.split('=', 1)[1]
                elif line.startswith('NOTION_COMPANIES_DB='):
                    notion_companies_db = line.split('=', 1)[1]
                elif line.startswith('NOTION_MONTHLY_PREP_DB='):
                    notion_monthly_prep_db = line.split('=', 1)[1]
    
    # Allow user to override Notion credentials if needed
    print(f"   Notion Token: {notion_token[:20]}..." if notion_token else "   Notion Token: Not found")
    if input("   Use different Notion credentials? (y/N): ").lower().strip() == 'y':
        notion_token = get_user_input("🗂️ Notion Token")
        notion_client_hours_db = get_user_input("📊 Client Hours Database ID")
        notion_companies_db = get_user_input("🏢 Companies Database ID") 
        notion_monthly_prep_db = get_user_input("📋 Monthly Prep Database ID")
    
    # Create production credentials file
    from datetime import datetime
    content = f"""# QuickBooks Production Environment Credentials  
# DO NOT COMMIT TO VERSION CONTROL

# QuickBooks Production API Credentials
INTUIT_CLIENT_ID={client_id}
INTUIT_CLIENT_SECRET={client_secret}
INTUIT_ACCESS_TOKEN={access_token}
INTUIT_REFRESH_TOKEN={refresh_token}
INTUIT_REALM_ID={realm_id}
TOKEN_TIMESTAMP={datetime.now().isoformat()}

# Notion API Credentials (shared across environments)
NOTION_TOKEN={notion_token}
NOTION_CLIENT_HOURS_DB={notion_client_hours_db}
NOTION_COMPANIES_DB={notion_companies_db}
NOTION_MONTHLY_PREP_DB={notion_monthly_prep_db}
"""
    
    try:
        with open(prod_config, 'w') as f:
            f.write(content)
        
        print("")
        print("✅ Production credentials saved successfully!")
        print(f"📁 File: {prod_config}")
        print("")
        print("🧪 TESTING PRODUCTION CONNECTION...")
        
        # Test the connection
        try:
            from qb_auth_manager import QuickBooksAuthManager
            auth = QuickBooksAuthManager(environment="production")
            
            if auth.validate_connection():
                print("✅ Production connection test successful!")
                print("")
                print("🚀 READY FOR PRODUCTION:")
                print("   Use --production flag to run in production mode:")
                print("   python populate_invoice_prep.py --production --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12")
            else:
                print("❌ Production connection test failed.")
                print("   Please verify your credentials and try again.")
                if auth.requires_manual_reauth():
                    print("")
                    print(auth.get_reauth_instructions())
                    
        except Exception as e:
            print(f"❌ Error testing connection: {e}")
            print("   Please verify your credentials manually.")
    
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return
    
    print("")
    print("🔒 SECURITY REMINDERS:")
    print("   • Never commit credentials.production.config to version control")
    print("   • Keep production credentials secure and rotate regularly")
    print("   • Monitor API usage and set up alerts")
    print("")


if __name__ == "__main__":
    setup_production_credentials()