#!/usr/bin/env python3
"""
Test Invoice Generation Script
Generates December retainer + October overage invoices for all clients
"""

import os
import requests
import json
from datetime import datetime


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


def fetch_notion_time_data():
    """Simulate fetching October time tracking data from Notion."""
    # TODO: Replace with actual Notion API calls
    # For now, using sample data based on typical usage
    
    return {
        'ABA': {
            'client_id': '58',
            'retainer_hours': 10,
            'retainer_rate': 2000,
            'overage_rate': 300,
            'october_hours': 15,  # 5 hours over
            'services': {
                'AI Advisory': '19',
                'AI Champions Program': '21', 
                'AI Team Workshops 2 teams': '20'
            }
        },
        'HumanGood': {
            'client_id': '60',
            'retainer_hours': 20,
            'retainer_rate': 5000,
            'overage_rate': 300,
            'october_hours': 18,  # 0 hours over (under retainer)
            'services': {
                'Team Based Workshops 1 team': '22'
            }
        },
        'TWG': {
            'client_id': '59',
            'retainer_hours': 20,
            'retainer_rate': 4000,
            'overage_rate': 250,
            'october_hours': 25,  # 5 hours over
            'services': {
                'Instructional Design Hourly Block 20hr Prepay': '23'
            }
        }
    }


def calculate_line_items(client_name, client_data):
    """Calculate invoice line items for a client."""
    line_items = []
    
    # December Retainer (always included)
    line_items.append({
        'DetailType': 'SalesItemLineDetail',
        'Amount': client_data['retainer_rate'],
        'SalesItemLineDetail': {
            'ItemRef': {'value': '1'},  # Generic "Services" item
            'Qty': 1,
            'UnitPrice': client_data['retainer_rate'],
            'ServiceDate': '2025-12-01'
        },
        'Description': f'Monthly Retainer - December 2025'
    })
    
    # October Overages (only if client exceeded hours)
    overage_hours = max(0, client_data['october_hours'] - client_data['retainer_hours'])
    if overage_hours > 0:
        overage_amount = overage_hours * client_data['overage_rate']
        line_items.append({
            'DetailType': 'SalesItemLineDetail', 
            'Amount': overage_amount,
            'SalesItemLineDetail': {
                'ItemRef': {'value': '24'},  # Hourly Services Overage
                'Qty': overage_hours,
                'UnitPrice': client_data['overage_rate'],
                'ServiceDate': '2025-10-31'
            },
            'Description': f'Overage Hours - October 2025 ({overage_hours} hrs @ ${client_data["overage_rate"]}/hr)'
        })
    
    return line_items, overage_hours


def create_qb_invoice(client_name, client_data, line_items):
    """Create a QuickBooks draft invoice."""
    creds = load_credentials()
    access_token = creds.get('INTUIT_ACCESS_TOKEN')
    realm_id = creds.get('INTUIT_REALM_ID')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Calculate total amount
    total_amount = sum(item['Amount'] for item in line_items)
    
    invoice_data = {
        'CustomerRef': {'value': client_data['client_id']},
        'TxnDate': '2025-12-15',  # Invoice date (15th of month)
        'DueDate': '2026-01-15',  # Due date (30 days)
        'Line': line_items
    }
    
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice"
    
    try:
        print(f"\\n📧 Creating invoice for {client_name}...")
        print(f"   Customer ID: {client_data['client_id']}")
        print(f"   Total Amount: ${total_amount}")
        print(f"   Line Items: {len(line_items)}")
        
        response = requests.post(url, headers=headers, json=invoice_data)
        
        if response.status_code == 200:
            result = response.json()
            invoice = result['Invoice']
            invoice_id = invoice['Id']
            invoice_num = invoice['DocNumber']
            print(f"   ✅ Invoice created: #{invoice_num} (ID: {invoice_id})")
            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_num,
                'total_amount': total_amount
            }
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return {'success': False, 'error': response.text}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Main function to generate test invoices."""
    print("🧾 Test Invoice Generation - December Retainer + October Overages")
    print("=" * 70)
    
    # Fetch client data
    clients_data = fetch_notion_time_data()
    
    results = {}
    
    for client_name, client_data in clients_data.items():
        print(f"\\n🏢 Processing {client_name}")
        print(f"   Retainer: {client_data['retainer_hours']} hrs @ ${client_data['retainer_rate']}/month")
        print(f"   October actual: {client_data['october_hours']} hrs")
        
        # Calculate line items
        line_items, overage_hours = calculate_line_items(client_name, client_data)
        
        if overage_hours > 0:
            print(f"   Overage: {overage_hours} hrs @ ${client_data['overage_rate']}/hr")
        else:
            print(f"   No overages (under retainer by {client_data['retainer_hours'] - client_data['october_hours']} hrs)")
        
        # Create QuickBooks invoice
        result = create_qb_invoice(client_name, client_data, line_items)
        results[client_name] = result
    
    # Summary
    print(f"\\n" + "=" * 70)
    print("📊 INVOICE GENERATION SUMMARY")
    print("=" * 70)
    
    successful = 0
    total_amount = 0
    
    for client_name, result in results.items():
        if result['success']:
            successful += 1
            total_amount += result['total_amount']
            print(f"✅ {client_name}: Invoice #{result['invoice_number']} - ${result['total_amount']}")
        else:
            print(f"❌ {client_name}: Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\\n🎯 Results: {successful}/{len(results)} invoices created successfully")
    print(f"💰 Total invoiced amount: ${total_amount}")
    
    if successful == len(results):
        print("\\n🎉 All invoices generated successfully!")
        print("💡 Next: Review draft invoices in QuickBooks sandbox")
    else:
        print(f"\\n⚠️  {len(results) - successful} invoices failed - check errors above")


if __name__ == "__main__":
    main()