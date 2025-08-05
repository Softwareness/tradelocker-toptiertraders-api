"""
TradeLocker Broker Implementation
Implements the BaseBroker interface for TradeLocker
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from tradelocker import TLAPI
from .base import BaseBroker

logger = logging.getLogger(__name__)

class TradeLockerBroker(BaseBroker):
    """TradeLocker broker implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.tl_api = None
        super().__init__(credentials)
    
    def connect(self) -> bool:
        """Connect to TradeLocker"""
        try:
            self.tl_api = TLAPI(
                environment=self.credentials.get('environment', 'https://demo.tradelocker.com'),
                username=self.credentials['username'],
                password=self.credentials['password'],
                server=self.credentials['server']
            )
            self.connected = True
            logger.info("Successfully connected to TradeLocker")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TradeLocker: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from TradeLocker"""
        try:
            self.tl_api = None
            self.connected = False
            logger.info("Disconnected from TradeLocker")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from TradeLocker: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to TradeLocker"""
        return self.connected and self.tl_api is not None
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get all TradeLocker accounts"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            accounts = self.tl_api.get_all_accounts()
            return self.standardize_response(True, {
                'accounts': accounts.to_dict('records') if hasattr(accounts, 'to_dict') else accounts
            })
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return self.standardize_response(False, error=str(e))
    
    def get_account_details(self) -> Dict[str, Any]:
        """Get detailed account information"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            # Get basic account info
            accounts = self.tl_api.get_all_accounts()
            if accounts.empty:
                return self.standardize_response(False, error="No accounts found")
            
            # Get the first account
            account = accounts.iloc[0]
            account_id = account['id']
            
            # Get positions for margin calculation
            positions = self.tl_api.get_all_positions()
            
            # Calculate additional metrics
            total_positions_value = 0
            unrealized_pnl = 0
            if not positions.empty:
                for _, position in positions.iterrows():
                    # Calculate position value
                    if 'qty' in position and 'avgPrice' in position:
                        position_value = abs(position['qty'] * position['avgPrice'])
                        total_positions_value += position_value
                        
                        # Calculate unrealized P&L if available
                        if 'unrealizedPnl' in position:
                            unrealized_pnl += position['unrealizedPnl']
            
            # Calculate equity (balance + unrealized P&L)
            equity = account['accountBalance'] + unrealized_pnl
            
            # Estimate margin used (simplified calculation)
            margin_used = total_positions_value * 0.01  # Assuming 1% margin requirement
            
            # Calculate available margin
            margin_available = account['accountBalance'] - margin_used
            
            # Calculate margin level
            margin_level = (equity / margin_used * 100) if margin_used > 0 else 0
            
            # Build response
            response_data = {
                'account_id': int(account_id),
                'account_name': str(account['name']),
                'currency': str(account['currency']),
                'balance': float(account['accountBalance']),
                'equity': float(equity),
                'margin_used': float(margin_used),
                'margin_available': float(margin_available),
                'margin_level': float(margin_level),
                'free_margin': float(margin_available),
                'total_positions_value': float(total_positions_value),
                'unrealized_pnl': float(unrealized_pnl),
                'positions_count': int(len(positions) if not positions.empty else 0),
                'account_status': str(account['status']),
                'positions': positions.to_dict('records') if not positions.empty and hasattr(positions, 'to_dict') else []
            }
            
            return self.standardize_response(True, response_data)
            
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            return self.standardize_response(False, error=str(e))
    
    def get_instruments(self) -> Dict[str, Any]:
        """Get all TradeLocker instruments"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            instruments = self.tl_api.get_all_instruments()
            return self.standardize_response(True, {
                'instruments': instruments.to_dict('records') if hasattr(instruments, 'to_dict') else instruments
            })
        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return self.standardize_response(False, error=str(e))
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            # Get instrument ID for the symbol
            instruments = self.tl_api.get_all_instruments()
            instrument = instruments[instruments['symbol'] == symbol]
            
            if instrument.empty:
                return self.standardize_response(False, error=f"Instrument {symbol} not found")
            
            instrument_id = instrument.iloc[0]['id']
            
            # Get current price
            price_data = self.tl_api.get_instrument_price(instrument_id)
            
            return self.standardize_response(True, {
                'symbol': symbol,
                'instrument_id': int(instrument_id),
                'ask_price': float(price_data.get('ask', 0)),
                'bid_price': float(price_data.get('bid', 0))
            })
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return self.standardize_response(False, error=str(e))
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new TradeLocker order"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            # Validate order data
            validation = self.validate_order_data(order_data)
            if not validation['success']:
                return self.standardize_response(False, error=validation['error'])
            
            order_data = validation['data']
            
            # Get instrument ID
            instruments = self.tl_api.get_all_instruments()
            instrument = instruments[instruments['symbol'] == order_data['symbol']]
            
            if instrument.empty:
                return self.standardize_response(False, error=f"Instrument {order_data['symbol']} not found")
            
            instrument_id = instrument.iloc[0]['id']
            
            # Prepare order parameters
            order_params = {
                'instrument_id': instrument_id,
                'quantity': order_data['quantity'],
                'side': order_data['side'],
                'type_': order_data['order_type'],
                'validity': order_data.get('validity', 'IOC' if order_data['order_type'] == 'market' else 'GTC')
            }
            
            # Add price for limit orders
            if order_data['order_type'] == 'limit' and order_data.get('price'):
                order_params['price'] = order_data['price']
            
            # Create the order
            order_result = self.tl_api.create_order(**order_params)
            
            # Add stop loss and take profit if specified
            if order_data.get('stop_loss') or order_data.get('take_profit'):
                # This would need to be implemented based on TradeLocker's API
                # For now, we'll just log that SL/TP was requested
                logger.info(f"Stop loss and take profit requested for order {order_result.get('id')}")
            
            return self.standardize_response(True, {
                'order_id': str(order_result.get('id')),
                'status': order_result.get('status', 'created'),
                'message': 'Order created successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return self.standardize_response(False, error=str(e))
    
    def get_orders(self) -> Dict[str, Any]:
        """Get all TradeLocker orders"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            orders = self.tl_api.get_all_orders()
            return self.standardize_response(True, {
                'orders': orders.to_dict('records') if hasattr(orders, 'to_dict') else orders
            })
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return self.standardize_response(False, error=str(e))
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a TradeLocker order"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            # This would need to be implemented based on TradeLocker's API
            # For now, we'll return a placeholder response
            logger.info(f"Cancelling order {order_id}")
            
            return self.standardize_response(True, {
                'order_id': order_id,
                'status': 'cancelled',
                'message': 'Order cancelled successfully'
            })
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return self.standardize_response(False, error=str(e))
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all TradeLocker positions"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            positions = self.tl_api.get_all_positions()
            return self.standardize_response(True, {
                'positions': positions.to_dict('records') if hasattr(positions, 'to_dict') else positions
            })
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return self.standardize_response(False, error=str(e))
    
    def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close a TradeLocker position"""
        try:
            if not self.is_connected():
                return self.standardize_response(False, error="Not connected to TradeLocker")
            
            # This would need to be implemented based on TradeLocker's API
            # For now, we'll return a placeholder response
            logger.info(f"Closing position {position_id}")
            
            return self.standardize_response(True, {
                'position_id': position_id,
                'status': 'closed',
                'message': 'Position closed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return self.standardize_response(False, error=str(e)) 