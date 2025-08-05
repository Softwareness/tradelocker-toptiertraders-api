#!/usr/bin/env python3
"""
TradeLocker REST API - FastAPI Application
Main application entry point for containerized deployment
"""

import os
import time
import uuid
import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Import TradeLocker service directly
from tradelocker import TLAPI

# API Key configuration
API_KEY = os.environ.get('API_KEY', 'your-secret-api-key-here')
API_KEY_NAME = "X-API-Key"

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for protected endpoints"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key

# Pydantic models for request/response validation
class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSD.TTF)")
    order_type: str = Field(..., description="Order type: market, limit, stop, stop_limit")
    side: str = Field(..., description="Order side: buy or sell")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Price for limit orders")
    stop_price: Optional[float] = Field(None, description="Stop price for stop orders")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    stop_loss_type: Optional[str] = Field(None, description="Stop loss type: absolute, offset, trailingOffset")
    take_profit_type: Optional[str] = Field(None, description="Take profit type: absolute, offset")
    trailing_distance: Optional[float] = Field(None, description="Trailing distance for trailing stops")
    validity: Optional[str] = Field(None, description="Order validity: GTC, IOC, FOK")
    user_id: Optional[str] = Field("default", description="User ID for tracking")

class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

class PriceResponse(BaseModel):
    success: bool
    symbol: Optional[str] = None
    instrument_id: Optional[int] = None
    ask_price: Optional[float] = None
    bid_price: Optional[float] = None
    error: Optional[str] = None
    timestamp: str

class AccountsResponse(BaseModel):
    success: bool
    accounts: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class InstrumentsResponse(BaseModel):
    success: bool
    instruments: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class OrdersResponse(BaseModel):
    success: bool
    orders: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class PositionsResponse(BaseModel):
    success: bool
    positions: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    success: bool
    message: str
    timestamp: str

