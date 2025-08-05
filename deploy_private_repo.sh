#!/bin/bash

# TradeLocker API - Private GitHub Repository Deployment
# This script deploys to AWS App Runner using a private GitHub repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 Deploying TradeLocker API with Private GitHub Repository${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if GitHub repository is configured
if [ -z "$GITHUB_REPO" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_REPO environment variable not set${NC}"
    echo -e "${BLUE}📋 Please set your private GitHub repository URL:${NC}"
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
echo "  GitHub Repo: $GITHUB_REPO"
echo "  GitHub Token: ${GITHUB_TOKEN:0:8}..."
echo "  AWS Region: eu-west-1"
echo "  AWS Profile: landingzone"
echo "  Repository Type: Private"
echo ""

# Update the GitHub repository URL in variables.tf
echo -e "${YELLOW}🔧 Updating GitHub repository URL...${NC}"
sed -i.bak "s|https://github.com/yourusername/tradelocker-api|$GITHUB_REPO|g" variables.tf
echo -e "${GREEN}✅ GitHub repository URL updated${NC}"
echo ""

# Set Terraform variables for private repository
export TF_VAR_is_private_repository=true
export TF_VAR_github_token="$GITHUB_TOKEN"

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
read -p "Deploy to AWS App Runner with private repository? (y/N): " -n 1 -r
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

# Configure private repository access
echo -e "${YELLOW}🔒 Configuring private repository access...${NC}"

# Create source code credentials for GitHub
echo -e "${YELLOW}📝 Creating GitHub source code credentials...${NC}"
CREDENTIALS_ARN=$(aws apprunner create-source-code-credentials \
    --source-code-credentials \
    "Provider=GITHUB,Token=$GITHUB_TOKEN" \
    --region eu-west-1 \
    --profile landingzone \
    --query 'SourceCodeCredentials.Arn' \
    --output text)

echo -e "${GREEN}✅ GitHub credentials created: ${CREDENTIALS_ARN}${NC}"

# Get the service ARN
SERVICE_ARN=$(terraform output -raw app_runner_service_arn)
SERVICE_NAME=$(terraform output -raw app_runner_service_name)

echo -e "${YELLOW}📝 Updating App Runner service with private repository access...${NC}"

# Update the service to use the credentials
aws apprunner update-service \
    --service-arn "$SERVICE_ARN" \
    --source-configuration \
    "RepositoryUrl=$GITHUB_REPO,SourceCodeVersion=Type=BRANCH,Value=main,CodeConfiguration=ConfigurationSource=API,Runtime=PYTHON_3,BuildCommand=pip install -r requirements.txt,StartCommand=python -m uvicorn app.main:app --host 0.0.0.0 --port 8000,SourceCodeCredentials=Arn=$CREDENTIALS_ARN" \
    --region eu-west-1 \
    --profile landingzone

echo -e "${GREEN}✅ Private repository access configured${NC}"
echo ""

# Get the service URL
echo -e "${YELLOW}🔍 Getting service URL...${NC}"
SERVICE_URL=$(terraform output -raw app_runner_service_url)
echo -e "${GREEN}✅ Service URL: https://$SERVICE_URL${NC}"
echo ""

# Wait for deployment to complete
echo -e "${YELLOW}⏳ Waiting for deployment to complete...${NC}"
sleep 60

# Test the health endpoint
echo -e "${YELLOW}🧪 Testing health endpoint...${NC}"
if curl -f https://$SERVICE_URL/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
    echo ""
    echo -e "${BLUE}📋 Service Information:${NC}"
    echo "  🌐 Service URL: https://$SERVICE_URL"
    echo "  📚 Documentation: https://$SERVICE_URL/docs"
    echo "  🔍 Health Check: https://$SERVICE_URL/health"
    echo "  🔒 Repository: Private GitHub"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo "  # Health check"
    echo "  curl https://$SERVICE_URL/health"
    echo ""
    echo "  # Get accounts"
    echo "  curl https://$SERVICE_URL/accounts"
    echo ""
    echo "  # Get detailed account info"
    echo "  curl https://$SERVICE_URL/accounts/details"
    echo ""
    echo "  # Get instruments"
    echo "  curl https://$SERVICE_URL/instruments"
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
    aws apprunner describe-service --service-name $SERVICE_NAME --region eu-west-1 --profile landingzone
    echo ""
fi

# Clean up
rm -f tfplan
rm -f variables.tf.bak

echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  # View service status"
echo "  aws apprunner describe-service --service-name $SERVICE_NAME --region eu-west-1 --profile landingzone"
echo ""
echo "  # View logs"
echo "  aws logs tail /aws/apprunner/$SERVICE_NAME --region eu-west-1 --profile landingzone"
echo ""
echo "  # Destroy infrastructure"
echo "  terraform destroy"
echo ""
echo -e "${GREEN}🎉 Private repository deployment completed successfully!${NC}" 