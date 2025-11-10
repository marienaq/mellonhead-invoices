#!/usr/bin/env python3
"""
Simple invoice creation test to debug QB API format
"""

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


def create_simple_invoice():
    """Create a minimal test invoice."""
    creds = load_credentials()
    access_token = creds.get('INTUIT_ACCESS_TOKEN')
    realm_id = creds.get('INTUIT_REALM_ID')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Minimal invoice structure based on QB API docs
    invoice_data = {
        'CustomerRef': {'value': '58'},  # ABA customer ID
        'Line': [{
            'DetailType': 'SalesItemLineDetail',
            'Amount': 2000.00,
            'SalesItemLineDetail': {
                'ItemRef': {'value': '1'},  # Services item
                'Qty': 1,
                'UnitPrice': 2000.00
            }
        }]
    }
    
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice"
    
    print("🧪 Testing minimal invoice creation...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(invoice_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=invoice_data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'QueryResponse' in result and 'Invoice' in result['QueryResponse']:
                invoice = result['QueryResponse']['Invoice'][0]
                print(f"✅ Success! Invoice ID: {invoice['Id']}, Number: {invoice.get('DocNumber', 'N/A')}")
            else:
                print(f"✅ Success! Response structure: {result.keys()}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    create_simple_invoice()