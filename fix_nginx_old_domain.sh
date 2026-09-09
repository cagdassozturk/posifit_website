#!/bin/bash
# Remove the old domain server block from nginx configuration

echo "🔧 Removing old domain server block from nginx configuration..."

# Backup the current configuration
echo "💾 Creating backup..."
sudo cp /etc/nginx/sites-available/renovation.legofit.eu /etc/nginx/sites-available/renovation.legofit.eu.backup.$(date +%Y%m%d_%H%M%S)

# Remove the server block for legofit-explorer.com (lines 138-142)
echo "🗑️  Removing old domain server block..."
sudo sed -i '/^server {$/,/^}$/ {
    /server_name legofit-explorer.com www.legofit-explorer.com/,/^}$/ {
        d
    }
}' /etc/nginx/sites-available/renovation.legofit.eu

# Also fix the comment at the top
echo "📝 Updating comment..."
sudo sed -i 's/# Domain: legofit-explorer.com/# Domain: renovation.legofit.eu/' /etc/nginx/sites-available/renovation.legofit.eu

echo ""
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    
    echo ""
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Old domain server block removed successfully!"
    echo ""
    echo "🔍 Verifying - checking for old domain references:"
    if sudo grep -q "legofit-explorer\.com" /etc/nginx/sites-available/renovation.legofit.eu; then
        echo "⚠️  Old domain still found in config:"
        sudo grep -n "legofit-explorer" /etc/nginx/sites-available/renovation.legofit.eu
    else
        echo "✅ No old domain references found!"
    fi
    
    echo ""
    echo "📊 Current server_name configurations:"
    sudo grep "server_name" /etc/nginx/sites-available/renovation.legofit.eu
    
else
    echo "❌ Nginx configuration has errors!"
    echo "Restoring backup..."
    LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/renovation.legofit.eu.backup.* 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        sudo cp "$LATEST_BACKUP" /etc/nginx/sites-available/renovation.legofit.eu
        echo "✅ Backup restored"
    fi
    exit 1
fi

echo ""
echo "✅ Done! legofit-explorer.com should no longer respond."
echo "🌐 Your site is only accessible at: renovation.legofit.eu"

