#!/bin/bash

set -e

echo "🚀 VaultZero Docker Deployment"
echo "================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📋 Checking Docker installation...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    echo "Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker installed${NC}"
echo ""

echo -e "${BLUE}📋 Checking .env file...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Creating .env template${NC}"
    cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_anthropic_key_here
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
    echo -e "${YELLOW}⚠️  Edit .env and add your API key${NC}"
    exit 1
fi

source .env
if [ "$ANTHROPIC_API_KEY" = "your_anthropic_key_here" ] || [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ Set ANTHROPIC_API_KEY in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

echo -e "${BLUE}📋 Building Docker image...${NC}"
docker-compose build

echo ""
echo -e "${GREEN}✅ Image built${NC}"
echo ""

echo -e "${BLUE}📋 Starting VaultZero...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✅ Container started${NC}"
echo ""

sleep 15

if ! docker ps | grep -q "vaultzero-app"; then
    echo -e "${RED}❌ Failed to start${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}     VaultZero is running! 🎉        ${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}🌐 Access: http://localhost:8501${NC}"
echo ""
echo -e "${BLUE}📊 Commands:${NC}"
echo "   Logs:    docker-compose logs -f"
echo "   Stop:    docker-compose down"
echo "   Restart: docker-compose restart"
echo ""