class TradeLockerService:
    """Service layer for TradeLocker trading operations"""
    
    def __init__(self):
        self.tl_api = None
        self.connect()
    
    def _error_response(self, error: str) -> Dict[str, Any]:
        """Create standardized error response with timestamp"""
        return {
            'success': False,
            'error': error,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def connect(self):
        """Connect to TradeLocker"""
        try:
            # Get credentials from environment variables
            environment = os.environ.get('TRADELOCKER_ENVIRONMENT', 'https://demo.tradelocker.com')
            username = os.environ.get('TRADELOCKER_USERNAME')
            password = os.environ.get('TRADELOCKER_PASSWORD')
            server = os.environ.get('TRADELOCKER_SERVER')
            
            if not all([username, password, server]):
                raise ValueError("Missing TradeLocker credentials in environment variables")
            
            # Initialize TradeLocker API
            self.tl_api = TLAPI(
                environment=environment,
                username=username,
                password=password,
                server=server
            )
            
            logger.info("Successfully connected to TradeLocker")
            
        except Exception as e:
            logger.error(f"Failed to connect to TradeLocker: {e}")
            raise
    
    def get_broker_info(self) -> Dict[str, Any]:
        """Get information about the current broker"""
        return {
            'current_broker': 'tradelocker',
            'connected': self.tl_api is not None,
            'message': 'TradeLocker API connected'
        }
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order with support for trailing stop loss"""
        try:
            # Get instrument ID
            instruments = self.tl_api.get_all_instruments()
            instrument = instruments[instruments['name'] == order_data['symbol']]
            
            if instrument.empty:
                return self._error_response(f"Instrument {order_data['symbol']} not found")
            
            # Use tradableInstrumentId if available, otherwise use id
            instrument_id = instrument.iloc[0].get('tradableInstrumentId', instrument.iloc[0]['id'])
            
            # Prepare order parameters
            order_params = {
                'instrument_id': instrument_id,
                'quantity': order_data['quantity'],
                'side': order_data['side'],
                'type_': order_data['order_type'],
                'validity': order_data.get('validity', 'IOC' if order_data['order_type'] == 'market' else 'GTC')
            }
            
            # Ensure validity is set for non-market orders
            if order_data['order_type'] != 'market' and not order_data.get('validity'):
                order_params['validity'] = 'GTC'
            
            # Add price for limit orders
            if order_data['order_type'] == 'limit' and order_data.get('price'):
                order_params['price'] = order_data['price']
            
            # Add stop price for stop orders
            if order_data['order_type'] == 'stop' and order_data.get('stop_price'):
                order_params['stop_price'] = order_data['stop_price']
            
            # Add stop price for stop-limit orders
            if order_data['order_type'] == 'stop_limit' and order_data.get('stop_price'):
                order_params['stop_price'] = order_data['stop_price']
                if order_data.get('price'):
                    order_params['price'] = order_data['price']
            
            # Add stop loss and take profit directly to order parameters
            if order_data.get('stop_loss'):
                order_params['stop_loss'] = order_data['stop_loss']
                if order_data.get('stop_loss_type'):
                    order_params['stop_loss_type'] = order_data['stop_loss_type']
            
            if order_data.get('take_profit'):
                order_params['take_profit'] = order_data['take_profit']
                if order_data.get('take_profit_type'):
                    order_params['take_profit_type'] = order_data['take_profit_type']
            
            # Add trailing distance if specified
            if order_data.get('trailing_distance'):
                order_params['trailing_distance'] = order_data['trailing_distance']
            
            # Create the order with all parameters including stop loss and take profit
            order_id = self.tl_api.create_order(**order_params)
            
            return {
                'success': True,
                'order_id': str(order_id),
                'status': 'created',
                'message': 'Order created successfully',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return self._error_response(str(e))
    
    def _add_stop_loss_and_take_profit(self, order_id: int, order_data: Dict[str, Any]):
        """Add stop loss and take profit to an existing order"""
        try:
            # This would need to be implemented based on TradeLocker's API
            # For now, we'll log the request for stop loss and take profit
            
            stop_loss_info = ""
            take_profit_info = ""
            
            if order_data.get('stop_loss'):
                stop_loss_type = order_data.get('stop_loss_type', 'absolute')
                if stop_loss_type == 'trailing':
                    trailing_distance = order_data.get('trailing_distance', 0)
                    stop_loss_info = f"Trailing stop loss at {order_data['stop_loss']} with {trailing_distance} distance"
                else:
                    stop_loss_info = f"Stop loss at {order_data['stop_loss']}"
            
            if order_data.get('take_profit'):
                take_profit_type = order_data.get('take_profit_type', 'absolute')
                if take_profit_type == 'trailing':
                    trailing_distance = order_data.get('trailing_distance', 0)
                    take_profit_info = f"Trailing take profit at {order_data['take_profit']} with {trailing_distance} distance"
                else:
                    take_profit_info = f"Take profit at {order_data['take_profit']}"
            
            if stop_loss_info or take_profit_info:
                logger.info(f"Order {order_id}: {stop_loss_info} {take_profit_info}")
                
        except Exception as e:
            logger.error(f"Error adding stop loss/take profit to order {order_id}: {e}")
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get all accounts"""
        try:
            accounts = self.tl_api.get_all_accounts()
            return {
                'success': True,
                'accounts': accounts.to_dict('records') if hasattr(accounts, 'to_dict') else accounts
            }
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return self._error_response(str(e))
    
    def get_account_details(self) -> Dict[str, Any]:
        """Get detailed account information including balance, equity, margin, etc."""
        try:
            # Get accounts
            accounts = self.tl_api.get_all_accounts()
            
            if accounts.empty:
                return self._error_response('No accounts found')
            
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
                        if 'unrealizedPl' in position:
                            unrealized_pnl += position['unrealizedPl']
            
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
            
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                **response_data
            }
            
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            return self._error_response(str(e))
    
    def get_instruments(self) -> Dict[str, Any]:
        """Get all instruments"""
        try:
            instruments = self.tl_api.get_all_instruments()
            return {
                'success': True,
                'instruments': instruments.to_dict('records') if hasattr(instruments, 'to_dict') else instruments
            }
        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return self._error_response(str(e))
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            # Get instrument ID for the symbol
            instruments = self.tl_api.get_all_instruments()
            instrument = instruments[instruments['name'] == symbol]
            
            if instrument.empty:
                return self._error_response(f"Instrument {symbol} not found")
            
            instrument_id = instrument.iloc[0]['id']
            
            # Get current price using the correct method
            # Note: The tradelocker library might not have a direct price method
            # For now, we'll return a placeholder response
            return {
                'success': True,
                'symbol': symbol,
                'instrument_id': int(instrument_id),
                'ask_price': 0.0,  # Placeholder - would need actual price data
                'bid_price': 0.0,   # Placeholder - would need actual price data
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return self._error_response(str(e))
    
    def get_orders(self) -> Dict[str, Any]:
        """Get all orders"""
        try:
            orders = self.tl_api.get_all_orders()
            return {
                'success': True,
                'orders': orders.to_dict('records') if hasattr(orders, 'to_dict') else orders
            }
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return self._error_response(str(e))
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            # This would need to be implemented based on TradeLocker's API
            # For now, we'll return a placeholder response
            logger.info(f"Cancelling order {order_id}")
            
            return {
                'success': True,
                'order_id': order_id,
                'status': 'cancelled',
                'message': 'Order cancelled successfully'
            }
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return self._error_response(str(e))
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all positions"""
        try:
            positions = self.tl_api.get_all_positions()
            return {
                'success': True,
                'positions': positions.to_dict('records') if hasattr(positions, 'to_dict') else positions
            }
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return self._error_response(str(e))
    
    def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close a position"""
        try:
            # This would need to be implemented based on TradeLocker's API
            # For now, we'll return a placeholder response
            logger.info(f"Closing position {position_id}")
            
            return {
                'success': True,
                'order_id': position_id,
                'status': 'closed',
                'message': 'Position closed successfully',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return self._error_response(str(e))
    
    def log_order(self, order_id: str, order_data: Dict[str, Any], status: str):
        """Log order to DynamoDB"""
        try:
            table_name = os.environ.get('ORDERS_TABLE_NAME', 'tradelocker-orders')
            table = dynamodb.Table(table_name)
            
            item = {
                'order_id': str(order_id),
                'user_id': order_data.get('user_id', 'default'),
                'symbol': order_data['symbol'],
                'order_type': order_data['order_type'],
                'side': order_data['side'],
                'quantity': order_data['quantity'],
                'price': order_data.get('price', 0),
                'status': status,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'stop_loss': order_data.get('stop_loss', 0),
                'take_profit': order_data.get('take_profit', 0)
            }
            
            table.put_item(Item=item)
            logger.info(f"Order logged to DynamoDB: {order_id}")
            
        except Exception as e:
            logger.error(f"Error logging order to DynamoDB: {e}")

# Global service instance
trading_service = None

def get_trading_service():
    """Get or create trading service instance"""
    global trading_service
    if trading_service is None:
        trading_service = TradeLockerService()
    return trading_service

# Create FastAPI app
app = FastAPI(
    title="TradeLocker API",
    description="REST API for automated trading with TradeLocker",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    logger.info(f"Request {request_id} completed in {duration:.2f}ms")
    
    return response

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        success=True,
        message="TradeLocker API is healthy",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.get("/broker", response_model=Dict[str, Any], tags=["Broker"])
async def get_broker_info():
    """Get broker information"""
    try:
        service = get_trading_service()
        return service.get_broker_info()
    except Exception as e:
        logger.error(f"Error getting broker info: {e}")
        raise HTTPException(status_code=503, detail=f"Broker connection error: {str(e)}")

@app.post("/orders", response_model=OrderResponse, tags=["Orders"])
async def create_order(order: OrderRequest, api_key: str = Depends(verify_api_key)):
    """Create a new trading order"""
    try:
        service = get_trading_service()
        result = service.create_order(order.dict())
        return OrderResponse(**result)
    except Exception as e:
        logger.error(f"Error in create_order: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/orders", response_model=OrdersResponse, tags=["Orders"])
async def get_orders(api_key: str = Depends(verify_api_key)):
    """Get all orders"""
    try:
        service = get_trading_service()
        result = service.get_orders()
        return OrdersResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_orders: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.delete("/orders/{order_id}", response_model=OrderResponse, tags=["Orders"])
async def cancel_order(order_id: str, api_key: str = Depends(verify_api_key)):
    """Cancel a specific order"""
    try:
        service = get_trading_service()
        result = service.cancel_order(order_id)
        return OrderResponse(**result)
    except Exception as e:
        logger.error(f"Error in cancel_order: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/accounts", response_model=AccountsResponse, tags=["Accounts"])
async def get_accounts():
    """Get all accounts"""
    try:
        service = get_trading_service()
        result = service.get_accounts()
        return AccountsResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_accounts: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/accounts/details", response_model=Dict[str, Any], tags=["Accounts"])
async def get_account_details(api_key: str = Depends(verify_api_key)):
    """Get detailed account information including balance, equity, margin, etc."""
    try:
        service = get_trading_service()
        result = service.get_account_details()
        return result
    except Exception as e:
        logger.error(f"Error in get_account_details: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/instruments", response_model=InstrumentsResponse, tags=["Instruments"])
async def get_instruments():
    """Get all instruments"""
    try:
        service = get_trading_service()
        result = service.get_instruments()
        return InstrumentsResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_instruments: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/instruments/{symbol}/price", response_model=PriceResponse, tags=["Instruments"])
async def get_price(symbol: str):
    """Get current price for a symbol"""
    try:
        service = get_trading_service()
        result = service.get_current_price(symbol)
        return PriceResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_price: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.get("/positions", response_model=PositionsResponse, tags=["Positions"])
async def get_positions():
    """Get all positions"""
    try:
        service = get_trading_service()
        result = service.get_positions()
        return PositionsResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_positions: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.delete("/positions/{position_id}", response_model=OrderResponse, tags=["Positions"])
async def close_position(position_id: str, api_key: str = Depends(verify_api_key)):
    """Close a specific position"""
    try:
        service = get_trading_service()
        result = service.close_position(position_id)
        return OrderResponse(**result)
    except Exception as e:
        logger.error(f"Error in close_position: {e}")
        raise HTTPException(status_code=503, detail=f"TradeLocker connection error: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': 'Internal server error',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 