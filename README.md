# TradeLocker API

A FastAPI-based REST API for automated trading with TradeLocker.

## Deployment

This application is deployed to AWS App Runner using Terraform. The deployment is configured to automatically redeploy when changes are pushed to the main branch.

### Infrastructure

The following AWS resources are created by Terraform:

- **AWS App Runner Service** - The main application service
- **ECR Repository** - For container images (if needed)
- **DynamoDB Table** - For order logging (`tradelocker-orders`)
- **Secrets Manager** - For storing credentials and API keys
- **CloudWatch Log Group** - For application logs

### Local Development

To run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export API_KEY="your-api-key"
export TRADELOCKER_CREDENTIALS_SECRET="your-credentials-secret"
export DYNAMODB_TABLE="tradelocker-orders"
export AWS_REGION="eu-west-1"

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /health` - Health check
- `GET /broker` - Get broker information
- `POST /orders` - Create a new trading order
- `GET /orders` - Get all orders
- `DELETE /orders/{order_id}` - Cancel a specific order
- `GET /accounts` - Get all accounts
- `GET /accounts/details` - Get detailed account information
- `GET /instruments` - Get all instruments
- `GET /instruments/{symbol}/price` - Get current price for a symbol
- `GET /positions` - Get all positions
- `DELETE /positions/{position_id}` - Close a specific position

### Environment Variables

The following environment variables are required:

- `API_KEY` - API key for authentication
- `TRADELOCKER_CREDENTIALS_SECRET` - Secret containing TradeLocker credentials
- `DYNAMODB_TABLE` - DynamoDB table name for order logging
- `AWS_REGION` - AWS region

### Auto-Deployment

The App Runner service is configured with auto-deployments enabled. When you push changes to the main branch, the service will automatically redeploy with the latest code.

## License

This project is licensed under the MIT License. 