#!/usr/bin/env python3
"""
QuickBooks API Error Handler and Logger
Handles API errors, validation errors, response headers, and logging for QuickBooks certification
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests


class QuickBooksErrorHandler:
    """Handles QuickBooks API errors, logging, and response tracking for certification compliance."""
    
    def __init__(self, log_file: str = "qb_api.log"):
        self.log_file = log_file
        self.setup_logging()
        self.error_log = []
        
    def setup_logging(self):
        """Set up comprehensive logging for API interactions."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        log_path = f"logs/{self.log_file}"
        
        # Configure logging with detailed format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, mode='a', encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.logger = logging.getLogger('QuickBooksAPI')
        self.logger.info("="*80)
        self.logger.info("QuickBooks API session started")
        self.logger.info("="*80)
    
    def log_api_request(self, method: str, url: str, headers: Dict[str, str], 
                       data: Any = None, params: Dict[str, str] = None):
        """Log API request details for troubleshooting."""
        self.logger.info(f"API REQUEST: {method} {url}")
        
        # Log sanitized headers (remove authorization)
        safe_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
        safe_headers['Authorization'] = '[REDACTED]' if 'authorization' in [h.lower() for h in headers.keys()] else None
        self.logger.info(f"Request headers: {json.dumps(safe_headers, indent=2)}")
        
        if params:
            self.logger.info(f"Request params: {json.dumps(params, indent=2)}")
            
        if data:
            if isinstance(data, (dict, list)):
                self.logger.info(f"Request body: {json.dumps(data, indent=2)}")
            else:
                self.logger.info(f"Request body: {data}")
    
    def log_api_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Log API response details and extract important headers.
        Returns response analysis for certification compliance.
        """
        response_data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'timestamp': datetime.now().isoformat(),
            'url': response.url,
            'intuit_tid': response.headers.get('intuit_tid'),
            'content_type': response.headers.get('content-type'),
            'response_time_ms': getattr(response, 'elapsed', None)
        }
        
        self.logger.info(f"API RESPONSE: {response.status_code} from {response.url}")
        self.logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
        
        # Log intuit_tid for QuickBooks support troubleshooting
        if response_data['intuit_tid']:
            self.logger.info(f"INTUIT_TID (for QB support): {response_data['intuit_tid']}")
        
        # Log response body (safely)
        try:
            if response.text:
                response_json = response.json()
                self.logger.info(f"Response body: {json.dumps(response_json, indent=2)}")
                response_data['body'] = response_json
        except json.JSONDecodeError:
            # Log non-JSON responses safely
            body_preview = response.text[:500] + "..." if len(response.text) > 500 else response.text
            self.logger.info(f"Response body (non-JSON): {body_preview}")
            response_data['body'] = response.text
        except Exception as e:
            self.logger.warning(f"Could not log response body: {e}")
        
        return response_data
    
    def handle_api_error(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle and categorize QuickBooks API errors for certification compliance.
        Includes syntax errors, validation errors, and business logic errors.
        """
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'url': response.url,
            'intuit_tid': response.headers.get('intuit_tid'),
            'error_type': 'unknown',
            'error_category': 'unknown',
            'error_message': '',
            'troubleshooting_steps': [],
            'user_message': '',
            'retry_recommended': False
        }
        
        try:
            error_data = response.json()
            error_info['raw_error'] = error_data
        except:
            error_info['raw_error'] = response.text
            
        # Categorize errors based on status code and content
        if response.status_code == 400:
            error_info.update(self._handle_400_errors(response, error_info))
        elif response.status_code == 401:
            error_info.update(self._handle_401_errors(response, error_info))
        elif response.status_code == 403:
            error_info.update(self._handle_403_errors(response, error_info))
        elif response.status_code == 404:
            error_info.update(self._handle_404_errors(response, error_info))
        elif response.status_code == 429:
            error_info.update(self._handle_429_errors(response, error_info))
        elif response.status_code >= 500:
            error_info.update(self._handle_500_errors(response, error_info))
        
        # Log the error comprehensively
        self.logger.error(f"API ERROR: {error_info['error_type']} - {error_info['error_message']}")
        self.logger.error(f"Troubleshooting: {'; '.join(error_info['troubleshooting_steps'])}")
        if error_info['intuit_tid']:
            self.logger.error(f"Reference ID for QuickBooks support: {error_info['intuit_tid']}")
        
        # Store error for aggregation
        self.error_log.append(error_info)
        
        return error_info
    
    def _handle_400_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 400 Bad Request errors - typically syntax and validation errors."""
        try:
            error_data = response.json()
            fault = error_data.get('Fault', {})
            error = fault.get('Error', [{}])[0] if fault.get('Error') else {}
            
            error_code = error.get('code', '')
            error_detail = error.get('Detail', '')
            error_element = error.get('element', '')
            
            error_info.update({
                'error_type': 'validation_error',
                'error_category': 'client_error',
                'error_message': f"Validation Error: {error_detail}",
                'error_code': error_code,
                'error_element': error_element,
                'retry_recommended': False
            })
            
            # Specific handling for common validation errors
            if 'ValidationFault' in error_detail:
                error_info['troubleshooting_steps'] = [
                    'Check required fields are provided',
                    'Validate data types and formats',
                    'Ensure field values meet QuickBooks constraints',
                    'Review API documentation for field requirements'
                ]
                error_info['user_message'] = 'Invalid data provided. Please check your input and try again.'
                
            elif 'BusinessValidationFault' in error_detail:
                error_info['troubleshooting_steps'] = [
                    'Check business logic constraints',
                    'Verify entity relationships exist',
                    'Ensure account types are appropriate',
                    'Check for duplicate entries'
                ]
                error_info['user_message'] = 'Business rule violation. Please review the data and correct any conflicts.'
                
        except:
            error_info.update({
                'error_type': 'syntax_error',
                'error_category': 'client_error',
                'error_message': 'Bad Request - Syntax or validation error',
                'troubleshooting_steps': ['Check request syntax', 'Validate JSON format', 'Review API documentation'],
                'user_message': 'Request format error. Please check your data and try again.',
                'retry_recommended': False
            })
        
        return error_info
    
    def _handle_401_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 401 Unauthorized errors - authentication issues."""
        return {
            'error_type': 'authentication_error',
            'error_category': 'auth_error',
            'error_message': 'Unauthorized - Invalid or expired access token',
            'troubleshooting_steps': [
                'Check access token validity',
                'Refresh access token using refresh token',
                'Verify token has not expired',
                'Re-authorize if refresh token is expired'
            ],
            'user_message': 'Authentication failed. The system will attempt to refresh your credentials.',
            'retry_recommended': True
        }
    
    def _handle_403_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 403 Forbidden errors - authorization/CSRF issues."""
        return {
            'error_type': 'authorization_error',
            'error_category': 'auth_error', 
            'error_message': 'Forbidden - Insufficient permissions or CSRF error',
            'troubleshooting_steps': [
                'Verify app has required permissions',
                'Check CSRF protection headers',
                'Ensure proper referrer headers',
                'Validate user agent string'
            ],
            'user_message': 'Access denied. Please contact support if this persists.',
            'retry_recommended': False
        }
    
    def _handle_404_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 404 Not Found errors - resource issues."""
        return {
            'error_type': 'resource_not_found',
            'error_category': 'client_error',
            'error_message': 'Resource not found',
            'troubleshooting_steps': [
                'Verify resource ID is correct',
                'Check if resource exists in current company',
                'Ensure proper endpoint URL',
                'Verify company ID (realm_id) is correct'
            ],
            'user_message': 'The requested resource could not be found.',
            'retry_recommended': False
        }
    
    def _handle_429_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 429 Rate Limit errors."""
        retry_after = response.headers.get('Retry-After', '60')
        return {
            'error_type': 'rate_limit_exceeded',
            'error_category': 'rate_limit',
            'error_message': f'Rate limit exceeded - retry after {retry_after} seconds',
            'retry_after_seconds': int(retry_after),
            'troubleshooting_steps': [
                f'Wait {retry_after} seconds before retrying',
                'Implement exponential backoff',
                'Consider reducing request frequency',
                'Review rate limit quotas'
            ],
            'user_message': f'Request rate limit exceeded. Please wait {retry_after} seconds.',
            'retry_recommended': True
        }
    
    def _handle_500_errors(self, response: requests.Response, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 500+ Server errors."""
        return {
            'error_type': 'server_error',
            'error_category': 'server_error',
            'error_message': f'Server error ({response.status_code}) - QuickBooks service issue',
            'troubleshooting_steps': [
                'Retry request after brief delay',
                'Check QuickBooks service status',
                'Implement exponential backoff',
                'Contact QuickBooks support if persistent'
            ],
            'user_message': 'Temporary service issue. The system will retry automatically.',
            'retry_recommended': True
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered in this session."""
        if not self.error_log:
            return {'total_errors': 0, 'error_categories': {}}
        
        summary = {
            'total_errors': len(self.error_log),
            'error_categories': {},
            'intuit_tids': [err.get('intuit_tid') for err in self.error_log if err.get('intuit_tid')],
            'first_error': self.error_log[0]['timestamp'],
            'last_error': self.error_log[-1]['timestamp']
        }
        
        # Categorize errors
        for error in self.error_log:
            category = error['error_category']
            summary['error_categories'][category] = summary['error_categories'].get(category, 0) + 1
        
        return summary
    
    def get_support_info(self) -> str:
        """Get formatted support contact information."""
        error_summary = self.get_error_summary()
        intuit_tids = [tid for tid in error_summary.get('intuit_tids', []) if tid]
        
        support_info = f"""
🆘 SUPPORT CONTACT INFORMATION

📧 Primary Support: billing@mellonhead.co
📞 Emergency Contact: Available during business hours (9 AM - 5 PM PST)

🔍 ERROR TRACKING INFORMATION:
- Session errors: {error_summary['total_errors']}
- Log file: logs/{self.log_file}
"""
        
        if intuit_tids:
            support_info += f"""
🎫 QUICKBOOKS REFERENCE IDs (provide to QuickBooks support):
{chr(10).join(f'   • {tid}' for tid in intuit_tids[:5])}
{"   • ... and more (see log file)" if len(intuit_tids) > 5 else ""}
"""
        
        support_info += """
📋 WHEN CONTACTING SUPPORT:
1. Describe what you were trying to do
2. Include the timestamp when the error occurred
3. Provide any QuickBooks reference IDs listed above
4. Attach the log file if requested
5. Include your company/realm ID (if safe to share)

⚡ SELF-SERVICE TROUBLESHOOTING:
1. Check logs/qb_api.log for detailed error information
2. Verify your internet connection
3. Try the operation again (some errors are temporary)
4. For authentication errors, the system will guide you through re-authorization
        """
        
        return support_info


def create_error_handler() -> QuickBooksErrorHandler:
    """Factory function to create a standardized error handler."""
    return QuickBooksErrorHandler()


if __name__ == "__main__":
    # Test the error handler
    handler = QuickBooksErrorHandler()
    handler.logger.info("Error handler test completed")
    print("Error handler initialized successfully")
    print(handler.get_support_info())