# 🚀 TradeLocker API - FastAPI Trading Service

A modern, containerized REST API for automated trading with TradeLocker, built with FastAPI.

## 🏗️ **Architecture**

This solution provides a **FastAPI** application that can be deployed to any container platform:

- **FastAPI** - Modern, fast web framework
- **Docker** - Containerized deployment
- **TradeLocker Python SDK** - Official trading library
- **Pydantic** - Data validation and serialization
- **Uvicorn** - ASGI server

## 🚀 **Quick Start**

### **Local Development**

```bash
# Clone the repository
git clone <your-repo-url>
cd TradeLocker

# Set up your credentials
cp .env.example .env
# Edit .env with your TradeLocker credentials

# Run locally with Docker
./run_local.sh
```

## 📋 **API Endpoints**

### Health Check
```bash
GET /health
```

### Orders Management

#### **Create Market Order with Stop Loss & Take Profit**
```bash
POST /orders
{
  "symbol": "BTCUSD.TTF",
  "order_type": "market",
  "side": "buy",
  "quantity": 0.01,
  "stop_loss": 114210,
  "stop_loss_type": "absolute",
  "take_profit": 115200,
  "take_profit_type": "absolute"
}
```

#### **Create Limit Order with Stop Loss & Take Profit**
```bash
POST /orders
{
  "symbol": "BTCUSD.TTF",
  "order_type": "limit",
  "side": "buy",
  "quantity": 0.01,
  "price": 114000,
  "stop_loss": 113500,
  "stop_loss_type": "absolute",
  "take_profit": 115000,
  "take_profit_type": "absolute",
  "validity": "GTC"
}
```

#### **Create Market Order with Trailing Stop Loss**
```bash
POST /orders
{
  "symbol": "BTCUSD.TTF",
  "order_type": "market",
  "side": "buy",
  "quantity": 0.01,
  "stop_loss": 1000,
  "stop_loss_type": "trailingOffset"
}
```

#### **Get All Orders**
```bash
GET /orders
```

#### **Cancel Order**
```bash
DELETE /orders/{order_id}
```

### Accounts
```bash
# Get all accounts
GET /accounts

# Get detailed account information (balance, equity, margin, positions)
GET /accounts/details
```

**Account Details Response:**
```json
{
  "success": true,
  "account_id": 1614336,
  "account_name": "TTFPRP#03c05155-51ac-4cf0-abba-3cc9a097d0c8#1#1",
  "currency": "USD",
  "balance": 5000.52,
  "equity": 5000.52,
  "margin_used": 0.0008,
  "margin_available": 5000.52,
  "margin_level": 627427263.65,
  "free_margin": 5000.52,
  "total_positions_value": 0.08,
  "unrealized_pnl": 0.0,
  "positions_count": 2,
  "account_status": "ACTIVE",
  "positions": [...]
}
```

### Instruments
```bash
# Get all instruments
GET /instruments

# Get current price for a symbol
GET /instruments/{symbol}/price
```

### Positions
```bash
# Get all positions
GET /positions

### **Position Management**

#### **Close a Position**
```bash
DELETE /positions/{position_id}
```

**Important Note**: The TradeLocker API has a limitation where positions cannot be directly "closed" or deleted. Instead, closing a position creates an **opposite position** to neutralize the exposure. The original position remains visible for audit purposes.

**Example**:
```bash
# Close a buy position (creates a sell position)
curl -X DELETE -H "X-API-Key: your-api-key" \
  http://localhost:8000/positions/7782220156104341016
```

**Response**:
```json
{
  "success": true,
  "order_id": "7782220156131813090",
  "status": "closed",
  "message": "Position closed by creating opposite order 7782220156131813090 (original position remains for audit)",
  "timestamp": "2025-08-05T07:50:02.096479+00:00"
}
```

**Result**: 
- Original position remains visible for audit
- New opposite position is created to neutralize exposure
- Net exposure becomes zero (or negative if multiple closes)

**TradeLocker API Limitation**: This is the expected behavior of the TradeLocker platform - positions are never "deleted" but rather "closed" through opposite orders for compliance and audit purposes.
```

## 📈 **Order Management Guide**

### **Supported Order Types**

#### **1. Market Orders**
- **Purpose**: Execute immediately at current market price
- **Use Case**: Quick entry/exit, high liquidity situations
- **Example**:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01,
    "stop_loss": 114210,
    "stop_loss_type": "absolute",
    "take_profit": 115200,
    "take_profit_type": "absolute"
  }'
