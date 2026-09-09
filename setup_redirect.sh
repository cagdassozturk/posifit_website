#!/bin/bash
# Setup redirect from old domain to new domain

echo "🔄 Setting up redirect from legofit-explorer.com to renovation.legofit.eu..."

# Copy redirect configuration
echo "📋 Creating redirect configuration..."
sudo cp nginx_redirect_old_domain.conf /etc/nginx/sites-available/legofit-explorer-redirect.conf

# Disable old site configuration (if exists)
echo "🗑️  Disabling old site configuration..."
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer.com
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer-redirect.conf

# Enable redirect configuration
echo "✅ Enabling redirect configuration..."
sudo ln -sf /etc/nginx/sites-available/legofit-explorer-redirect.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Configuration is valid"
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo ""
    echo "✅ Redirect setup complete!"
    echo "🌐 Testing redirect..."
    echo ""
    curl -I http://legofit-explorer.com 2>/dev/null | grep -i location || echo "⚠️  Could not test redirect"
    echo ""
    echo "📋 All visitors to legofit-explorer.com will now be redirected to renovation.legofit.eu"
else
    echo "❌ Nginx configuration has errors!"
    exit 1
fi

