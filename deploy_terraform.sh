#!/bin/bash

# TradeLocker API - Terraform App Runner Deployment Script
# This script deploys the containerized API to AWS App Runner using Terraform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying TradeLocker API to AWS App Runner with Terraform${NC}"
echo ""

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

# Check if it's a private repository
if [[ "$GITHUB_REPO" == *"private"* ]] || [[ "$GITHUB_REPO" == *"yourusername"* ]]; then
    echo -e "${YELLOW}🔒 Private repository detected${NC}"
    echo -e "${BLUE}📋 For private repositories, you need a GitHub personal access token${NC}"
    echo ""
    
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
    
    # Set private repository flag
    export TF_VAR_is_private_repository=true
    export TF_VAR_github_token="$GITHUB_TOKEN"
else
    export TF_VAR_is_private_repository=false
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  GitHub Repo: $GITHUB_REPO"
echo "  AWS Region: eu-west-1"
echo "  AWS Profile: landingzone"
echo "  API Key: ${API_KEY:-your-secret-api-key-here}"
echo ""

# Update the GitHub repository URL in variables.tf
echo -e "${YELLOW}🔧 Updating GitHub repository URL...${NC}"
sed -i.bak "s|https://github.com/yourusername/tradelocker-api|$GITHUB_REPO|g" variables.tf
echo -e "${GREEN}✅ GitHub repository URL updated${NC}"
echo ""

# Set API key for Terraform
export TF_VAR_api_key="${API_KEY:-your-secret-api-key-here}"
echo ""

# Initialize Terraform
echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
terraform init
echo -e "${GREEN}✅ Terraform initialized${NC}"
echo ""

# Plan the deployment
echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
terraform plan -out=tfplan
echo -e "${GREEN}✅ Terraform plan created${NC}"
echo ""

# Ask for confirmation
echo -e "${YELLOW}⚠️  Review the plan above and confirm deployment:${NC}"
read -p "Deploy to AWS App Runner? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

# Apply the deployment
echo -e "${YELLOW}🚀 Deploying to AWS App Runner...${NC}"
terraform apply tfplan
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""

# Configure private repository access if needed
if [ "$TF_VAR_is_private_repository" = "true" ]; then
    echo -e "${YELLOW}🔒 Configuring private repository access...${NC}"
    
    # Get the service ARN
    SERVICE_ARN=$(terraform output -raw app_runner_service_arn)
    
    # Configure source code credentials for private repository
    aws apprunner create-source-code-credentials \
        --source-code-credentials \
        "Provider=GITHUB,Token=$GITHUB_TOKEN" \
        --region eu-west-1 \
        --profile landingzone
    
    echo -e "${GREEN}✅ Private repository access configured${NC}"
    echo ""
fi

# Get the service URL
echo -e "${YELLOW}🔍 Getting service URL...${NC}"
SERVICE_URL=$(terraform output -raw app_runner_service_url)
echo -e "${GREEN}✅ Service URL: https://$SERVICE_URL${NC}"
echo ""

# Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
sleep 30

# Test the health endpoint
echo -e "${YELLOW}🧪 Testing health endpoint...${NC}"
if curl -f https://$SERVICE_URL/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
    echo ""
    echo -e "${BLUE}📋 Service Information:${NC}"
    echo "  🌐 Service URL: https://$SERVICE_URL"
    echo "  📚 Documentation: https://$SERVICE_URL/docs"
    echo "  🔍 Health Check: https://$SERVICE_URL/health"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo "  # Health check (no auth required)"
    echo "  curl https://$SERVICE_URL/health"
    echo ""
    echo "  # Get accounts (no auth required)"
    echo "  curl https://$SERVICE_URL/accounts"
    echo ""
    echo "  # Get detailed account info (requires API key)"
    echo "  curl -H 'X-API-Key: your-secret-api-key-here' https://$SERVICE_URL/accounts/details"
    echo ""
    echo "  # Get instruments (no auth required)"
    echo "  curl https://$SERVICE_URL/instruments"
    echo ""
    echo "  # Create order (requires API key)"
    echo "  curl -X POST https://$SERVICE_URL/orders \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -H 'X-API-Key: your-secret-api-key-here' \\"
    echo "    -d '{\"symbol\":\"BTCUSD.TTF\",\"order_type\":\"market\",\"side\":\"buy\",\"quantity\":0.01}'"
    echo ""
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo ""
    echo -e "${YELLOW}📋 Service logs:${NC}"
    aws apprunner describe-service --service-name tradelocker-api --region eu-west-1 --profile landingzone
    echo ""
fi

# Clean up
rm -f tfplan
rm -f variables.tf.bak

echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  # View service status"
echo "  aws apprunner describe-service --service-name tradelocker-api --region eu-west-1 --profile landingzone"
echo ""
echo "  # View logs"
echo "  aws logs tail /aws/apprunner/tradelocker-api --region eu-west-1 --profile landingzone"
echo ""
echo "  # Destroy infrastructure"
echo "  terraform destroy"
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}" 