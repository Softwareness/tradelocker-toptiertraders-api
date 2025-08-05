"""
Base Broker Interface
Defines the common interface that all broker implementations must follow
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseBroker(ABC):
    """Base class for all broker implementations"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.connected = False
        self.connect()
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the broker"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the broker"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        pass
    
    @abstractmethod
    def get_accounts(self) -> Dict[str, Any]:
        """Get all accounts"""
        pass
    
    @abstractmethod
    def get_account_details(self) -> Dict[str, Any]:
        """Get detailed account information"""
        pass
    
    @abstractmethod
    def get_instruments(self) -> Dict[str, Any]:
        """Get all available instruments"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order"""
        pass
    
    @abstractmethod
    def get_orders(self) -> Dict[str, Any]:
        """Get all orders"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Any]:
        """Get all positions"""
        pass
    
    @abstractmethod
    def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close a position"""
        pass
    
    def validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data and return standardized format"""
        required_fields = ['symbol', 'order_type', 'side', 'quantity']
        missing_fields = [field for field in required_fields if field not in order_data]
        
        if missing_fields:
            return {
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Validate order types
        valid_order_types = ['market', 'limit', 'stop', 'stop_limit']
        if order_data.get('order_type') not in valid_order_types:
            return {
                'success': False,
                'error': f"Invalid order_type. Must be one of: {', '.join(valid_order_types)}"
            }
        
        # Validate sides
        valid_sides = ['buy', 'sell']
        if order_data.get('side') not in valid_sides:
            return {
                'success': False,
                'error': f"Invalid side. Must be one of: {', '.join(valid_sides)}"
            }
        
        # Validate quantity
        if order_data.get('quantity', 0) <= 0:
            return {
                'success': False,
                'error': "Quantity must be greater than 0"
            }
        
        return {'success': True, 'data': order_data}
    
    def standardize_response(self, success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
        """Standardize API responses"""
        response = {
            'success': success,
            'timestamp': self._get_timestamp()
        }
        
        if success and data:
            response.update(data)
        elif not success and error:
            response['error'] = error
            
        return response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat() 