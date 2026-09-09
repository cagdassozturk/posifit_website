#!/bin/bash
# Precisely remove the old domain server block

echo "🔧 Removing old domain server block from nginx..."

# Backup first
echo "💾 Creating backup..."
sudo cp /etc/nginx/sites-available/renovation.legofit.eu /etc/nginx/sites-available/renovation.legofit.eu.backup.$(date +%Y%m%d_%H%M%S)

# Remove lines 138-142 (the old domain server block)
echo "🗑️  Removing server block (lines 138-142)..."
sudo sed -i '138,142d' /etc/nginx/sites-available/renovation.legofit.eu

# Test configuration
echo ""
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Configuration valid!"
    
    echo ""
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Successfully removed old domain block!"
    echo ""
    echo "🔍 Verifying removal:"
    if sudo grep -q "legofit-explorer" /etc/nginx/sites-available/renovation.legofit.eu; then
        echo "⚠️  Still found references:"
        sudo grep -n "legofit-explorer" /etc/nginx/sites-available/renovation.legofit.eu
    else
        echo "✅ No references to old domain found!"
    fi
    
else
    echo "❌ Configuration error! Restoring backup..."
    BACKUP=$(ls -t /etc/nginx/sites-available/renovation.legofit.eu.backup.* 2>/dev/null | head -1)
    sudo cp "$BACKUP" /etc/nginx/sites-available/renovation.legofit.eu
    echo "Backup restored. Please check manually."
    exit 1
fi

echo ""
echo "✅ Complete! Your server no longer responds to legofit-explorer.com"