```

#### **2. Limit Orders**
- **Purpose**: Execute at specified price or better
- **Use Case**: Entry at specific levels, avoiding slippage
- **Example**:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": 114000,
    "stop_loss": 113500,
    "stop_loss_type": "absolute",
    "take_profit": 115000,
    "take_profit_type": "absolute",
    "validity": "GTC"
  }'
```

#### **3. Stop Orders**
- **Purpose**: Execute when price reaches stop level
- **Use Case**: Breakout entries, stop losses
- **Example**:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "stop",
    "side": "buy",
    "quantity": 0.01,
    "stop_price": 115000,
    "stop_loss": 114500,
    "stop_loss_type": "absolute",
    "take_profit": 116000,
    "take_profit_type": "absolute",
    "validity": "GTC"
  }'
```

#### **4. Stop-Limit Orders**
- **Purpose**: Stop order that becomes a limit order when triggered
- **Use Case**: Controlled breakout entries
- **Example**:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "stop_limit",
    "side": "buy",
    "quantity": 0.01,
    "stop_price": 115000,
    "price": 115100,
    "stop_loss": 114500,
    "stop_loss_type": "absolute",
    "take_profit": 116000,
    "take_profit_type": "absolute",
    "validity": "GTC"
  }'
```

### **Stop Loss Types**

#### **1. Absolute Stop Loss**
- **Type**: `"absolute"`
- **Description**: Fixed price level
- **Example**: `"stop_loss": 114210, "stop_loss_type": "absolute"`

#### **2. Offset Stop Loss**
- **Type**: `"offset"`
- **Description**: Relative to entry price
- **Example**: `"stop_loss": 500, "stop_loss_type": "offset"`

#### **3. Trailing Stop Loss**
- **Type**: `"trailingOffset"`
- **Description**: Moves with price in favorable direction
- **Example**: `"stop_loss": 1000, "stop_loss_type": "trailingOffset"`

### **Take Profit Types**

#### **1. Absolute Take Profit**
- **Type**: `"absolute"`
- **Description**: Fixed price level
- **Example**: `"take_profit": 115200, "take_profit_type": "absolute"`

#### **2. Offset Take Profit**
- **Type**: `"offset"`
- **Description**: Relative to entry price
- **Example**: `"take_profit": 1000, "take_profit_type": "offset"`

### **Order Validity**

- **GTC** (Good Till Cancelled): Order remains active until cancelled
- **IOC** (Immediate Or Cancel): Execute immediately or cancel
- **FOK** (Fill Or Kill): Execute completely or cancel

### **Supported Instruments**

#### **Cryptocurrencies**
- `BTCUSD.TTF` - Bitcoin (recommended)
- `XAUUSD.TTF` - Gold

#### **Forex Pairs**
- `AUDCAD` - Australian Dollar / Canadian Dollar
- `EURUSD` - Euro / US Dollar
- `GBPUSD` - British Pound / US Dollar
- And many more...

### **Risk Management**

#### **Position Sizing**
- **Small**: 0.01 lots (recommended for testing)
- **Medium**: 0.1 lots
- **Large**: 1.0+ lots (use with caution)

#### **Stop Loss Guidelines**
- **BTCUSD.TTF**: 500-2000 points
- **Forex**: 50-200 pips
- **Gold**: 100-500 points

#### **Risk-Reward Ratios**
- **Conservative**: 1:1.5
- **Moderate**: 1:2
- **Aggressive**: 1:3+

### **API Authentication**

All sensitive endpoints require API key authentication:

```bash
# Include API key in headers
curl -H "X-API-Key: your-secret-api-key-here" \
  http://localhost:8000/orders
```

### **Error Handling**

Common error responses:

```json
{
  "success": false,
  "error": "No TRADE route found for instrument_id=np.int64(892)",
  "timestamp": "2025-08-05T05:13:23.551674+00:00"
}
```

**Common Issues:**
1. **Invalid instrument**: Check symbol name
2. **No TRADE route**: Instrument not available for API trading
3. **Invalid price**: Price outside acceptable range
4. **Insufficient margin**: Not enough account balance

### **Testing Your Orders**

#### **1. Test Market Order**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01
  }'
```

#### **2. Test Limit Order**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": 114000,
    "validity": "GTC"
  }'
```

