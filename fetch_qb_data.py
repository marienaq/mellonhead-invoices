#!/usr/bin/env python3
"""
Fetch QuickBooks customers and items using credentials.config
"""

import os
import requests
import json


def load_credentials():
    """Load all credentials from credentials.config."""
    credentials = {}
    with open("credentials.config", 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()
    return credentials


def test_connection(base_url, headers, realm_id):
    """Test if we can connect to QuickBooks."""
    url = f"{base_url}/v3/company/{realm_id}/query"
    params = {'query': 'SELECT * FROM Customer MAXRESULTS 1'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return "Connected"
        return None
    except:
        return None


def fetch_customers(base_url, headers, realm_id):
    """Fetch all customers."""
    url = f"{base_url}/v3/company/{realm_id}/query"
    params = {'query': 'SELECT * FROM Customer'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if 'QueryResponse' in data and 'Customer' in data['QueryResponse']:
            return data['QueryResponse']['Customer']
        return []
    except Exception as e:
        print(f"❌ Error fetching customers: {e}")
        return []


def fetch_items(base_url, headers, realm_id):
    """Fetch all items/services."""
    url = f"{base_url}/v3/company/{realm_id}/query"
    params = {'query': 'SELECT * FROM Item WHERE Active = true'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if 'QueryResponse' in data and 'Item' in data['QueryResponse']:
            return data['QueryResponse']['Item']
        return []
    except Exception as e:
        print(f"❌ Error fetching items: {e}")
        return []


def main():
    """Main function."""
    print("🚀 QuickBooks Data Fetcher")
    print("=" * 50)
    
    # Load credentials
    creds = load_credentials()
    access_token = creds.get('INTUIT_ACCESS_TOKEN')
    realm_id = creds.get('INTUIT_REALM_ID')
    
    if not access_token or not realm_id:
        print("❌ Missing credentials in credentials.config")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Test sandbox first, then production
    environments = [
        ("SANDBOX", "https://sandbox-quickbooks.api.intuit.com"),
        ("PRODUCTION", "https://quickbooks.api.intuit.com")
    ]
    
    connected_env = None
    company_name = None
    
    for env_name, base_url in environments:
        print(f"\n🔍 Testing {env_name}...")
        company = test_connection(base_url, headers, realm_id)
        if company:
            print(f"✅ Connected to {env_name}: {company}")
            connected_env = (env_name, base_url)
            company_name = company
            break
        else:
            print(f"❌ Failed to connect to {env_name}")
    
    if not connected_env:
        print("\n❌ Could not connect to any environment")
        return
    
    env_name, base_url = connected_env
    
    # Fetch data
    print(f"\n📋 Fetching data from {env_name}...")
    customers = fetch_customers(base_url, headers, realm_id)
    items = fetch_items(base_url, headers, realm_id)
    
    # Display customers
    if customers:
        print(f"\n" + "="*60)
        print(f"💼 CUSTOMERS ({len(customers)} found)")
        print("="*60)
        
        for customer in customers:
            name = customer.get('Name', 'N/A')
            customer_id = customer.get('Id', 'N/A')
            active = customer.get('Active', True)
            
            print(f"Name: {name}")
            print(f"ID: {customer_id}")
            print(f"Status: {'Active' if active else 'Inactive'}")
            print("-" * 30)
    
    # Display items
    if items:
        print(f"\n" + "="*60)
        print(f"🛍️ ITEMS/SERVICES ({len(items)} found)")
        print("="*60)
        
        for item in items:
            name = item.get('Name', 'N/A')
            item_id = item.get('Id', 'N/A')
            item_type = item.get('Type', 'N/A')
            
            print(f"Name: {name}")
            print(f"ID: {item_id}")
            print(f"Type: {item_type}")
            
            if 'UnitPrice' in item:
                print(f"Unit Price: ${item['UnitPrice']}")
            
            print("-" * 30)
    
    # Save results
    output = {
        'environment': env_name,
        'company_name': company_name,
        'realm_id': realm_id,
        'customers': customers,
        'items': items
    }
    
    filename = f"qb_data_{env_name.lower()}.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Data saved to: {filename}")
    print(f"\n🎯 SUMMARY:")
    print(f"   Environment: {env_name}")
    print(f"   Company: {company_name}")
    print(f"   Customers: {len(customers)}")
    print(f"   Items: {len(items)}")


if __name__ == "__main__":
    main()