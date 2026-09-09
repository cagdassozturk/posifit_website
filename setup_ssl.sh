#!/bin/bash
# SSL Certificate Setup Script for renovation.legofit.eu

echo "🔒 Setting up SSL certificate for renovation.legofit.eu..."

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
fi

# Request SSL certificate
echo "📜 Requesting SSL certificate..."
echo "⚠️  You will need to provide an email address for important renewal notifications"
echo ""

# Run certbot
sudo certbot --nginx -d renovation.legofit.eu -d www.renovation.legofit.eu

# Check if certificate was issued
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL certificate installed successfully!"
    echo "🌐 Your website is now accessible at: https://renovation.legofit.eu"
    echo ""
    echo "📋 Certificate will auto-renew. To test renewal:"
    echo "   sudo certbot renew --dry-run"
    echo ""
else
    echo ""
    echo "❌ SSL certificate installation failed!"
    echo "Please check:"
    echo "1. DNS is correctly pointing to this server"
    echo "2. Port 80 and 443 are open in firewall"
    echo "3. Domain renovation.legofit.eu is accessible"
    echo ""
fi

# Restart services to apply SSL
echo "🔄 Restarting services..."
sudo systemctl restart nginx
sudo supervisorctl restart all

echo ""
echo "📊 Current Nginx status:"
sudo systemctl status nginx --no-pager -l

