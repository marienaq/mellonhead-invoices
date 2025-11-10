#!/usr/bin/env python3
"""
QuickBooks Authentication Manager
Handles token refresh, validation, and retry logic for QuickBooks API calls
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class QuickBooksAuthManager:
    """Manages QuickBooks OAuth tokens with automatic refresh and retry logic."""
    
    def __init__(self, credentials_file: str = "credentials.config"):
        self.credentials_file = credentials_file
        self.credentials = self._load_credentials()
        self.base_url = "https://sandbox-quickbooks.api.intuit.com"  # Will be configurable
        self.token_endpoint = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
    def _load_credentials(self) -> Dict[str, str]:
        """Load credentials from config file."""
        credentials = {}
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
            
        with open(self.credentials_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()
        return credentials
    
    def _save_credentials(self):
        """Save updated credentials back to config file."""
        with open(self.credentials_file, 'w') as f:
            for key, value in self.credentials.items():
                f.write(f"{key}={value}\n")
    
    def _is_token_expired(self) -> bool:
        """Check if access token is likely expired (QuickBooks tokens expire in 1 hour)."""
        token_timestamp = self.credentials.get('TOKEN_TIMESTAMP')
        if not token_timestamp:
            return True
            
        try:
            token_time = datetime.fromisoformat(token_timestamp)
            # Consider token expired if it's more than 55 minutes old (5-minute buffer)
            return datetime.now() - token_time > timedelta(minutes=55)
        except (ValueError, TypeError):
            return True
    
    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        Handles expired access tokens, expired refresh tokens, invalid grants, and CSRF errors.
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        refresh_token = self.credentials.get('INTUIT_REFRESH_TOKEN')
        client_id = self.credentials.get('INTUIT_CLIENT_ID')
        client_secret = self.credentials.get('INTUIT_CLIENT_SECRET')
        
        if not all([refresh_token, client_id, client_secret]):
            print("❌ Missing required credentials for token refresh")
            return False
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Basic {self._get_basic_auth(client_id, client_secret)}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        try:
            print("🔄 Refreshing QuickBooks access token...")
            response = requests.post(self.token_endpoint, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update credentials with new tokens
                self.credentials['INTUIT_ACCESS_TOKEN'] = token_data['access_token']
                self.credentials['INTUIT_REFRESH_TOKEN'] = token_data['refresh_token']
                self.credentials['TOKEN_TIMESTAMP'] = datetime.now().isoformat()
                
                # Save to file
                self._save_credentials()
                
                print("✅ Token refreshed successfully")
                return True
            else:
                # Handle specific QuickBooks certification scenarios
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                
                error_type = error_data.get('error', 'unknown_error')
                error_description = error_data.get('error_description', response.text)
                
                if response.status_code == 400:
                    if error_type == 'invalid_grant':
                        print("❌ INVALID GRANT ERROR: Refresh token is expired or invalid")
                        print("   → Manual re-authorization required through QuickBooks OAuth flow")
                        print("   → This typically happens after 101 days of inactivity")
                        # Clear invalid tokens to prevent retry loops
                        self.credentials['INTUIT_REFRESH_TOKEN'] = 'EXPIRED'
                        self._save_credentials()
                        return False
                    elif 'expired' in error_description.lower():
                        print("❌ EXPIRED REFRESH TOKEN: Refresh token has expired")
                        print("   → Manual re-authorization required")
                        return False
                elif response.status_code == 401:
                    print("❌ UNAUTHORIZED: Invalid client credentials or token")
                    return False
                elif response.status_code == 403:
                    print("❌ CSRF ERROR: Cross-Site Request Forgery protection triggered")
                    print("   → Check request headers and origin")
                    return False
                elif response.status_code >= 500:
                    print(f"❌ SERVER ERROR ({response.status_code}): QuickBooks service issue")
                    print("   → Temporary issue, retry may succeed")
                    return False
                else:
                    print(f"❌ Token refresh failed: {response.status_code}")
                    print(f"   Error: {error_type}")
                    print(f"   Description: {error_description}")
                    return False
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT ERROR: Request to QuickBooks took too long")
            print("   → Network issue, retry may succeed")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ CONNECTION ERROR: Unable to connect to QuickBooks")
            print("   → Check internet connection")
            return False
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR during token refresh: {e}")
            return False
    
    def _get_basic_auth(self, client_id: str, client_secret: str) -> str:
        """Generate base64 encoded basic auth string."""
        import base64
        auth_string = f"{client_id}:{client_secret}"
        return base64.b64encode(auth_string.encode()).decode()
    
    def get_valid_headers(self) -> Optional[Dict[str, str]]:
        """
        Get valid authorization headers, refreshing token if necessary.
        
        Returns:
            Dict with valid headers, or None if unable to get valid token
        """
        # Check if token needs refresh
        if self._is_token_expired():
            if not self.refresh_access_token():
                print("❌ Unable to refresh expired token")
                return None
        
        access_token = self.credentials.get('INTUIT_ACCESS_TOKEN')
        if not access_token:
            print("❌ No access token available")
            return None
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def make_authenticated_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make an authenticated request with automatic retry on auth failures.
        Handles expired access tokens, invalid grants, and CSRF errors.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL for the request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if all retries failed
        """
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            headers = self.get_valid_headers()
            if not headers:
                print(f"❌ Unable to get valid headers (attempt {attempt + 1})")
                if attempt < max_retries:
                    continue
                return None
            
            # Merge with any existing headers
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
            kwargs['headers'] = headers
            
            try:
                # Set timeout to handle hanging requests
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 30
                
                response = requests.request(method, url, **kwargs)
                
                # Handle QuickBooks certification error scenarios
                if response.status_code == 401:
                    if attempt < max_retries:
                        print(f"🔄 EXPIRED ACCESS TOKEN: Attempting refresh (attempt {attempt + 1})")
                        # Force refresh by clearing timestamp
                        self.credentials['TOKEN_TIMESTAMP'] = '2020-01-01T00:00:00'
                        continue
                    else:
                        print("❌ PERSISTENT 401 ERROR: Access token refresh failed")
                        print("   → Manual re-authorization may be required")
                
                elif response.status_code == 403:
                    print("❌ CSRF ERROR: Cross-Site Request Forgery protection triggered")
                    print("   → Check request headers, user agent, and referrer")
                    return response  # Don't retry CSRF errors
                
                elif response.status_code >= 500:
                    if attempt < max_retries:
                        print(f"🔄 SERVER ERROR ({response.status_code}): Retrying... (attempt {attempt + 1})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        print(f"❌ PERSISTENT SERVER ERROR ({response.status_code}): QuickBooks service issue")
                
                return response
                
            except requests.exceptions.Timeout:
                print(f"❌ TIMEOUT ERROR: Request took too long (attempt {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ CONNECTION ERROR: Unable to connect to QuickBooks (attempt {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                    
            except Exception as e:
                print(f"❌ REQUEST EXCEPTION (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
        
        print("❌ All request attempts failed")
        return None
    
    def validate_connection(self) -> bool:
        """
        Test the QuickBooks connection with current credentials.
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        realm_id = self.credentials.get('INTUIT_REALM_ID')
        if not realm_id:
            print("❌ Missing INTUIT_REALM_ID")
            return False
        
        # Test with a simple company info query
        test_url = f"{self.base_url}/v3/company/{realm_id}/companyinfo/{realm_id}"
        
        response = self.make_authenticated_request('GET', test_url)
        
        if response and response.status_code == 200:
            print("✅ QuickBooks connection validated")
            return True
        else:
            status = response.status_code if response else "No response"
            print(f"❌ QuickBooks connection failed: {status}")
            return False
    
    def set_production_mode(self, production: bool = True):
        """Switch between sandbox and production environments."""
        if production:
            self.base_url = "https://quickbooks.api.intuit.com"
            print("🚀 Switched to production environment")
        else:
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
            print("🧪 Switched to sandbox environment")
    
    def requires_manual_reauth(self) -> bool:
        """
        Check if manual re-authorization is required.
        This happens when refresh tokens are expired or invalid.
        
        Returns:
            bool: True if OAuth playground re-authorization is needed
        """
        refresh_token = self.credentials.get('INTUIT_REFRESH_TOKEN', '')
        
        # Check for obvious invalid states
        if not refresh_token or refresh_token == 'EXPIRED':
            return True
        
        # Try a test refresh to see if token is valid
        if self._is_token_expired():
            print("🔍 Testing refresh token validity...")
            if not self.refresh_access_token():
                return True
        
        return False
    
    def get_reauth_instructions(self) -> str:
        """
        Get instructions for manual re-authorization.
        
        Returns:
            str: Formatted instructions for re-authorization
        """
        client_id = self.credentials.get('INTUIT_CLIENT_ID', 'YOUR_CLIENT_ID')
        is_production = 'quickbooks.api.intuit.com' in self.base_url
        
        environment = "Production" if is_production else "Sandbox"
        oauth_url = "https://developer.intuit.com/app/developer/oauth2playground"
        
        instructions = f"""
🔑 MANUAL RE-AUTHORIZATION REQUIRED

Your QuickBooks tokens have expired and need to be refreshed manually.

📋 STEPS TO RE-AUTHORIZE:
1. Visit the OAuth 2.0 Playground: {oauth_url}
2. Select "{environment}" environment
3. Enter your Client ID: {client_id}
4. Click "Connect to QuickBooks"
5. Authorize your application
6. Copy the new Access Token and Refresh Token
7. Update your credentials.config file
8. Add current timestamp: TOKEN_TIMESTAMP={datetime.now().isoformat()}

⚠️  NOTE: This typically happens after 101 days of inactivity.
💡 TIP: Set up a monthly reminder to run your automation to keep tokens fresh.
        """
        
        return instructions


def example_usage():
    """Example of how to use the auth manager."""
    try:
        # Initialize auth manager
        auth = QuickBooksAuthManager()
        
        # Test connection
        if not auth.validate_connection():
            print("Connection failed - check credentials")
            return
        
        # Example API call using the auth manager
        realm_id = auth.credentials['INTUIT_REALM_ID']
        customers_url = f"{auth.base_url}/v3/company/{realm_id}/query?query=SELECT * FROM Customer"
        
        response = auth.make_authenticated_request('GET', customers_url)
        
        if response and response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data.get('QueryResponse', {}).get('Customer', []))} customers")
        else:
            print("❌ Failed to retrieve customers")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    example_usage()