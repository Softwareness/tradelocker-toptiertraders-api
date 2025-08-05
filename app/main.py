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

from fastapi import FastAPI, HTTPException, Request
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

# Import broker factory
from brokers.factory import BrokerFactory

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
    order_type: str = Field(..., description="Order type: market or limit")
    side: str = Field(..., description="Order side: buy or sell")
    quantity: float = Field(..., description="Order quantity")
    price: Optional[float] = Field(None, description="Price for limit orders")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
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

class TradingService:
    """Service layer for multi-broker trading operations"""
    
    def __init__(self):
        self.broker_factory = BrokerFactory()
        self.broker = None
        self.connect()
    
    def connect(self):
        """Connect to the configured broker"""
        try:
            broker_type = os.environ.get('BROKER_TYPE', 'tradelocker')
            self.broker = self.broker_factory.get_broker(broker_type)
            logger.info(f"Successfully connected to {broker_type}")
        except Exception as e:
            logger.error(f"Failed to connect to broker: {e}")
            raise
    
    def get_broker_info(self) -> Dict[str, Any]:
        """Get information about the current broker"""
        broker_type = os.environ.get('BROKER_TYPE', 'tradelocker')
        available_brokers = self.broker_factory.get_available_brokers()
        
        return {
            'current_broker': broker_type,
            'available_brokers': available_brokers,
            'connected': self.broker.is_connected() if self.broker else False
        }
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order"""
        try:
            result = self.broker.create_order(order_data)
            
            # Log to DynamoDB if successful
            if result.get('success') and result.get('order_id'):
                self.log_order(result['order_id'], order_data, 'created')
            
            return result
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get all accounts"""
        try:
            return self.broker.get_accounts()
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_details(self) -> Dict[str, Any]:
        """Get detailed account information including balance, equity, margin, etc."""
        try:
            return self.broker.get_account_details()
        except Exception as e:
            logger.error(f"Error getting account details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_instruments(self) -> Dict[str, Any]:
        """Get all instruments"""
        try:
            return self.broker.get_instruments()
        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            return self.broker.get_current_price(symbol)
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_orders(self) -> Dict[str, Any]:
        """Get all orders"""
        try:
            return self.broker.get_orders()
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all positions"""
        try:
            return self.broker.get_positions()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            return self.broker.cancel_order(order_id)
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close a position"""
        try:
            return self.broker.close_position(position_id)
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
        message="Multi-Broker Trading API is healthy",
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