#!/bin/bash

# TradeLocker API - Local Development Script
# This script builds and runs the containerized API locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Building and running TradeLocker API locally${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating example .env file...${NC}"
           cat > .env << EOF
# TradeLocker API Configuration
TRADELOCKER_USERNAME=your_username
TRADELOCKER_PASSWORD=your_password
TRADELOCKER_SERVER=your_server
API_KEY=your-secret-api-key-here
EOF
    echo -e "${YELLOW}📝 Please edit .env file with your TradeLocker credentials${NC}"
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    echo -e "${YELLOW}📋 Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
    echo ""
fi

# Build the Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker-compose build
echo -e "${GREEN}✅ Docker image built successfully${NC}"
echo ""

# Run the container
echo -e "${YELLOW}🚀 Starting TradeLocker API...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ Container started${NC}"
echo ""

# Wait for the API to be ready
echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
sleep 10

# Test the health endpoint
echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
    echo ""
    echo -e "${BLUE}📋 API Information:${NC}"
    echo "  🌐 API URL: http://localhost:8000"
    echo "  📚 Documentation: http://localhost:8000/docs"
    echo "  🔍 Health Check: http://localhost:8000/health"
    echo ""
    echo -e "${BLUE}🧪 Test Commands:${NC}"
    echo "  # Health check"
    echo "  curl http://localhost:8000/health"
    echo ""
    echo "  # Get accounts"
    echo "  curl http://localhost:8000/accounts"
    echo ""
    echo "  # Get instruments"
    echo "  curl http://localhost:8000/instruments"
    echo ""
    echo "  # Get current price"
    echo "  curl http://localhost:8000/instruments/BTCUSD.TTF/price"
    echo ""
    echo "  # Create order (example)"
    echo "  curl -X POST http://localhost:8000/orders \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"symbol\":\"BTCUSD.TTF\",\"order_type\":\"market\",\"side\":\"buy\",\"quantity\":0.01}'"
    echo ""
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo ""
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker-compose logs
    echo ""
    echo -e "${YELLOW}🛠️  Troubleshooting:${NC}"
    echo "  1. Check your .env file has correct credentials"
    echo "  2. Ensure AWS credentials are configured"
    echo "  3. Check container logs: docker-compose logs"
    echo ""
fi

echo -e "${BLUE}📋 Useful Commands:${NC}"
echo "  # View logs"
echo "  docker-compose logs -f"
echo ""
echo "  # Stop the API"
echo "  docker-compose down"
echo ""
echo "  # Rebuild and restart"
echo "  docker-compose up --build -d"
echo "" 