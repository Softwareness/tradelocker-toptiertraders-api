# 🚀 TradeLocker API - Containerized REST API

A modern, containerized REST API for automated trading with TradeLocker, built with FastAPI and deployable to AWS App Runner.

## 🏗️ **Architecture**

This solution uses **AWS App Runner** instead of Lambda for better reliability and easier debugging:

- **FastAPI** - Modern, fast web framework
- **Docker** - Containerized deployment
- **AWS App Runner** - Managed container service
- **AWS Secrets Manager** - Secure credential storage
- **AWS DynamoDB** - Order logging and state management

## 🚀 **Quick Start**

### 1. **Local Development**

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

### 2. **AWS App Runner Deployment**

#### **Public Repository:**
```bash
# Set up GitHub repository
export GITHUB_REPO=https://github.com/Softwareness/tradelocker-api

# Deploy to AWS App Runner
./deploy_terraform.sh
```

#### **Private Repository:**
```bash
# Set up GitHub repository and token
export GITHUB_REPO=https://github.com/Softwareness/tradelocker-api
export GITHUB_TOKEN=your_github_token

# Deploy to AWS App Runner with private repository
./deploy_private_repo.sh
```

## 📋 **API Endpoints**

### Health Check
```bash
GET /health
```

### Orders
```bash
# Create order
POST /orders
{
  "symbol": "BTCUSD.TTF",
  "order_type": "market",
  "side": "buy",
  "quantity": 0.01,
  "stop_loss": 45000,
  "take_profit": 55000
}

# Get all orders
GET /orders

# Cancel order
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

# Get current price
GET /instruments/{symbol}/price
```

### Positions
```bash
# Get all positions
GET /positions

# Close position
DELETE /positions/{position_id}
```

## 🐳 **Local Development**

### Prerequisites
- Docker and Docker Compose
- TradeLocker credentials
- AWS CLI configured

### Setup
1. **Create `.env` file:**
```bash
TRADELOCKER_USERNAME=your_username
TRADELOCKER_PASSWORD=your_password
TRADELOCKER_SERVER=your_server
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
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01
  }'
```

### Local Development Commands
```bash
# View logs
docker-compose logs -f

# Stop the API
docker-compose down

# Rebuild and restart
docker-compose up --build -d
```

## ☁️ **AWS App Runner Deployment**

### Prerequisites
- AWS CLI configured with `landingzone` profile
- GitHub repository with the code
- GitHub personal access token

### Deployment Steps

1. **Set up environment variables:**
```bash
export GITHUB_REPO=https://github.com/yourusername/tradelocker-api
export GITHUB_TOKEN=your_github_token
```

2. **Deploy to App Runner:**
```bash
./deploy_apprunner.sh
```

3. **Test the deployed API:**
```bash
# Get the service URL
SERVICE_URL=$(aws apprunner describe-service \
  --service-name tradelocker-api \
  --region eu-west-1 \
  --profile landingzone \
  --query 'Service.ServiceUrl' \
  --output text)

# Test health endpoint
curl https://$SERVICE_URL/health
```

### App Runner Management
```bash
# View service status
aws apprunner describe-service \
  --service-name tradelocker-api \
  --region eu-west-1 \
  --profile landingzone

# View logs
aws logs tail /aws/apprunner/tradelocker-api \
  --region eu-west-1 \
  --profile landingzone

# Delete service
aws apprunner delete-service \
  --service-name tradelocker-api \
  --region eu-west-1 \
  --profile landingzone
```

## 🔧 **Configuration**

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRADELOCKER_USERNAME` | TradeLocker username | - |
| `TRADELOCKER_PASSWORD` | TradeLocker password | - |
| `TRADELOCKER_SERVER` | TradeLocker server | - |
| `TRADELOCKER_ENVIRONMENT` | TradeLocker environment | `https://demo.tradelocker.com` |
| `TRADELOCKER_SECRET_NAME` | AWS Secrets Manager secret name | `tradelocker/credentials` |
| `ORDERS_TABLE_NAME` | DynamoDB table for order logging | `tradelocker-orders` |

