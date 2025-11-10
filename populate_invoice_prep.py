#!/usr/bin/env python3
"""
Populate Monthly Invoice Prep database and generate QuickBooks invoices
Usage: python populate_invoice_prep.py --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12
"""

import os
import requests
import json
import argparse
from datetime import datetime, timedelta
from qb_auth_manager import QuickBooksAuthManager


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


def get_notion_headers():
    """Get headers for Notion API requests."""
    creds = load_credentials()
    notion_token = creds.get('NOTION_TOKEN')
    
    if not notion_token:
        raise ValueError("NOTION_TOKEN not found in credentials.config")
    
    return {
        'Authorization': f'Bearer {notion_token}',
        'Content-Type': 'application/json',
        'Notion-Version': '2022-06-28'
    }


def fetch_notion_client_data(debug=False):
    """Fetch client configuration from Notion Clients database using Notion API."""
    if debug:
        print("📋 Fetching client configuration from Notion Clients database...")
    
    headers = get_notion_headers()
    creds = load_credentials()
    
    # Query the Clients database for Active clients
    database_id = creds.get('NOTION_COMPANIES_DB')
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    # Filter for Active clients only
    query_data = {
        "filter": {
            "property": "Client Status",
            "status": {
                "equals": "Active"
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=query_data)
        response.raise_for_status()
        
        data = response.json()
        clients = {}
        
        for result in data.get('results', []):
            properties = result['properties']
            
            # Extract client data from Notion properties
            client_name = properties.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Unknown')
            
            # Process retainer service IDs (multi_select field)
            retainer_service_items = properties.get('Retainer Service IDs', {}).get('multi_select', [])
            services = {}
            retainer_service_ids = []
            
            # Extract QB service IDs from multi_select items
            for item in retainer_service_items:
                qb_id = item.get('name', '')
                if qb_id:
                    retainer_service_ids.append(qb_id)
                    # Create service entry with QB ID (QuickBooks will provide the amount)
                    services[f'Service_{qb_id}'] = {
                        'amount': 0,  # Will be set by QuickBooks based on service ID
                        'qb_id': qb_id
                    }
            
            retainer_service_ids_str = ','.join(retainer_service_ids)
            
            client_data = {
                'client_page_url': result['url'],
                'qb_customer_id': properties.get('QB Customer ID', {}).get('rich_text', [{}])[0].get('plain_text', ''),
                'monthly_retainer_hours': properties.get('Monthly Retainer Hours', {}).get('number', 0),
                'overage_rate': properties.get('Overage Rate', {}).get('number', 0),
                'retainer_rate': properties.get('Retainer Rate', {}).get('number', 0),
                'overage_sku': properties.get('Overage SKU', {}).get('rich_text', [{}])[0].get('plain_text', ''),
                'retainer_service_ids': retainer_service_ids_str,
                'services': services
            }
            
            clients[client_name] = client_data
            
            if debug:
                print(f"   • {client_name}: {client_data['monthly_retainer_hours']} hrs retainer, ${client_data['overage_rate']}/hr overage")
                print(f"     Retainer Service IDs: '{retainer_service_ids_str}'")
                print(f"     Services: {list(services.keys())}")
                print(f"     Overage SKU: '{client_data['overage_sku']}'")
        
        if debug:
            print(f"   Found {len(clients)} active clients")
        
        return clients
        
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"   Error fetching client data: {e}")
        raise


def extract_client_from_title(title_text):
    """Extract client name from time entry title like 'work for ABA' or 'work for TWG'."""
    title_lower = title_text.lower()
    if 'for aba' in title_lower:
        return 'ABA'
    elif 'for twg' in title_lower:
        return 'TWG'
    elif 'for humangood' in title_lower:
        return 'Humangood'
    return None


def fetch_notion_time_entries(start_date, end_date, debug=False):
    """Fetch time entries from Notion Time Tracking database for date range using Notion API."""
    if debug:
        print(f"⏱️  Fetching time entries from {start_date} to {end_date}...")
    
    headers = get_notion_headers()
    creds = load_credentials()
    
    # Query the Time Tracking database for entries in date range
    database_id = creds.get('NOTION_CLIENT_HOURS_DB')
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    
    # Filter by date range
    query_data = {
        "filter": {
            "and": [
                {
                    "property": "Date",
                    "date": {
                        "on_or_after": start_date
                    }
                },
                {
                    "property": "Date", 
                    "date": {
                        "on_or_before": end_date
                    }
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=query_data)
        response.raise_for_status()
        
        data = response.json()
        client_entries = {}
        
        for result in data.get('results', []):
            properties = result['properties']
            
            # Extract time entry data
            date_prop = properties.get('Date', {}).get('date', {})
            entry_date = date_prop.get('start', '') if date_prop else ''
            
            hours_worked = properties.get('Hours', {}).get('number', 0)
            
            # Get client name from relation or fallback to title extraction
            client_relation = properties.get('Client', {}).get('relation', [])
            if client_relation:
                # Resolve client name from relation ID
                client_id = client_relation[0]['id']
                client_name = resolve_client_name_from_id(client_id, headers, debug)
            else:
                # Fallback: extract client name from title
                title_prop = properties.get('Title', {}).get('title', [])
                title_text = title_prop[0].get('plain_text', '') if title_prop else ''
                client_name = extract_client_from_title(title_text)
                if not client_name:
                    if debug:
                        print(f"   Warning: Could not determine client for entry: {title_text}")
                    continue
            
            notes = properties.get('Description', {}).get('rich_text', [{}])[0].get('plain_text', '')
            
            # Group by client
            if client_name not in client_entries:
                client_entries[client_name] = []
            
            client_entries[client_name].append({
                'date': entry_date,
                'hours': hours_worked,
                'description': notes
            })
        
        # Calculate totals per client
        client_totals = {}
        for client_name, entries in client_entries.items():
            total_hours = sum(entry['hours'] for entry in entries)
            client_totals[client_name] = {
                'entries': entries,
                'total_hours': total_hours
            }
            
            if debug:
                print(f"   {client_name}: {total_hours} hours ({len(entries)} entries)")
        
        if debug:
            print(f"   Found {len(client_totals)} clients with time entries")
        
        return client_totals
        
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"   Error fetching time entries: {e}")
        raise


def resolve_client_name_from_id(client_id, headers, debug=False):
    """Resolve client name from Notion page ID."""
    url = f"https://api.notion.com/v1/pages/{client_id}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        properties = data.get('properties', {})
        
        # Get the Name property (title)
        name_prop = properties.get('Name', {}).get('title', [])
        if name_prop:
            return name_prop[0].get('plain_text', 'Unknown')
        
        return 'Unknown'
        
    except Exception as e:
        if debug:
            print(f"   Warning: Could not resolve client name for ID {client_id}: {e}")
        return 'Unknown'


def calculate_client_billing_data(clients_config, time_data, debug=False):
    """Calculate billing data by combining client config with actual time entries."""
    if debug:
        print(f"\\n🧮 Calculating billing data...")
    
    billing_data = {}
    
    for client_name, config in clients_config.items():
        time_info = time_data.get(client_name, {'entries': [], 'total_hours': 0})
        
        # Calculate overages
        actual_hours = time_info['total_hours']
        retainer_hours = config['monthly_retainer_hours']
        overage_hours = max(0, actual_hours - retainer_hours)
        overage_amount = overage_hours * config['overage_rate']
        
        billing_data[client_name] = {
            **config,  # Include all client config
            'time_entries': time_info['entries'],
            'actual_hours': actual_hours,
            'overage_hours': overage_hours,
            'overage_amount': overage_amount,
            'under_retainer_hours': max(0, retainer_hours - actual_hours) if actual_hours < retainer_hours else 0
        }
        
        if debug:
            status = "OVERAGE" if overage_hours > 0 else "UNDER" if actual_hours < retainer_hours else "EXACT"
            print(f"   {client_name}: {actual_hours}hrs actual vs {retainer_hours}hrs retainer → {status}")
    
    return billing_data


def get_client_data_from_notion(start_date, end_date, debug=False):
    """Main function to get client data by querying Notion databases."""
    if debug:
        print(f"\\n📊 FETCHING DATA FROM NOTION")
        print(f"   Date range: {start_date} to {end_date}")
    
    # Step 1: Get client configuration 
    clients_config = fetch_notion_client_data(debug)
    
    # Step 2: Get time entries for date range
    time_data = fetch_notion_time_entries(start_date, end_date, debug)
    
    # Step 3: Calculate billing data
    billing_data = calculate_client_billing_data(clients_config, time_data, debug)
    
    if debug:
        print_client_debug_info(billing_data)
    
    return billing_data


def print_client_debug_info(clients):
    """Print detailed debug information for each client."""
    print(f"\\n" + "=" * 100)
    print("🔍 DETAILED CLIENT DEBUG BREAKDOWN")
    print("=" * 100)
    
    grand_total = 0
    
    for client_name, data in clients.items():
        print(f"\\n🏢 {client_name.upper()}")
        print("-" * 60)
        
        # Client configuration
        print("📋 CLIENT CONFIGURATION:")
        print(f"   Monthly Retainer Hours: {data['monthly_retainer_hours']} hrs")
        print(f"   Retainer Rate: ${data['retainer_rate']:,.2f}/month")
        print(f"   Overage Rate: ${data['overage_rate']}/hr")
        print(f"   QB Customer ID: {data['qb_customer_id']}")
        
        # Fixed services
        print("\\n🛍️  FIXED SERVICES:")
        total_services = 0
        for service_name, service_data in data['services'].items():
            print(f"   • {service_name}: ${service_data['amount']:,} (QB ID: {service_data['qb_id']})")
            total_services += service_data['amount']
        
        # Time tracking data
        print(f"\\n⏱️  TIME ENTRIES:")
        if data['time_entries']:
            for entry in data['time_entries']:
                print(f"   {entry['date']}: {entry['hours']} hrs - {entry['description']}")
            print(f"   {'─' * 50}")
            print(f"   TOTAL: {data['actual_hours']} hrs")
        else:
            print(f"   Total hours: {data['actual_hours']} hrs (no detailed entries)")
            
        # Overage calculations
        print(f"\\n💰 OVERAGE CALCULATION:")
        print(f"   Retainer allocation: {data['monthly_retainer_hours']} hrs")
        print(f"   Actual hours worked: {data['actual_hours']} hrs")
        
        if data['overage_hours'] > 0:
            print(f"   ✅ OVERAGE: {data['overage_hours']} hrs")
            print(f"   Overage calculation: {data['overage_hours']} × ${data['overage_rate']} = ${data['overage_amount']:,.2f}")
        elif data['under_retainer_hours'] > 0:
            print(f"   ⬇️  UNDER RETAINER: {data['under_retainer_hours']} hrs unused")
            print(f"   Overage amount: $0")
        else:
            print(f"   ✅ EXACT MATCH: Used exactly {data['monthly_retainer_hours']} hrs")
            print(f"   Overage amount: $0")
            
        # Expected invoice
        print(f"\\n🧾 EXPECTED INVOICE:")
        for service_name, service_data in data['services'].items():
            print(f"   • {service_name}: ${service_data['amount']:,}")
        
        if data['overage_amount'] > 0:
            print(f"   • Hourly Overages: ${data['overage_amount']:,} ({data['overage_hours']} hrs)")
            
        invoice_total = total_services + data['overage_amount']
        print(f"   {'─' * 50}")
        print(f"   CLIENT TOTAL: ${invoice_total:,}")
        grand_total += invoice_total
    
    print(f"\\n" + "=" * 100)
    print(f"💰 GRAND TOTAL ALL CLIENTS: ${grand_total:,}")
    print("=" * 100)


def create_invoice_prep_records(time_data, overage_month, bill_month, invoice_date):
    """Create Monthly Invoice Prep records for specified retainer and overage periods.
    
    Args:
        time_data: Dictionary of client time data
        overage_month (str): Month being billed for overages (YYYY-MM format)
        bill_month (str): Month being billed for retainer (YYYY-MM format) 
        invoice_date (str): Invoice date in YYYY-MM-DD format
    """
    print(f"📝 Creating Monthly Invoice Prep records...")
    print(f"   Retainer period: {bill_month}")
    print(f"   Overage period: {overage_month}")
    print(f"   Invoice date: {invoice_date}")
    
    # Data source ID for Monthly Invoice Prep database
    creds = load_credentials()
    prep_db_id = creds.get('NOTION_MONTHLY_PREP_DB')
    
    records_to_create = []
    
    for client_name, data in time_data.items():
        # 1. Current month Retainer record (always create)
        retainer_record = {
            "properties": {
                "Title": f"{client_name} {bill_month} Retainer",
                "Client": f'["{data["client_page_url"]}"]',  # JSON array format for relation
                "Client Hours": '[]',  # Empty for retainer, will populate for overages
                "Billing Month": bill_month,
                "Billing Type": "Current Retainer",
                "date:Invoice Date:start": invoice_date,
                "date:Invoice Date:is_datetime": 0
            }
        }
        records_to_create.append(retainer_record)
        
        # 2. Previous month Overage record (only if client exceeded retainer) 
        overage_hours = max(0, data['actual_hours'] - data['monthly_retainer_hours'])
        if overage_hours > 0:
            overage_record = {
                "properties": {
                    "Title": f"{client_name} {overage_month} Overage", 
                    "Client": f'["{data["client_page_url"]}"]',
                    "Client Hours": json.dumps(data['time_entries']),  # JSON array of time entry URLs
                    "Billing Month": overage_month,
                    "Billing Type": "Previous Overage",
                    "date:Invoice Date:start": invoice_date,
                    "date:Invoice Date:is_datetime": 0
                }
            }
            records_to_create.append(overage_record)
            print(f"   ✅ {client_name}: Retainer + Overage ({overage_hours} hrs)")
        else:
            print(f"   ✅ {client_name}: Retainer only (no overages)")
    
    # TODO: Use Notion MCP to create these records
    # For now, just return the data structure that would be created
    return records_to_create


def convert_client_data_to_prep_records(client_data, bill_month, overage_month):
    """Convert client billing data to invoice prep records format.
    
    Args:
        client_data (dict): Client data from Notion with billing calculations
        bill_month (str): Month being billed for retainer (YYYY-MM format)
        overage_month (str): Month being billed for overages (YYYY-MM format)
    """
    prep_records = []
    
    for client_name, data in client_data.items():
        # Add retainer services
        for service_name, service_info in data.get('services', {}).items():
            # Convert YYYY-MM to "Month YYYY" format for description
            bill_month_formatted = datetime.strptime(bill_month + '-01', '%Y-%m-%d').strftime('%B %Y')
            prep_records.append({
                'title': f'{client_name} {bill_month} {service_name}',
                'client': client_name,
                'client_id': data['qb_customer_id'],
                'billing_type': 'Current Retainer',
                'qb_service_id': service_info['qb_id'],
                'invoice_description': f'Services for {bill_month_formatted}'
            })
        
        # Add overage if client exceeded retainer hours
        if data.get('overage_amount', 0) > 0:
            # Convert YYYY-MM to "Month YYYY" format for description
            overage_month_formatted = datetime.strptime(overage_month + '-01', '%Y-%m-%d').strftime('%B %Y')
            prep_records.append({
                'title': f'{client_name} {overage_month} Overage',
                'client': client_name,
                'client_id': data['qb_customer_id'],
                'billing_type': 'Previous Overage',
                'qb_service_id': data['overage_sku'],
                'invoice_amount': data['overage_amount'],
                'invoice_description': f'Services for {overage_month_formatted} ({data["overage_hours"]} hrs overage)'
            })
    
    return prep_records


def group_by_client_for_invoicing(prep_data):
    """Group Monthly Invoice Prep records by client for consolidated invoices."""
    client_invoices = {}
    
    for record in prep_data:
        client = record['client']
        if client not in client_invoices:
            client_invoices[client] = {
                'client_id': record['client_id'],
                'line_items': []
            }
        client_invoices[client]['line_items'].append(record)
    
    return client_invoices


def fetch_qb_service_price(service_id, auth_manager):
    """Fetch service price from QuickBooks API."""
    realm_id = auth_manager.credentials.get('INTUIT_REALM_ID')
    url = f"{auth_manager.base_url}/v3/company/{realm_id}/item/{service_id}"
    
    try:
        response = auth_manager.make_authenticated_request('GET', url)
        if response and response.status_code == 200:
            data = response.json()
            item = data.get('Item', {})
            return item.get('UnitPrice', 0)
        else:
            status = response.status_code if response else "No response"
            print(f"   Warning: Could not fetch price for service {service_id}: HTTP {status}")
            return 0
        
    except Exception as e:
        print(f"   Warning: Could not fetch price for service {service_id}: {e}")
        return 0


def create_qb_invoice_from_prep(client_name, client_data, auth_manager):
    """Create QuickBooks invoice from Monthly Invoice Prep data."""
    realm_id = auth_manager.credentials.get('INTUIT_REALM_ID')
    
    # Convert prep data to QB line items
    line_items = []
    for item in client_data['line_items']:
        # Use QB service ID from Notion data
        qb_item_id = item.get('qb_service_id', '1')  # Default to generic service if not specified
        
        line_item = {
            'DetailType': 'SalesItemLineDetail',
            'SalesItemLineDetail': {
                'ItemRef': {'value': qb_item_id},
                'Qty': 1
            },
            'Description': item['invoice_description']
        }
        
        # Add amount - either from overage calculation or fetch from QB service
        if item['billing_type'] == 'Previous Overage' and 'invoice_amount' in item:
            line_item['Amount'] = item['invoice_amount']
            line_item['SalesItemLineDetail']['UnitPrice'] = item['invoice_amount']
        else:
            # For retainer services, fetch price from QuickBooks
            service_price = fetch_qb_service_price(qb_item_id, auth_manager)
            if service_price > 0:
                line_item['Amount'] = service_price
                line_item['SalesItemLineDetail']['UnitPrice'] = service_price
            else:
                # Fallback if we can't fetch the price
                line_item['Amount'] = 0.01
        
        line_items.append(line_item)
    
    total_amount = sum(item.get('Amount', 0) for item in line_items)
    
    invoice_data = {
        'CustomerRef': {'value': client_data['client_id']},
        'TxnDate': '2025-11-09',  # Today's date
        'DueDate': '2025-12-09',  # 30 days from today
        'Line': line_items,
        'CustomerMemo': {'value': 'Payment accepted via ACH or Wire. Contact billing@mellonhead.co for account and routing numbers.'}
    }
    
    url = f"{auth_manager.base_url}/v3/company/{realm_id}/invoice"
    
    try:
        print(f"\\n📧 Creating consolidated invoice for {client_name}...")
        print(f"   Customer ID: {client_data['client_id']}")
        print(f"   Line Items:")
        for i, item in enumerate(client_data['line_items'], 1):
            amount_str = f"${item['invoice_amount']}" if 'invoice_amount' in item else "QB will set amount"
            print(f"     {i}. {item['invoice_description']}: {amount_str}")
        print(f"   Total Amount: ${total_amount}")
        
        response = auth_manager.make_authenticated_request('POST', url, json=invoice_data)
        
        if response and response.status_code == 200:
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
            status = response.status_code if response else "No response"
            error_text = response.text if response else "Connection failed"
            print(f"   ❌ Error: {status}")
            print(f"   Response: {error_text}")
            return {'success': False, 'error': error_text}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {'success': False, 'error': str(e)}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Populate Monthly Invoice Prep database and generate QuickBooks invoices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Bill December retainer + October overages (invoice on Dec 15)
  python populate_invoice_prep.py --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12
  
  # Bill January retainer + November overages (invoice on Jan 15)  
  python populate_invoice_prep.py --overage-start 2025-11-01 --overage-end 2025-11-30 --bill-month 2026-01
  
  # Custom invoice date
  python populate_invoice_prep.py --overage-start 2025-10-01 --overage-end 2025-10-31 --bill-month 2025-12 --invoice-date 2025-12-20
        """
    )
    
    parser.add_argument('--overage-start', required=True, 
                       help='Start date for overage period (YYYY-MM-DD)')
    parser.add_argument('--overage-end', required=True,
                       help='End date for overage period (YYYY-MM-DD)')
    parser.add_argument('--bill-month', required=True,
                       help='Month to bill retainer for (YYYY-MM)')
    parser.add_argument('--invoice-date', 
                       help='Invoice date (YYYY-MM-DD). Default: 15th of bill month')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating QB invoices')
    parser.add_argument('--debug', action='store_true',
                       help='Show detailed breakdown of client data and calculations')
    parser.add_argument('--production', action='store_true',
                       help='Use production QuickBooks environment (default: sandbox)')
    
    return parser.parse_args()


def validate_date_inputs(args):
    """Validate and process date inputs."""
    try:
        # Validate date formats
        overage_start = datetime.strptime(args.overage_start, '%Y-%m-%d')
        overage_end = datetime.strptime(args.overage_end, '%Y-%m-%d')
        bill_month = datetime.strptime(args.bill_month + '-01', '%Y-%m-%d')
        
        # Validate overage period
        if overage_start > overage_end:
            raise ValueError("Overage start date must be before or equal to end date")
        
        # Set default invoice date if not provided
        if args.invoice_date:
            invoice_date = datetime.strptime(args.invoice_date, '%Y-%m-%d')
        else:
            # Default to 15th of bill month
            invoice_date = bill_month.replace(day=15)
        
        # Extract overage month for billing (YYYY-MM format)
        overage_month = overage_start.strftime('%Y-%m')
        
        return {
            'overage_start': args.overage_start,
            'overage_end': args.overage_end, 
            'overage_month': overage_month,
            'bill_month': args.bill_month,
            'invoice_date': invoice_date.strftime('%Y-%m-%d'),
            'dry_run': args.dry_run,
            'debug': args.debug,
            'production': args.production
        }
        
    except ValueError as e:
        print(f"❌ Date validation error: {e}")
        return None


def main():
    """Main function to populate Invoice Prep database and generate QB invoices."""
    # Parse command line arguments
    args = parse_arguments()
    dates = validate_date_inputs(args)
    
    if not dates:
        return 1
    
    print("🎯 Monthly Invoice Prep Population + QuickBooks Invoice Generation")
    print("=" * 80)
    print(f"📅 Overage period: {dates['overage_start']} to {dates['overage_end']}")
    print(f"📅 Retainer billing month: {dates['bill_month']}")
    print(f"📅 Invoice date: {dates['invoice_date']}")
    if dates['dry_run']:
        print("🔍 DRY RUN MODE - No QuickBooks invoices will be created")
    
    # Initialize QuickBooks authentication manager
    try:
        auth_manager = QuickBooksAuthManager()
        
        # Set production or sandbox mode
        auth_manager.set_production_mode(dates['production'])
        
        print("🔐 Initializing QuickBooks authentication...")
        
        # Check if manual re-authorization is required
        if auth_manager.requires_manual_reauth():
            print(auth_manager.get_reauth_instructions())
            return 1
        
        if not auth_manager.validate_connection():
            print("❌ QuickBooks authentication failed - check credentials")
            if auth_manager.requires_manual_reauth():
                print(auth_manager.get_reauth_instructions())
            return 1
        
        print("✅ QuickBooks authentication validated")
    except Exception as e:
        print(f"❌ Error initializing QuickBooks authentication: {e}")
        return 1
    
    # Step 1: Fetch client data and time tracking data from Notion  
    print(f"\\n📊 STEP 1: Fetching data from Notion...")
    client_data = get_client_data_from_notion(dates['overage_start'], dates['overage_end'], dates['debug'])
    print(f"Found data for {len(client_data)} clients")
    
    # Step 2: Create Monthly Invoice Prep records
    print("\\n📝 STEP 2: Creating Monthly Invoice Prep records...")
    prep_records = create_invoice_prep_records(
        client_data, 
        dates['overage_month'], 
        dates['bill_month'], 
        dates['invoice_date']
    )
    print(f"Created {len(prep_records)} invoice prep records")
    
    # Step 3: Process client data for invoice generation
    print("\\n📋 STEP 3: Processing client data for QuickBooks invoices...")
    # Convert client data to prep records format for invoicing
    populated_data = convert_client_data_to_prep_records(client_data, dates['bill_month'], dates['overage_month'])
    
    # Step 4: Group by client and generate QB invoices
    print("\\n🧾 STEP 4: Generating QuickBooks invoices...")
    client_invoices = group_by_client_for_invoicing(populated_data)
    
    results = {}
    if dates['dry_run']:
        # Simulate results for dry run
        for client_name in client_invoices.keys():
            results[client_name] = {
                'success': True,
                'invoice_number': 'DRY-RUN',
                'total_amount': sum(item.get('invoice_amount', 0) for item in client_invoices[client_name]['line_items'])
            }
            print(f"   🔍 Would create invoice for {client_name}: ${results[client_name]['total_amount']}")
    else:
        for client_name, client_data in client_invoices.items():
            result = create_qb_invoice_from_prep(client_name, client_data, auth_manager)
            results[client_name] = result
    
    # Summary
    print(f"\\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    successful = 0
    total_amount = 0
    
    for client_name, result in results.items():
        if result['success']:
            successful += 1
            total_amount += result['total_amount']
            if dates['dry_run']:
                print(f"🔍 {client_name}: Would invoice ${result['total_amount']}")
            else:
                print(f"✅ {client_name}: Invoice #{result['invoice_number']} - ${result['total_amount']}")
        else:
            print(f"❌ {client_name}: Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\\n🎯 Results: {successful}/{len(results)} invoices {'would be created' if dates['dry_run'] else 'created'}")
    print(f"💰 Total {'potential' if dates['dry_run'] else ''} amount: ${total_amount}")
    print(f"📝 Invoice prep records: {len(prep_records)}")
    
    if successful == len(results):
        if dates['dry_run']:
            print("\\n🔍 Dry run completed successfully!")
            print("💡 Run without --dry-run to create actual QuickBooks invoices")
        else:
            print("\\n🎉 Complete workflow successful!")
            print("💡 Next steps:")
            print("   1. Review draft invoices in QuickBooks sandbox")
            print("   2. Implement real Notion API calls to create prep records")
            print("   3. Set up n8n automation for monthly execution")
    else:
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)