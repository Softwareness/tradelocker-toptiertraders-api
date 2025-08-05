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
    "Content-Type": "application/json"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": 113500.0,
    "stop_loss": 113200.0,
    "take_profit": 113800.0,
    "validity": "GTC",
    "description": "BTC long position from n8n"
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
  const currentPrice = priceData.ask_price;
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
    "Content-Type": "application/json"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": "={{ $('Decision').item.json.currentPrice }}",
    "stop_loss": "={{ $('Decision').item.json.currentPrice * 0.99 }}",
    "take_profit": "={{ $('Decision').item.json.currentPrice * 1.02 }}",
    "description": "Automated trade from n8n"
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

### 4. Risk Management Workflow

#### Workflow Structure
```
Cron Trigger → Get Positions → Calculate Risk → Decision → Close Positions
```

#### Risk Calculation (Code Node)
```javascript
const portfolioData = $input.all()[0].json;
const maxRisk = 1000; // $1000 max loss

const totalPnL = portfolioData.totalPnL;

if (totalPnL < -maxRisk) {
  return {
    shouldCloseAll: true,
    reason: `Portfolio loss (${totalPnL}) exceeds maximum risk (${maxRisk})`,
    totalPnL
  };
} else {
  return {
    shouldCloseAll: false,
    totalPnL
  };
}
```

#### Close All Positions (conditional)
```json
{
  "url": "https://your-app-runner-url/positions",
  "method": "DELETE",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 5. Market Data Monitoring

#### Get Account Status
```json
{
  "url": "https://your-app-runner-url/accounts",
  "method": "GET",
  "headers": {
    "Content-Type": "application/json"
  }
}
```
```

#### Account Monitoring (Code Node)
```javascript
const accountData = $input.all()[0].json;

if (accountData.success) {
  const account = accountData.accounts[0];
  const balance = account.accountBalance;
  const minBalance = 1000; // Minimum balance alert
  
  return {
    balance,
    currency: account.currency,
    accountId: account.id,
    status: account.status,
    lowBalance: balance < minBalance,
    alert: balance < minBalance ? `Low balance: ${balance} ${account.currency}` : null
  };
} else {
  throw new Error(`Failed to get account data: ${accountData.error}`);
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
  const currentPrice = priceData.ask_price;
  
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
  "url": "https://your-api-url/orders",
  "method": "POST",
  "headers": {
    "x-api-key": "your-api-key",
    "Content-Type": "application/json"
  },
  "body": {
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "={{ $('Technical Analysis').item.json.signal }}",
    "quantity": 0.01,
    "stop_loss": "={{ $('Technical Analysis').item.json.currentPrice * 0.98 }}",
    "take_profit": "={{ $('Technical Analysis').item.json.currentPrice * 1.03 }}",
    "description": "Automated strategy trade"
  }
}
```

### 7. Error Handling and Notifications

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
          "value": "{{ $('Place Order').item.json.symbol }}",
          "short": true
        },
        {
          "title": "Side",
          "value": "{{ $('Place Order').item.json.side }}",
          "short": true
        },
        {
          "title": "Quantity",
          "value": "{{ $('Place Order').item.json.quantity }}",
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
TRADELOCKER_API_KEY=your-api-key
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

This comprehensive integration allows you to build sophisticated automated trading systems using n8n's visual workflow builder while leveraging the power of your serverless TradeLocker API. 