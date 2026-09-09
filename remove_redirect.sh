#!/bin/bash
# Remove redirect configuration for legofit-explorer.com

echo "🗑️  Removing redirect configuration for legofit-explorer.com..."

# Remove redirect configuration from sites-enabled
echo "📋 Removing from sites-enabled..."
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer-redirect.conf
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer.com
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer-redirect

# Remove redirect configuration from sites-available
echo "📋 Removing from sites-available..."
sudo rm -f /etc/nginx/sites-available/legofit-explorer-redirect.conf
sudo rm -f /etc/nginx/sites-available/legofit-explorer.com
sudo rm -f /etc/nginx/sites-available/legofit-explorer-redirect

# List remaining nginx configurations
echo ""
echo "📊 Remaining nginx configurations:"
ls -la /etc/nginx/sites-enabled/

echo ""
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    
    echo ""
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Redirect configuration removed successfully!"
    echo ""
    echo "📋 Current active sites:"
    ls -la /etc/nginx/sites-enabled/
    echo ""
    echo "🌐 Your site is now only accessible at: renovation.legofit.eu"
    echo "🚫 legofit-explorer.com will stop working once DNS propagates (24-48 hours)"
else
    echo "❌ Nginx configuration has errors!"
    echo "Please check the configuration."
    exit 1
fi

echo ""
echo "✅ Done! The redirect has been removed from your server."

