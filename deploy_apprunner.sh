#!/bin/bash

# TradeLocker API - AWS App Runner Deployment Script
# This script deploys the containerized API to AWS App Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying TradeLocker API to AWS App Runner${NC}"
echo ""

# Configuration
APP_NAME="tradelocker-api"
REGION="eu-west-1"
PROFILE="landingzone"

# Check if GitHub repository is configured
if [ -z "$GITHUB_REPO" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_REPO environment variable not set${NC}"
    echo -e "${BLUE}📋 Please set your GitHub repository URL:${NC}"
    echo "  export GITHUB_REPO=https://github.com/yourusername/tradelocker-api"
    echo ""
    echo -e "${YELLOW}📝 Or provide it now:${NC}"
    read -p "GitHub repository URL: " GITHUB_REPO
    export GITHUB_REPO
fi

# Check if GitHub token is configured
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN environment variable not set${NC}"
    echo -e "${BLUE}📋 Please set your GitHub personal access token:${NC}"
    echo "  export GITHUB_TOKEN=your_github_token"
    echo ""
    echo -e "${YELLOW}📝 Or provide it now:${NC}"
    read -s -p "GitHub token: " GITHUB_TOKEN
    export GITHUB_TOKEN
    echo ""
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  App Name: $APP_NAME"
echo "  Region: $REGION"
echo "  Profile: $PROFILE"
echo "  GitHub Repo: $GITHUB_REPO"
echo ""

# Check if App Runner service exists
echo -e "${YELLOW}🔍 Checking if App Runner service exists...${NC}"
if aws apprunner describe-service --service-name $APP_NAME --region $REGION --profile $PROFILE > /dev/null 2>&1; then
    echo -e "${GREEN}✅ App Runner service exists${NC}"
    UPDATE_EXISTING=true
else
    echo -e "${YELLOW}📝 App Runner service does not exist, will create new one${NC}"
    UPDATE_EXISTING=false
fi
echo ""

# Create or update App Runner service
if [ "$UPDATE_EXISTING" = true ]; then
    echo -e "${YELLOW}🔄 Updating existing App Runner service...${NC}"
    
    # Create deployment configuration
    cat > deployment-config.json << EOF
{
    "SourceConfiguration": {
        "RepositoryUrl": "$GITHUB_REPO",
        "SourceCodeVersion": {
            "Type": "BRANCH",
            "Value": "main"
        },
        "CodeRepository": {
            "CodeConfiguration": {
                "ConfigurationSource": "API",
                "Runtime": "PYTHON_3",
                "BuildCommand": "pip install -r requirements.txt",
                "StartCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
            }
        }
    },
    "InstanceConfiguration": {
        "Cpu": "1 vCPU",
        "Memory": "2 GB",
        "InstanceRoleArn": "arn:aws:iam::491649323445:role/AppRunnerECRAccessRole"
    },
    "AutoScalingConfigurationArn": "arn:aws:apprunner:eu-west-1:491649323445:autoscalingconfiguration/TradeLockerAPI/1/00000000000000000000000000000001"
}
EOF

    # Update the service
    aws apprunner update-service \
        --service-name $APP_NAME \
        --source-configuration file://deployment-config.json \
        --region $REGION \
        --profile $PROFILE

    echo -e "${GREEN}✅ App Runner service updated${NC}"
else
    echo -e "${YELLOW}🆕 Creating new App Runner service...${NC}"
    
    # Create deployment configuration
    cat > deployment-config.json << EOF
{
    "ServiceName": "$APP_NAME",
    "SourceConfiguration": {
        "RepositoryUrl": "$GITHUB_REPO",
        "SourceCodeVersion": {
            "Type": "BRANCH",
            "Value": "main"
        },
        "CodeRepository": {
            "CodeConfiguration": {
                "ConfigurationSource": "API",
                "Runtime": "PYTHON_3",
                "BuildCommand": "pip install -r requirements.txt",
                "StartCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
            }
        }
    },
    "InstanceConfiguration": {
        "Cpu": "1 vCPU",
        "Memory": "2 GB",
        "InstanceRoleArn": "arn:aws:iam::491649323445:role/AppRunnerECRAccessRole"
    },
    "AutoScalingConfigurationArn": "arn:aws:apprunner:eu-west-1:491649323445:autoscalingconfiguration/TradeLockerAPI/1/00000000000000000000000000000001"
}
EOF

    # Create the service
    aws apprunner create-service \
        --cli-input-json file://deployment-config.json \
        --region $REGION \
        --profile $PROFILE

    echo -e "${GREEN}✅ App Runner service created${NC}"
fi

echo ""

# Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
sleep 30

# Get service URL
echo -e "${YELLOW}🔍 Getting service URL...${NC}"
SERVICE_URL=$(aws apprunner describe-service --service-name $APP_NAME --region $REGION --profile $PROFILE --query 'Service.ServiceUrl' --output text)

echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo -e "${BLUE}📋 Service Information:${NC}"
echo "  🌐 Service URL: https://$SERVICE_URL"
echo "  📚 Documentation: https://$SERVICE_URL/docs"
echo "  🔍 Health Check: https://$SERVICE_URL/health"
echo ""

# Test the health endpoint
echo -e "${YELLOW}🧪 Testing health endpoint...${NC}"
if curl -f https://$SERVICE_URL/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo "  # Health check"
    echo "  curl https://$SERVICE_URL/health"
    echo ""
    echo "  # Get accounts"
    echo "  curl https://$SERVICE_URL/accounts"
    echo ""
    echo "  # Get instruments"
    echo "  curl https://$SERVICE_URL/instruments"
    echo ""
    echo "  # Get current price"
    echo "  curl https://$SERVICE_URL/instruments/BTCUSD.TTF/price"
    echo ""
    echo "  # Create order (example)"
    echo "  curl -X POST https://$SERVICE_URL/orders \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"symbol\":\"BTCUSD.TTF\",\"order_type\":\"market\",\"side\":\"buy\",\"quantity\":0.01}'"
    echo ""
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo ""
    echo -e "${YELLOW}📋 Service logs:${NC}"
    aws apprunner describe-service --service-name $APP_NAME --region $REGION --profile $PROFILE
    echo ""
fi

# Clean up
rm -f deployment-config.json

echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  # View service status"
echo "  aws apprunner describe-service --service-name $APP_NAME --region $REGION --profile $PROFILE"
echo ""
echo "  # View logs"
echo "  aws logs tail /aws/apprunner/$APP_NAME --region $REGION --profile $PROFILE"
echo ""
echo "  # Delete service"
echo "  aws apprunner delete-service --service-name $APP_NAME --region $REGION --profile $PROFILE"
echo "" 