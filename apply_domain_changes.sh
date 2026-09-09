#!/bin/bash
# Script to apply domain migration from legofit-explorer.com to renovation.legofit.eu
# Run this script on your VPS server

echo "🔄 Applying domain migration to renovation.legofit.eu..."

# Stop services
echo "⏸️  Stopping services..."
sudo supervisorctl stop all
sudo systemctl stop nginx

# Remove old Nginx configuration
echo "🗑️  Removing old Nginx configuration..."
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer.com
sudo rm -f /etc/nginx/sites-available/legofit-explorer.com

# Copy new Nginx configuration
echo "📋 Copying new Nginx configuration..."
sudo cp nginx_config.conf /etc/nginx/sites-available/renovation.legofit.eu

# Enable new Nginx site
echo "✅ Enabling new Nginx site..."
sudo ln -sf /etc/nginx/sites-available/renovation.legofit.eu /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors. Please check!"
    exit 1
fi

# Update supervisor configuration
echo "📋 Updating supervisor configuration..."
sudo cp supervisor_config.conf /etc/supervisor/conf.d/legofit.conf

# Reload configurations
echo "🔄 Reloading configurations..."
sudo supervisorctl reread
sudo supervisorctl update

# Start services
echo "🚀 Starting services..."
sudo systemctl start nginx
sudo supervisorctl start all

# Check service status
echo "📊 Service status:"
sudo supervisorctl status

echo ""
echo "✅ Domain migration completed!"
echo "🌐 Your website should now be accessible at: http://renovation.legofit.eu"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Test your website at: http://renovation.legofit.eu"
echo "2. If everything works, run SSL setup: sudo bash setup_ssl.sh"
echo ""

