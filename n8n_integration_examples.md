# n8n Integration Examples for TradeLocker API

## 🔗 API Configuration

### Base URL
```
https://your-app-runner-service-url.region.awsapprunner.com
```

### Headers
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-secret-api-key-here"
}
```

> **Note:** API key authentication is required for sensitive endpoints. Set your API key in the `X-API-Key` header.

## 📋 n8n Workflow Examples

### 1. Create Trading Order

#### HTTP Request Node Configuration
```json
{
  "url": "https://your-app-runner-url/orders",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01,
    "stop_loss": 114210,
    "stop_loss_type": "absolute",
    "take_profit": 115200,
    "take_profit_type": "absolute"
  }
}
```

#### Response Handling
```javascript
// In Code node after HTTP Request
const response = $input.all()[0].json;

if (response.success) {
  return {
    order_id: response.order_id,
    status: response.status,
    message: response.message,
    timestamp: response.timestamp
  };
} else {
  throw new Error(`Order creation failed: ${response.error}`);
}
```

### 2. Get Current Price and Place Order

#### Workflow Structure
```
Trigger → Get Price → Decision → Place Order → Notification
```

#### Get Price Node
```json
{
  "url": "https://your-app-runner-url/instruments/BTCUSD.TTF/price",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

#### Decision Node (Code)
```javascript
const priceData = $input.all()[0].json;

if (priceData.success) {
  const currentPrice = priceData.ask_price || 114000; // Fallback if price not available
  const targetPrice = 113500.0;
  
  // Place order if price is below target
  if (currentPrice <= targetPrice) {
    return { shouldTrade: true, currentPrice };
  } else {
    return { shouldTrade: false, currentPrice };
  }
} else {
  throw new Error(`Failed to get price: ${priceData.error}`);
}
```

#### Place Order Node (conditional)
```json
{
  "url": "https://your-app-runner-url/orders",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": "={{ $('Decision').item.json.currentPrice }}",
    "stop_loss": "={{ $('Decision').item.json.currentPrice * 0.99 }}",
    "stop_loss_type": "absolute",
    "take_profit": "={{ $('Decision').item.json.currentPrice * 1.02 }}",
    "take_profit_type": "absolute",
    "validity": "GTC"
  }
}
```

### 3. Portfolio Monitoring

#### Get Positions
```json
{
  "url": "https://your-app-runner-url/positions",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

#### Portfolio Analysis (Code Node)
```javascript
const positions = $input.all()[0].json;

if (positions.success) {
  const totalPnL = positions.positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const openPositions = positions.positions.length;
  
  return {
    totalPnL,
    openPositions,
    positions: positions.positions,
    timestamp: new Date().toISOString()
  };
} else {
  throw new Error(`Failed to get positions: ${positions.error}`);
}
```

### 4. Account Monitoring

#### Get Account Details
```json
{
  "url": "https://your-app-runner-url/accounts/details",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
  }
}
```

#### Account Analysis (Code Node)
```javascript
const accountData = $input.all()[0].json;

if (accountData.success) {
  const balance = accountData.balance;
  const equity = accountData.equity;
  const marginUsed = accountData.margin_used;
  const marginAvailable = accountData.margin_available;
  const marginLevel = accountData.margin_level;
  const positionsCount = accountData.positions_count;
  const unrealizedPnl = accountData.unrealized_pnl;
  
  return {
    balance,
    equity,
    marginUsed,
    marginAvailable,
    marginLevel,
    positionsCount,
    unrealizedPnl,
    currency: accountData.currency,
    accountId: accountData.account_id,
    status: accountData.account_status,
    lowBalance: balance < 1000,
    lowMargin: marginLevel < 100,
    alert: balance < 1000 ? `Low balance: ${balance} ${accountData.currency}` : 
           marginLevel < 100 ? `Low margin level: ${marginLevel}%` : null
  };
} else {
  throw new Error(`Failed to get account data: ${accountData.error}`);
}
```

### 5. Risk Management Workflow

#### Workflow Structure
```
Cron Trigger → Get Account Details → Calculate Risk → Decision → Close Positions
```

#### Risk Calculation (Code Node)
```javascript
const accountData = $input.all()[0].json;
const maxRisk = 1000; // $1000 max loss

if (accountData.success) {
  const unrealizedPnl = accountData.unrealizedPnl;
  const marginLevel = accountData.marginLevel;
  
  if (unrealizedPnl < -maxRisk) {
    return {
      shouldCloseAll: true,
      reason: `Portfolio loss (${unrealizedPnl}) exceeds maximum risk (${maxRisk})`,
      unrealizedPnl
    };
  } else if (marginLevel < 100) {
    return {
      shouldCloseAll: true,
      reason: `Low margin level (${marginLevel}%)`,
      marginLevel
    };
  } else {
    return {
      shouldCloseAll: false,
      unrealizedPnl,
      marginLevel
    };
  }
} else {
  throw new Error(`Failed to get account data: ${accountData.error}`);
}
```

#### Close All Positions (conditional)
```json
{
  "url": "https://your-app-runner-url/positions",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

#### Close Position (Code Node)
```javascript
const positions = $input.all()[0].json;

if (positions.success && positions.positions.length > 0) {
  // Close each position
  const closePromises = positions.positions.map(position => {
    return {
      url: `https://your-app-runner-url/positions/${position.id}`,
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": "your-secret-api-key-here"
      }
    };
  });
  
  return {
    positionsToClose: closePromises,
    count: positions.positions.length
  };
} else {
  return {
    positionsToClose: [],
    count: 0
  };
}
```

### 6. Automated Trading Strategy

#### Workflow Structure
```
Cron Trigger → Get Price → Technical Analysis → Decision → Place Order
```

#### Technical Analysis (Code Node)
```javascript
const priceData = $input.all()[0].json;

