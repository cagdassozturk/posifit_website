#!/bin/bash
# Deployment script for Turkiye pilot pages
# Run this script to deploy Turkiye pages to production

set -e  # Exit on any error

echo "======================================"
echo "   TURKIYE PAGES DEPLOYMENT SCRIPT"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEV_DIR="/var/www/legofit-explorer.com"
PROD_DIR="/root/legofit-website"
NGINX_CONFIG="/etc/nginx/sites-available/legofit"

echo -e "${YELLOW}Step 1: Checking directories...${NC}"
if [ ! -d "$DEV_DIR" ]; then
    echo -e "${RED}Error: Development directory not found: $DEV_DIR${NC}"
    exit 1
fi

if [ ! -d "$PROD_DIR" ]; then
    echo -e "${RED}Error: Production directory not found: $PROD_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Directories verified${NC}"
echo ""

echo -e "${YELLOW}Step 2: Copying new Turkiye page files...${NC}"
cp -v "$DEV_DIR/pages/turkiye_explorer.py" "$PROD_DIR/pages/"
cp -v "$DEV_DIR/pages/turkiye_optimized.py" "$PROD_DIR/pages/"
echo -e "${GREEN}✓ Page files copied${NC}"
echo ""

echo -e "${YELLOW}Step 3: Copying new Turkiye callback files...${NC}"
cp -v "$DEV_DIR/callbacks/turkiye_explorer_callbacks.py" "$PROD_DIR/callbacks/"
cp -v "$DEV_DIR/callbacks/turkiye_optimized_callbacks.py" "$PROD_DIR/callbacks/"
cp -v "$DEV_DIR/callbacks/turkiye_comparison_callbacks.py" "$PROD_DIR/callbacks/"
cp -v "$DEV_DIR/callbacks/turkiye_optimized_comparison_callbacks.py" "$PROD_DIR/callbacks/"
echo -e "${GREEN}✓ Callback files copied${NC}"
echo ""

echo -e "${YELLOW}Step 4: Copying Turkiye utility files...${NC}"
cp -v "$DEV_DIR/utils/turkiye_plots.py" "$PROD_DIR/utils/"
echo -e "${GREEN}✓ Utility files copied${NC}"
echo ""

echo -e "${YELLOW}Step 5: Updating main app files...${NC}"
cp -v "$DEV_DIR/app.py" "$PROD_DIR/"
cp -v "$DEV_DIR/dash_app.py" "$PROD_DIR/"
cp -v "$DEV_DIR/main.py" "$PROD_DIR/"
echo -e "${GREEN}✓ Main app files updated${NC}"
echo ""

echo -e "${YELLOW}Step 6: Updating Nginx configuration...${NC}"
# Backup current nginx config
if [ -f "$NGINX_CONFIG" ]; then
    sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  → Backup created: $NGINX_CONFIG.backup.*"
fi

# Copy new nginx config
sudo cp "$DEV_DIR/nginx_config.conf" "$NGINX_CONFIG"
echo -e "${GREEN}✓ Nginx config updated${NC}"
echo ""

echo -e "${YELLOW}Step 7: Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx config is valid${NC}"
else
    echo -e "${RED}✗ Nginx config has errors! Restoring backup...${NC}"
    sudo cp "$NGINX_CONFIG.backup.*" "$NGINX_CONFIG" 2>/dev/null || true
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 8: Reloading Nginx...${NC}"
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"
echo ""

echo -e "${YELLOW}Step 9: Restarting Supervisor services...${NC}"
echo "  → Stopping services..."
sudo supervisorctl stop legofit-dash
sudo supervisorctl stop legofit-flask

echo "  → Waiting 3 seconds..."
sleep 3

echo "  → Starting services..."
sudo supervisorctl start legofit-flask
sudo supervisorctl start legofit-dash

echo "  → Waiting for services to initialize..."
sleep 5
echo -e "${GREEN}✓ Services restarted${NC}"
echo ""

echo -e "${YELLOW}Step 10: Checking service status...${NC}"
sudo supervisorctl status legofit-flask
sudo supervisorctl status legofit-dash
echo ""

echo -e "${GREEN}======================================"
echo "   ✓ DEPLOYMENT COMPLETE!"
echo "======================================${NC}"
echo ""
echo "Turkiye pages are now available at:"
echo "  → https://renovation.legofit.eu/pilot_tur_explorer"
echo "  → https://renovation.legofit.eu/pilot_tur_optimized"
echo ""
echo "To verify deployment:"
echo "  1. Visit the URLs above"
echo "  2. Check logs: sudo tail -f /var/log/legofit-dash.err.log"
echo "  3. Check supervisor: sudo supervisorctl status"
echo ""
echo -e "${YELLOW}Note: If you see errors, check the log files:${NC}"
echo "  - Flask: /var/log/legofit-flask.err.log"
echo "  - Dash:  /var/log/legofit-dash.err.log"
echo ""

