#!/usr/bin/env python3
"""
QuickBooks Data Fetcher
Fetches customer IDs and service/item IDs from QuickBooks API for invoice automation setup.
"""

import json
import requests
from typing import Dict, List, Optional
import os
import sys
from datetime import datetime


class QuickBooksClient:
    def __init__(self, config_path: str = "config.json"):
        """Initialize QuickBooks client with config file."""
        self.config = self._load_config(config_path)
        self.qb_config = self.config['quickbooks']
        self.base_url = self.qb_config['baseUrl']
        self.realm_id = self.qb_config['realmId']
        
        # Set up headers for API requests
        self.headers = {
            'Authorization': f"Bearer {self.qb_config['accessToken']}",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            print(f"💡 Copy config.example.json to {config_path} and add your credentials")
            sys.exit(1)
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def _make_request(self, endpoint: str) -> Dict:
        """Make authenticated request to QuickBooks API."""
        url = f"{self.base_url}/v3/company/{self.realm_id}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {}
    
    def get_customers(self) -> List[Dict]:
        """Fetch all customers from QuickBooks."""
        print("📋 Fetching customers...")
        
        response = self._make_request("query?query=SELECT * FROM Customer")
        
        if 'QueryResponse' in response and 'Customer' in response['QueryResponse']:
            customers = response['QueryResponse']['Customer']
            print(f"✅ Found {len(customers)} customers")
            return customers
        else:
            print("⚠️ No customers found")
            return []
    
    def get_items(self) -> List[Dict]:
        """Fetch all items/services from QuickBooks."""
        print("🛍️ Fetching items/services...")
        
        response = self._make_request("query?query=SELECT * FROM Item WHERE Active = true")
        
        if 'QueryResponse' in response and 'Item' in response['QueryResponse']:
            items = response['QueryResponse']['Item']
            print(f"✅ Found {len(items)} active items/services")
            return items
        else:
            print("⚠️ No items found")
            return []
    
    def format_customers(self, customers: List[Dict]) -> None:
        """Print formatted customer information."""
        print("\n" + "="*60)
        print("💼 CUSTOMERS")
        print("="*60)
        
        for customer in customers:
            print(f"Name: {customer.get('Name', 'N/A')}")
            print(f"ID: {customer.get('Id', 'N/A')}")
            if 'CompanyName' in customer:
                print(f"Company: {customer['CompanyName']}")
            if customer.get('Active', True):
                print("Status: Active")
            else:
                print("Status: Inactive")
            print("-" * 30)
    
    def format_items(self, items: List[Dict]) -> None:
        """Print formatted item information."""
        print("\n" + "="*60)
        print("🛍️ ITEMS/SERVICES")
        print("="*60)
        
        for item in items:
            print(f"Name: {item.get('Name', 'N/A')}")
            print(f"ID: {item.get('Id', 'N/A')}")
            print(f"Type: {item.get('Type', 'N/A')}")
            if 'Description' in item:
                print(f"Description: {item['Description']}")
            if 'UnitPrice' in item:
                print(f"Unit Price: ${item['UnitPrice']}")
            print("-" * 30)
    
    def save_to_file(self, customers: List[Dict], items: List[Dict]) -> None:
        """Save fetched data to JSON file for reference."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"qb_data_{timestamp}.json"
        
        data = {
            "fetched_at": datetime.now().isoformat(),
            "environment": self.qb_config['environment'],
            "customers": customers,
            "items": items
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Data saved to: {filename}")
    
    def find_notion_clients(self, customers: List[Dict]) -> None:
        """Help map customers to Notion clients."""
        print("\n" + "="*60)
        print("🎯 MAPPING TO NOTION CLIENTS")
        print("="*60)
        
        # Known Notion clients from validation
        notion_clients = ["ABA", "HumanGood", "Humangood"]
        
        print("Looking for these Notion clients in QuickBooks:")
        for notion_client in notion_clients:
            print(f"\n🔍 Searching for: {notion_client}")
            found = False
            
            for customer in customers:
                customer_name = customer.get('Name', '').lower()
                company_name = customer.get('CompanyName', '').lower()
                
                if (notion_client.lower() in customer_name or 
                    notion_client.lower() in company_name):
                    print(f"   ✅ MATCH: {customer.get('Name')} (ID: {customer.get('Id')})")
                    if 'CompanyName' in customer:
                        print(f"      Company: {customer['CompanyName']}")
                    found = True
            
            if not found:
                print(f"   ❌ No match found - may need to create test customer")


def main():
    """Main function to fetch and display QuickBooks data."""
    print("🚀 QuickBooks Data Fetcher")
    print("=" * 40)
    
    # Initialize client
    qb_client = QuickBooksClient()
    
    print(f"🌍 Environment: {qb_client.qb_config['environment']}")
    print(f"🏢 Company ID: {qb_client.realm_id}")
    print()
    
    # Fetch data
    customers = qb_client.get_customers()
    items = qb_client.get_items()
    
    # Display formatted results
    if customers:
        qb_client.format_customers(customers)
        qb_client.find_notion_clients(customers)
    
    if items:
        qb_client.format_items(items)
    
    # Save to file
    if customers or items:
        qb_client.save_to_file(customers, items)
    
    print(f"\n✅ Complete! Use the IDs above to update your Notion database.")


if __name__ == "__main__":
    main()