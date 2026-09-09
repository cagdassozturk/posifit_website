#!/bin/bash
# LEGOFIT Hostinger VPS Deployment Script
# Run this script on your Hostinger VPS

echo "🚀 Starting LEGOFIT deployment on Hostinger VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx git supervisor redis-server

# Install Node.js (for some Dash components)
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /root/legofit-website
cd /root/legofit-website

# Clone repository (replace with your actual repository)
echo "📥 Cloning repository..."
# git clone https://github.com/yourusername/legofit-website.git .

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn supervisor

# Copy configuration files
echo "⚙️ Setting up configuration files..."
sudo cp nginx_config.conf /etc/nginx/sites-available/renovation.legofit.eu
sudo cp supervisor_config.conf /etc/supervisor/conf.d/legofit.conf

# Enable Nginx site
echo "🌐 Configuring Nginx..."
sudo ln -sf /etc/nginx/sites-available/renovation.legofit.eu /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Start services
echo "🚀 Starting services..."
sudo systemctl restart nginx
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Setup SSL certificate
echo "🔒 Setting up SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d renovation.legofit.eu -d www.renovation.legofit.eu --non-interactive --agree-tos --email your-email@example.com

echo "✅ LEGOFIT deployment completed!"
echo "🌐 Your website should be available at: https://renovation.legofit.eu"
echo "📊 Monitor logs with: sudo supervisorctl status"