if (priceData.success) {
  const currentPrice = priceData.ask_price || 114000; // Fallback if price not available
  
  // Simple moving average strategy (example)
  // In real implementation, you'd calculate actual moving averages
  const sma20 = currentPrice * 0.995; // Mock SMA
  const sma50 = currentPrice * 1.005; // Mock SMA
  
  const signal = currentPrice > sma20 && sma20 > sma50 ? 'buy' : 'sell';
  
  return {
    currentPrice,
    sma20,
    sma50,
    signal,
    shouldTrade: signal === 'buy'
  };
} else {
  throw new Error(`Failed to get price: ${priceData.error}`);
}
```

#### Place Order Based on Signal
```json
{
  "url": "https://your-app-runner-url/orders",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "={{ $('Technical Analysis').item.json.signal }}",
    "quantity": 0.01,
    "stop_loss": "={{ $('Technical Analysis').item.json.currentPrice * 0.98 }}",
    "stop_loss_type": "absolute",
    "take_profit": "={{ $('Technical Analysis').item.json.currentPrice * 1.03 }}",
    "take_profit_type": "absolute"
  }
}
```

### 7. Trailing Stop Loss Strategy

#### Create Trailing Stop Order
```json
{
  "url": "https://your-app-runner-url/orders",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-api-key-here"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01,
    "stop_loss": 1000,
    "stop_loss_type": "trailingOffset"
  }
}
```

### 8. Error Handling and Notifications

#### Error Handling (Code Node)
```javascript
const previousNode = $input.all()[0];

if (previousNode.json && !previousNode.json.success) {
  // Send error notification
  return {
    error: true,
    message: previousNode.json.error,
    timestamp: new Date().toISOString(),
    node: previousNode.name
  };
} else {
  return {
    error: false,
    success: true
  };
}
```

#### Slack Notification (Error)
```json
{
  "channel": "#trading-alerts",
  "text": "🚨 Trading API Error: {{ $('Error Handler').item.json.message }}",
  "attachments": [
    {
      "color": "danger",
      "fields": [
        {
          "title": "Error",
          "value": "{{ $('Error Handler').item.json.message }}",
          "short": false
        },
        {
          "title": "Timestamp",
          "value": "{{ $('Error Handler').item.json.timestamp }}",
          "short": true
        }
      ]
    }
  ]
}
```

#### Slack Notification (Success)
```json
{
  "channel": "#trading-alerts",
  "text": "✅ Trade Executed Successfully",
  "attachments": [
    {
      "color": "good",
      "fields": [
        {
          "title": "Order ID",
          "value": "{{ $('Place Order').item.json.order_id }}",
          "short": true
        },
        {
          "title": "Symbol",
          "value": "BTCUSD.TTF",
          "short": true
        },
        {
          "title": "Side",
          "value": "{{ $('Place Order').item.json.side }}",
          "short": true
        },
        {
          "title": "Quantity",
          "value": "0.01",
          "short": true
        }
      ]
    }
  ]
}
```

## 🔧 Advanced n8n Configurations

### Environment Variables
Set these in n8n settings:
```
TRADELOCKER_API_URL=https://your-api-url
TRADELOCKER_API_KEY=your-secret-api-key-here
TRADELOCKER_SYMBOL=BTCUSD.TTF
TRADELOCKER_QUANTITY=0.01
```

### Webhook Triggers
Configure webhook endpoints for real-time trading signals:
```
https://your-n8n-instance/webhook/trading-signal
```

### Scheduled Workflows
- **Daily Portfolio Check**: Every day at 9 AM
- **Price Monitoring**: Every 5 minutes
- **Risk Management**: Every hour
- **Weekly Report**: Every Monday at 8 AM

### Data Storage
Use n8n's built-in data storage or integrate with external databases:
- PostgreSQL for historical data
- Redis for caching
- MongoDB for flexible data storage

## 📊 Monitoring and Analytics

### Custom Metrics
Track in n8n:
- Orders placed per day
- Success/failure rates
- Portfolio performance
- API response times

### Dashboard Integration
Connect n8n workflows to:
- Grafana dashboards
- TradingView alerts
- Telegram bots
- Email notifications

## 🎯 **API Endpoints Summary**

### **Public Endpoints** (No API Key Required)
- `GET /health` - Health check
- `GET /accounts` - Basic account info
- `GET /instruments` - Available instruments
- `GET /instruments/{symbol}/price` - Current prices
- `GET /positions` - Open positions
- `GET /orders` - Order history

### **Protected Endpoints** (API Key Required)
- `POST /orders` - Create orders
- `DELETE /orders/{order_id}` - Cancel orders
- `GET /accounts/details` - Detailed account info
- `DELETE /positions/{position_id}` - Close positions

### **Supported Order Types**
- **Market**: Immediate execution
- **Limit**: Execute at specified price
- **Stop**: Execute when price reaches stop level
- **Stop-Limit**: Stop order that becomes limit order

### **Stop Loss Types**
- **absolute**: Fixed price level
- **offset**: Relative to entry price
- **trailingOffset**: Moves with price

### **Take Profit Types**
- **absolute**: Fixed price level
- **offset**: Relative to entry price

This comprehensive integration allows you to build sophisticated automated trading systems using n8n's visual workflow builder while leveraging the power of your containerized TradeLocker API. 