"""
REST API Client Library
Simplifies API calls from PyQt5 clients
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class APIClient:
    """Client for REST API communication"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.token = None
        self.user_id = None
        self.username = None
        self.role = None
        self.session = requests.Session()
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUTHENTICATION
    # ─────────────────────────────────────────────────────────────────────────
    
    def login(self, username: str, password: str) -> bool:
        """Login user and store JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={'username': username, 'password': password},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                user_info = data.get('user', {})
                self.user_id = user_info.get('id')
                self.username = user_info.get('username')
                self.role = user_info.get('role')
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                })
                
                logger.info(f"User {username} logged in successfully")
                return True
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False
        
        except requests.RequestException as e:
            logger.error(f"Login request failed: {e}")
            return False
    
    def logout(self):
        """Logout user and clear token"""
        self.token = None
        self.user_id = None
        self.username = None
        self.role = None
        self.session.headers.pop('Authorization', None)
        logger.info("User logged out")
    
    def refresh_token(self) -> bool:
        """Refresh JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                logger.info("Token refreshed successfully")
                return True
            else:
                logger.error(f"Token refresh failed: {response.status_code}")
                return False
        
        except requests.RequestException as e:
            logger.error(f"Token refresh request failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.token is not None and self.user_id is not None
    
    # ─────────────────────────────────────────────────────────────────────────
    # GENERIC API METHODS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _handle_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """Handle API response"""
        try:
            if response.status_code == 401:
                logger.warning("Unauthorized - token may have expired")
                self.token = None
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Response handling error: {e}")
            return None
    
    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make GET request"""
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"GET request failed: {e}")
            return None
    
    def _post(self, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make POST request"""
        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"POST request failed: {e}")
            return None
    
    def _put(self, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make PUT request"""
        try:
            response = self.session.put(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"PUT request failed: {e}")
            return None
    
    def _delete(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make DELETE request"""
        try:
            response = self.session.delete(
                f"{self.base_url}{endpoint}",
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"DELETE request failed: {e}")
            return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # REPORTS API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_daily_reports(
        self,
        date_from: str = None,
        date_to: str = None,
        client_id: int = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch daily reports"""
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if client_id:
            params['client_id'] = client_id
        
        response = self._get('/api/v1/reports/daily', params)
        return response.get('data') if response and response.get('success') else None
    
    def get_report_summary(
        self,
        date_from: str = None,
        date_to: str = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch report summary"""
        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        response = self._get('/api/v1/reports/summary', params)
        return response.get('data') if response and response.get('success') else None
    
    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single report"""
        response = self._get(f'/api/v1/reports/{report_id}')
        return response.get('data') if response and response.get('success') else None
    
    def create_report(self, data: Dict[str, Any]) -> Optional[int]:
        """Create new report"""
        response = self._post('/api/v1/reports', data)
        return response.get('report_id') if response and response.get('success') else None
    
    def update_report(self, report_id: int, data: Dict[str, Any]) -> bool:
        """Update report"""
        response = self._put(f'/api/v1/reports/{report_id}', data)
        return response.get('success', False) if response else False
    
    def delete_report(self, report_id: int) -> bool:
        """Delete report"""
        response = self._delete(f'/api/v1/reports/{report_id}')
        return response.get('success', False) if response else False
    
    # ─────────────────────────────────────────────────────────────────────────
    # USERS API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get current user profile"""
        response = self._get('/api/v1/users/profile')
        return response.get('data') if response and response.get('success') else None
    
    def update_user_profile(self, data: Dict[str, Any]) -> bool:
        """Update user profile"""
        response = self._put('/api/v1/users/profile', data)
        return response.get('success', False) if response else False
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change user password"""
        response = self._post(
            '/api/v1/users/change-password',
            {'old_password': old_password, 'new_password': new_password}
        )
        return response.get('success', False) if response else False
    
    # ─────────────────────────────────────────────────────────────────────────
    # DATA API (Generic Table Access)
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_table_data(
        self,
        table_name: str,
        columns: List[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch data from any table"""
        params = {'limit': limit, 'offset': offset}
        if columns:
            params['columns'] = ','.join(columns)
        
        response = self._get(f'/api/v1/data/{table_name}', params)
        return response.get('data') if response and response.get('success') else None
    
    def insert_table_data(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert data into table"""
        response = self._post(f'/api/v1/data/{table_name}', data)
        return response.get('id') if response and response.get('success') else None
    
    def update_table_data(self, table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
        """Update table record"""
        response = self._put(f'/api/v1/data/{table_name}/{record_id}', data)
        return response.get('success', False) if response else False
    
    def delete_table_data(self, table_name: str, record_id: int) -> bool:
        """Delete table record"""
        response = self._delete(f'/api/v1/data/{table_name}/{record_id}')
        return response.get('success', False) if response else False
    
    # ─────────────────────────────────────────────────────────────────────────
    # TRANSACTIONS API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_transactions(
        self,
        date_from: str = None,
        date_to: str = None,
        client_id: int = None,
        transaction_type: str = None,
        limit: int = 100
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch transactions"""
        params = {'limit': limit}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if client_id:
            params['client_id'] = client_id
        if transaction_type:
            params['type'] = transaction_type
        
        response = self._get('/api/v1/transactions', params)
        return response.get('data') if response and response.get('success') else None
    
    def get_fund_transfers(
        self,
        status: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch fund transfers"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        
        response = self._get('/api/v1/transactions/fund-transfers', params)
        return response.get('data') if response and response.get('success') else None
    
    def create_fund_transfer(
        self,
        from_account: str,
        to_account: str,
        amount: float,
        transfer_date: str
    ) -> Optional[int]:
        """Create fund transfer"""
        data = {
            'from_account': from_account,
            'to_account': to_account,
            'amount': amount,
            'transfer_date': transfer_date
        }
        response = self._post('/api/v1/transactions/fund-transfers', data)
        return response.get('transfer_id') if response and response.get('success') else None
    
    def approve_fund_transfer(self, transfer_id: int) -> bool:
        """Approve fund transfer"""
        response = self._post(f'/api/v1/transactions/fund-transfers/{transfer_id}/approve')
        return response.get('success', False) if response else False
    
    def reject_fund_transfer(self, transfer_id: int, reason: str = None) -> bool:
        """Reject fund transfer"""
        data = {}
        if reason:
            data['reason'] = reason
        response = self._post(f'/api/v1/transactions/fund-transfers/{transfer_id}/reject', data)
        return response.get('success', False) if response else False
    
    # ─────────────────────────────────────────────────────────────────────────
    # HEALTH CHECK
    # ─────────────────────────────────────────────────────────────────────────
    
    def health_check(self) -> bool:
        """Check API and database health"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return False