#### **3. Test with Stop Loss & Take Profit**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01,
    "stop_loss": 114210,
    "stop_loss_type": "absolute",
    "take_profit": 115200,
    "take_profit_type": "absolute"
  }'
```

## 📈 **Account Monitoring Features**

The API provides comprehensive account monitoring capabilities:

### **Financial Metrics**
- **Balance:** Current account balance
- **Equity:** Balance + unrealized P&L
- **Margin Used:** Estimated margin required for positions
- **Margin Available:** Available margin for new trades
- **Margin Level:** Margin level percentage
- **Free Margin:** Available margin

### **Position Tracking**
- **Total Positions Value:** Combined value of all positions
- **Unrealized P&L:** Current unrealized profit/loss
- **Positions Count:** Number of active positions
- **Position Details:** Individual position information with SL/TP

### **Real-time Data**
- Live account status monitoring
- Real-time position updates
- Current market prices
- Order execution tracking

Perfect for automated trading strategies and risk management!

## 🔐 **API Security**

### **API Key Authentication**
All sensitive endpoints require API key authentication:

```bash
# Required for:
# - POST /orders (create orders)
# - DELETE /orders/{order_id} (cancel orders)
# - GET /accounts/details (account details)
# - DELETE /positions/{position_id} (close positions)

curl -H "X-API-Key: your-secret-api-key-here" \
  http://localhost:8000/orders
```

### **Public Endpoints**
These endpoints don't require authentication:
- `GET /health` - Health check
- `GET /accounts` - Basic account info
- `GET /instruments` - Available instruments
- `GET /instruments/{symbol}/price` - Current prices
- `GET /positions` - Open positions
- `GET /orders` - Order history

## 🐳 **Local Development**

### **Prerequisites**
- Docker and Docker Compose
- TradeLocker credentials

### **Setup**
1. **Create `.env` file:**
```bash
TRADELOCKER_USERNAME=your_username
TRADELOCKER_PASSWORD=your_password
TRADELOCKER_SERVER=your_server
API_KEY=your-secret-api-key-here
```

2. **Run locally:**
```bash
./run_local.sh
```

3. **Test the API:**
```bash
# Health check
curl http://localhost:8000/health

# Get accounts
curl http://localhost:8000/accounts

# Get detailed account information
curl http://localhost:8000/accounts/details

# Create order
curl -X POST http://localhost:8000/orders \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-secret-api-key-here' \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01
  }'
```

### **Local Development Commands**
```bash
# View logs
docker-compose logs -f

# Stop the API
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## 🔧 **Troubleshooting**

### **Common Issues**

1. **"No TRADE route found"**
   - Check if instrument is available for API trading
   - Try different instruments (BTCUSD.TTF, AUDCAD, etc.)

2. **"Invalid API key"**
   - Verify API key in headers
   - Check environment variables

3. **"Instrument not found"**
   - Verify symbol name (case sensitive)
   - Check available instruments list

4. **"TP price for the order is not valid"**
   - Adjust take profit price to realistic levels
   - Check current market price

### **Debug Mode**
Enable detailed logging:
```bash
# Check container logs
docker-compose logs -f

# Check specific endpoint
curl -v http://localhost:8000/health
```

## 📚 **Examples**

### **Complete Trading Workflow**

1. **Check Account Status**
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/accounts/details
```

2. **Get Current Price**
```bash
curl http://localhost:8000/instruments/BTCUSD.TTF/price
```

3. **Place Market Order with SL/TP**
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01,
    "stop_loss": 114210,
    "stop_loss_type": "absolute",
    "take_profit": 115200,
    "take_profit_type": "absolute"
  }'
```

4. **Monitor Positions**
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/positions
```

5. **Close Position (if needed)**
```bash
curl -X DELETE -H "X-API-Key: your-api-key" \
  http://localhost:8000/positions/{position_id}
```

## 🎯 **Best Practices**

1. **Always use stop loss and take profit**
2. **Test with small quantities first**
3. **Monitor positions regularly**
4. **Use appropriate risk-reward ratios**
5. **Keep API keys secure**
6. **Test thoroughly before live trading**

## 📖 **Documentation**

Once the API is running, visit:
- **Swagger UI:** `http://localhost:8000/docs` (local)
- **ReDoc:** `http://localhost:8000/redoc` (local)

## 🔗 **Integration**

For n8n integration examples, see: `n8n_integration_examples.md`

Perfect for automated trading strategies and risk management! 