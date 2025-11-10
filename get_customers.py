#!/usr/bin/env python3
"""
QuickBooks Customer ID Fetcher
Reads from credentials.config and determines production vs sandbox environment.
"""

import os
import requests
import json
from typing import Dict, List
import sys


def load_credentials():
    """Load credentials from credentials.config file."""
    config_file = "credentials.config"
    
    if not os.path.exists(config_file):
        print(f"❌ Credentials file not found: {config_file}")
        sys.exit(1)
    
    credentials = {}
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()
    
    return credentials


def get_access_token(client_id: str, client_secret: str) -> str:
    """
    Get access token from QuickBooks.
    Note: This is a simplified version. In practice, you'll need OAuth flow.
    """
    print("⚠️  ACCESS TOKEN NEEDED")
    print("This script needs an access token from your QuickBooks OAuth flow.")
    print("For now, please provide your access token manually.")
    
    token = input("\nEnter your QuickBooks access token: ").strip()
    if not token:
        print("❌ Access token required")
        sys.exit(1)
    
    return token


def get_realm_id() -> str:
    """Get the QuickBooks company/realm ID."""
    print("\n📋 REALM ID NEEDED")
    print("This is your QuickBooks Company ID (also called Realm ID).")
    print("You can find it in your QuickBooks developer app dashboard.")
    
    realm_id = input("\nEnter your QuickBooks Realm/Company ID: ").strip()
    if not realm_id:
        print("❌ Realm ID required")
        sys.exit(1)
    
    return realm_id


def detect_environment(access_token: str, realm_id: str) -> Dict:
    """
    Try to detect if we're using sandbox or production by making test calls.
    """
    environments = [
        {
            "name": "sandbox",
            "base_url": "https://sandbox-quickbooks.api.intuit.com",
            "description": "Sandbox (test environment)"
        },
        {
            "name": "production", 
            "base_url": "https://quickbooks.api.intuit.com",
            "description": "Production (live environment)"
        }
    ]
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    print("\n🔍 DETECTING ENVIRONMENT...")
    
    for env in environments:
        print(f"   Testing {env['description']}...")
        
        url = f"{env['base_url']}/v3/company/{realm_id}/companyinfo/{realm_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: Connected to {env['description']}")
                return env
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n⚠️  Could not detect environment. Defaulting to sandbox.")
    return environments[0]  # Default to sandbox


def fetch_customers(base_url: str, access_token: str, realm_id: str) -> List[Dict]:
    """Fetch all customers from QuickBooks."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    url = f"{base_url}/v3/company/{realm_id}/query"
    params = {'query': 'SELECT * FROM Customer'}
    
    print(f"\n📋 Fetching customers from {base_url}...")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'QueryResponse' in data and 'Customer' in data['QueryResponse']:
            customers = data['QueryResponse']['Customer']
            print(f"✅ Found {len(customers)} customers")
            return customers
        else:
            print("⚠️  No customers found")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch customers: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return []


def display_customers(customers: List[Dict], environment: str):
    """Display customers in a readable format."""
    print(f"\n" + "="*60)
    print(f"💼 CUSTOMERS ({environment.upper()} ENVIRONMENT)")
    print("="*60)
    
    # Look for potential matches to Notion clients
    notion_clients = ['aba', 'humangood', 'american bankers', 'american banker']
    
    for customer in customers:
        name = customer.get('Name', 'N/A')
        customer_id = customer.get('Id', 'N/A')
        company = customer.get('CompanyName', '')
        active = customer.get('Active', True)
        
        # Check if this might match a Notion client
        is_match = False
        for notion_client in notion_clients:
            if notion_client in name.lower() or notion_client in company.lower():
                is_match = True
                break
        
        # Display with highlighting for potential matches
        if is_match:
            print(f"🎯 POTENTIAL MATCH:")
        
        print(f"Name: {name}")
        print(f"ID: {customer_id}")
        
        if company:
            print(f"Company: {company}")
        
        print(f"Status: {'Active' if active else 'Inactive'}")
        
        if is_match:
            print(f"💡 This might match a Notion client!")
        
        print("-" * 30)
    
    print(f"\n📝 NEXT STEPS:")
    print(f"1. Copy the relevant Customer IDs above")
    print(f"2. Update your Notion Clients database:")
    print(f"   - ABA client → QB Customer ID field")
    print(f"   - HumanGood client → QB Customer ID field")
    
    if environment == "sandbox":
        print(f"3. ⚠️  Remember: These are SANDBOX IDs for testing only")
        print(f"4. You'll need PRODUCTION IDs when going live")


def main():
    """Main function."""
    print("🚀 QuickBooks Customer ID Fetcher")
    print("=" * 40)
    
    # Load credentials
    credentials = load_credentials()
    client_id = credentials.get('INTUIT_CLIENT_ID')
    client_secret = credentials.get('INTUIT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing CLIENT_ID or CLIENT_SECRET in credentials.config")
        sys.exit(1)
    
    print(f"✅ Loaded credentials from credentials.config")
    print(f"📱 Client ID: {client_id[:8]}...")
    
    # Get access token and realm ID
    access_token = get_access_token(client_id, client_secret)
    realm_id = get_realm_id()
    
    # Detect environment
    env_info = detect_environment(access_token, realm_id)
    
    # Fetch customers
    customers = fetch_customers(env_info['base_url'], access_token, realm_id)
    
    # Display results
    if customers:
        display_customers(customers, env_info['name'])
        
        # Save to file
        output_file = f"customers_{env_info['name']}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'environment': env_info['name'],
                'base_url': env_info['base_url'],
                'realm_id': realm_id,
                'customers': customers
            }, f, indent=2)
        
        print(f"\n💾 Data saved to: {output_file}")
    else:
        print("\n❌ No customers retrieved")


if __name__ == "__main__":
    main()