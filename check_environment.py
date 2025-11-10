#!/usr/bin/env python3
"""
Environment Configuration Checker
Utility to check which environments are configured and test connections
"""

import os
import sys
from qb_auth_manager import QuickBooksAuthManager


def check_environment(env_name: str):
    """Check if an environment is configured and test connection."""
    print(f"\n🔧 CHECKING {env_name.upper()} ENVIRONMENT")
    print("-" * 40)
    
    try:
        auth = QuickBooksAuthManager(environment=env_name)
        
        print(f"📁 Credentials file: {auth.credentials_file}")
        print(f"🌐 Base URL: {auth.base_url}")
        
        # Check if credentials file exists
        if not os.path.exists(auth.credentials_file):
            print(f"❌ Credentials file not found: {auth.credentials_file}")
            if env_name == "production":
                print("   → Run: python setup_production_credentials.py")
            return False
        
        # Check credentials
        realm_id = auth.credentials.get('INTUIT_REALM_ID')
        client_id = auth.credentials.get('INTUIT_CLIENT_ID', '')
        
        print(f"🏢 Realm ID: {realm_id}")
        print(f"🔑 Client ID: {client_id[:20]}..." if client_id else "🔑 Client ID: Not set")
        
        # Test connection
        print("🧪 Testing connection...")
        if auth.requires_manual_reauth():
            print("❌ Manual re-authorization required")
            return False
        
        if auth.validate_connection():
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function to check all environments."""
    print("🔍 QUICKBOOKS ENVIRONMENT CHECKER")
    print("=" * 50)
    
    environments = ["sandbox", "production"]
    results = {}
    
    for env in environments:
        results[env] = check_environment(env)
    
    print("\n" + "=" * 50)
    print("📊 ENVIRONMENT STATUS SUMMARY")
    print("=" * 50)
    
    for env, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {env.title()}: {'Ready' if status else 'Not Ready'}")
    
    print("\n💡 USAGE:")
    print("   Sandbox: python populate_invoice_prep.py --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12")
    print("   Production: python populate_invoice_prep.py --production --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12")
    
    if not results["production"]:
        print("\n🚀 TO SET UP PRODUCTION:")
        print("   python setup_production_credentials.py")


if __name__ == "__main__":
    main()