### AWS Resources Required

1. **Secrets Manager Secret:**
```json
{
  "environment": "https://demo.tradelocker.com",
  "username": "your_username",
  "password": "your_password",
  "server": "your_server"
}
```

2. **DynamoDB Table:**
```bash
aws dynamodb create-table \
  --table-name tradelocker-orders \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1 \
  --profile landingzone
```

## 📊 **API Documentation**

Once the API is running, visit:
- **Swagger UI:** `http://localhost:8000/docs` (local) or `https://your-app-runner-url/docs`
- **ReDoc:** `http://localhost:8000/redoc` (local) or `https://your-app-runner-url/redoc`

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

## 🧪 **Testing**

### Example API Calls

```bash
# Health check
curl https://your-app-runner-url/health

# Get accounts
curl https://your-app-runner-url/accounts

# Get detailed account information
curl https://your-app-runner-url/accounts/details

# Get instruments
curl https://your-app-runner-url/instruments

# Get current price
curl https://your-app-runner-url/instruments/BTCUSD.TTF/price

# Create market order
curl -X POST https://your-app-runner-url/orders \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "market",
    "side": "buy",
    "quantity": 0.01
  }'

# Create limit order with SL/TP
curl -X POST https://your-app-runner-url/orders \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "BTCUSD.TTF",
    "order_type": "limit",
    "side": "buy",
    "quantity": 0.01,
    "price": 50000,
    "stop_loss": 45000,
    "take_profit": 55000
  }'
```

## 🔍 **Monitoring & Logging**

### Local Logs
```bash
# View container logs
docker-compose logs -f

# View specific service logs
docker-compose logs tradelocker-api
```

### AWS CloudWatch Logs
```bash
# View App Runner logs
aws logs tail /aws/apprunner/tradelocker-api \
  --region eu-west-1 \
  --profile landingzone \
  --follow
```

## 🛠️ **Troubleshooting**

### Common Issues

1. **Container won't start:**
   - Check your `.env` file has correct credentials
   - Ensure AWS credentials are configured
   - Check Docker logs: `docker-compose logs`

2. **API returns 503 errors:**
   - Verify TradeLocker credentials
   - Check network connectivity
   - Review application logs

3. **App Runner deployment fails:**
   - Ensure GitHub repository is public or token has access
   - Check IAM roles and permissions
   - Verify region and profile configuration

### Debug Commands

```bash
# Test TradeLocker connection locally
python -c "
from tradelocker import TLAPI
tl = TLAPI(
    environment='https://demo.tradelocker.com',
    username='your_username',
    password='your_password',
    server='your_server'
)
print('Connection successful')
"

# Check AWS credentials
aws sts get-caller-identity --profile landingzone

# Test Secrets Manager access
aws secretsmanager get-secret-value \
  --secret-id tradelocker/credentials \
  --region eu-west-1 \
  --profile landingzone
```

## 📈 **Benefits of App Runner vs Lambda**

| Feature | Lambda | App Runner |
|---------|--------|------------|
| **Cold Starts** | Yes | No |
| **Dependencies** | Complex layers | Simple requirements.txt |
| **Debugging** | Limited | Full container logs |
| **Local Testing** | Difficult | Easy with Docker |
| **Auto-scaling** | Yes | Yes |
| **HTTPS** | Via API Gateway | Built-in |
| **Deployment** | Complex | Simple GitHub integration |

## 🚀 **Next Steps**

1. **Set up GitHub repository** with your code
2. **Configure AWS credentials** in Secrets Manager
3. **Test locally** with Docker
4. **Deploy to App Runner** for production
5. **Integrate with n8n** for automation

## 📝 **License**

This project is licensed under the MIT License. 