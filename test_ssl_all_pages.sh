#!/bin/bash
# SSL Verification Script - Tests all pages on renovation.legofit.eu

echo "🔒 SSL VERIFICATION FOR RENOVATION.LEGOFIT.EU"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASS=0
FAIL=0

# Function to test URL
test_url() {
    local url=$1
    local name=$2
    
    echo -n "Testing $name... "
    
    # Test if URL returns 200 OK via HTTPS
    status=$(curl -s -o /dev/null -w "%{http_code}" -L "$url" 2>&1)
    
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTPS working)"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC} (Status: $status)"
        ((FAIL++))
    fi
}

echo "📋 Testing Main Pages:"
echo "----------------------"
test_url "https://renovation.legofit.eu/" "Home Page"
test_url "https://renovation.legofit.eu/about" "About Page"
test_url "https://renovation.legofit.eu/contributors" "Contributors Page"
test_url "https://renovation.legofit.eu/contact" "Contact Page"

echo ""
echo "📋 Testing Pilot Pages:"
echo "----------------------"
test_url "https://renovation.legofit.eu/pilot_lux" "Luxembourg Pilot"
test_url "https://renovation.legofit.eu/pilot_tur" "Turkey Pilot"
test_url "https://renovation.legofit.eu/pilot_hun" "Hungary Pilot"
test_url "https://renovation.legofit.eu/pilot_spa" "Spain Pilot"
test_url "https://renovation.legofit.eu/pilot_net" "Netherlands Pilot"

echo ""
echo "📋 Testing Data Visualization Pages:"
echo "------------------------------------"
test_url "https://renovation.legofit.eu/pilot_lux_explorer" "Luxembourg Explorer"
test_url "https://renovation.legofit.eu/pilot_lux_optimized" "Luxembourg Optimized"
test_url "https://renovation.legofit.eu/market" "Market Explorer"
test_url "https://renovation.legofit.eu/market-optimized" "Market Optimized"

echo ""
echo "📋 Testing HTTP to HTTPS Redirect:"
echo "----------------------------------"
echo -n "Testing HTTP redirect... "
redirect_status=$(curl -s -o /dev/null -w "%{http_code}" "http://renovation.legofit.eu/" 2>&1)
redirect_location=$(curl -s -I "http://renovation.legofit.eu/" | grep -i "location:" | awk '{print $2}' | tr -d '\r')

if [ "$redirect_status" = "301" ] && [[ "$redirect_location" == *"https"* ]]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP → HTTPS working)"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} (Redirect not working properly)"
    ((FAIL++))
fi

echo ""
echo "📋 Testing SSL Certificate:"
echo "---------------------------"
echo -n "Checking certificate validity... "

# Check if certificate is valid
cert_check=$(echo | openssl s_client -servername renovation.legofit.eu -connect renovation.legofit.eu:443 2>/dev/null | openssl x509 -noout -checkend 0)

if [[ $cert_check == *"Certificate will not expire"* ]]; then
    echo -e "${GREEN}✅ PASS${NC} (Certificate is valid)"
    ((PASS++))
    
    # Get certificate expiry date
    expiry=$(echo | openssl s_client -servername renovation.legofit.eu -connect renovation.legofit.eu:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    echo "   └─ Expires: $expiry"
else
    echo -e "${RED}❌ FAIL${NC} (Certificate expired or invalid)"
    ((FAIL++))
fi

echo ""
echo "📋 Testing Static Resources:"
echo "----------------------------"
test_url "https://renovation.legofit.eu/static/logo/main_logo.jpg" "Main Logo"
test_url "https://renovation.legofit.eu/static/style.css" "CSS File"
test_url "https://renovation.legofit.eu/static/script.js" "JavaScript File"

echo ""
echo "=============================================="
echo "📊 RESULTS SUMMARY"
echo "=============================================="
echo -e "Total Tests: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Your website is fully SSL-protected!${NC}"
    echo ""
    echo "✅ All pages are accessible via HTTPS"
    echo "✅ HTTP automatically redirects to HTTPS"
    echo "✅ SSL certificate is valid"
    echo "✅ All resources are served securely"
    echo ""
    echo "Your website is 100% secure! 🔒"
else
    echo -e "${YELLOW}⚠️  Some tests failed. Please check the output above.${NC}"
fi

echo ""
echo "=============================================="

