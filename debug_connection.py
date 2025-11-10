#!/usr/bin/env python3
"""
Debug QuickBooks connection
"""

import requests


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


def test_simple_call():
    """Make a simple API call to test connection."""
    creds = load_credentials()
    access_token = creds.get('INTUIT_ACCESS_TOKEN')
    realm_id = creds.get('INTUIT_REALM_ID')
    
    print(f"🔍 Debug Info:")
    print(f"   Realm ID: {realm_id}")
    print(f"   Token length: {len(access_token) if access_token else 0}")
    print(f"   Token starts with: {access_token[:20] if access_token else 'None'}...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    # Try sandbox first with a simple customer query
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query"
    params = {'query': 'SELECT * FROM Customer MAXRESULTS 5'}
    
    print(f"\n📡 Making API call...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"Response keys: {list(data.keys())}")
            
            if 'QueryResponse' in data:
                if 'Customer' in data['QueryResponse']:
                    customers = data['QueryResponse']['Customer']
                    print(f"Found {len(customers)} customers")
                    for customer in customers[:3]:  # Show first 3
                        print(f"  - {customer.get('Name', 'No Name')} (ID: {customer.get('Id')})")
                else:
                    print("No customers found")
            
        else:
            print(f"❌ Error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    test_simple_call()