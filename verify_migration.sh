#!/bin/bash
# Verification script to check if all files have been updated correctly

echo "🔍 Verifying domain migration..."
echo "========================================"

ERRORS=0
WARNINGS=0

# Check if old domain still exists in key files
echo ""
echo "1️⃣  Checking for old domain references..."

if grep -q "legofit-explorer\.com" nginx_config.conf 2>/dev/null; then
    echo "❌ ERROR: Old domain found in nginx_config.conf"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ nginx_config.conf updated"
fi

if grep -q "legofit-explorer\.com" supervisor_config.conf 2>/dev/null; then
    echo "❌ ERROR: Old domain found in supervisor_config.conf"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ supervisor_config.conf updated"
fi

if grep -q "legofit-explorer\.com" main.py 2>/dev/null; then
    echo "❌ ERROR: Old domain found in main.py"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ main.py updated"
fi

if grep -q "legofit-explorer\.com" dash_app.py 2>/dev/null; then
    echo "❌ ERROR: Old domain found in dash_app.py"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ dash_app.py updated"
fi

# Check if new domain exists in key files
echo ""
echo "2️⃣  Checking for new domain..."

if grep -q "renovation\.legofit\.eu" nginx_config.conf 2>/dev/null; then
    echo "✅ New domain found in nginx_config.conf"
else
    echo "❌ ERROR: New domain NOT found in nginx_config.conf"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "renovation\.legofit\.eu" supervisor_config.conf 2>/dev/null; then
    echo "✅ New domain found in supervisor_config.conf"
else
    echo "❌ ERROR: New domain NOT found in supervisor_config.conf"
    ERRORS=$((ERRORS + 1))
fi

# Check if deployment scripts exist
echo ""
echo "3️⃣  Checking deployment scripts..."

if [ -x "apply_domain_changes.sh" ]; then
    echo "✅ apply_domain_changes.sh is executable"
else
    echo "⚠️  WARNING: apply_domain_changes.sh is not executable"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -x "setup_ssl.sh" ]; then
    echo "✅ setup_ssl.sh is executable"
else
    echo "⚠️  WARNING: setup_ssl.sh is not executable"
    WARNINGS=$((WARNINGS + 1))
fi

# Check current services
echo ""
echo "4️⃣  Checking current services..."

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "⚠️  WARNING: Nginx is not running"
    WARNINGS=$((WARNINGS + 1))
fi

if command -v supervisorctl &> /dev/null; then
    FLASK_STATUS=$(sudo supervisorctl status legofit-flask 2>/dev/null | awk '{print $2}')
    DASH_STATUS=$(sudo supervisorctl status legofit-dash 2>/dev/null | awk '{print $2}')
    
    if [ "$FLASK_STATUS" = "RUNNING" ]; then
        echo "✅ Flask service is running"
    else
        echo "⚠️  WARNING: Flask service is not running (Status: $FLASK_STATUS)"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if [ "$DASH_STATUS" = "RUNNING" ]; then
        echo "✅ Dash service is running"
    else
        echo "⚠️  WARNING: Dash service is not running (Status: $DASH_STATUS)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check DNS
echo ""
echo "5️⃣  Checking DNS resolution..."

if command -v dig &> /dev/null; then
    DNS_IP=$(dig +short renovation.legofit.eu | head -1)
    if [ -n "$DNS_IP" ]; then
        echo "✅ DNS resolves to: $DNS_IP"
        
        # Get current server IP
        if command -v hostname &> /dev/null; then
            SERVER_IP=$(hostname -I | awk '{print $1}')
            if [ "$DNS_IP" = "$SERVER_IP" ]; then
                echo "✅ DNS points to this server"
            else
                echo "⚠️  WARNING: DNS ($DNS_IP) doesn't match server IP ($SERVER_IP)"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    else
        echo "⚠️  WARNING: DNS not resolving for renovation.legofit.eu"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "ℹ️  dig command not available, skipping DNS check"
fi

# Summary
echo ""
echo "========================================"
echo "📊 VERIFICATION SUMMARY"
echo "========================================"
echo "❌ Errors: $ERRORS"
echo "⚠️  Warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo "✅ All critical checks passed!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Review the warnings (if any)"
    echo "2. Run: sudo bash apply_domain_changes.sh"
    echo "3. Test: curl -I http://renovation.legofit.eu"
    echo "4. Run: sudo bash setup_ssl.sh"
    echo "5. Test: curl -I https://renovation.legofit.eu"
    exit 0
else
    echo "❌ Please fix the errors before proceeding!"
    exit 1
fi

