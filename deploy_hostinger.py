#!/usr/bin/env python3
"""
Hostinger VPS deployment script for POSIFIT website
Optimized for 25-30 concurrent users with domain renovation.legofit.eu
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        print(f"Error output: {e.stderr}")
        return None

def update_urls_for_production():
    """Update hardcoded localhost URLs to production URLs"""
    production_url = "https://renovation.legofit.eu"
    
    files_to_update = [
        'dash_app.py',
        'main.py'
    ]
    
    for filename in files_to_update:
        if os.path.exists(filename):
            print(f"📝 Updating URLs in {filename}...")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace localhost URLs with production URL
            content = content.replace('http://localhost:8050', production_url)
            content = content.replace('http://localhost:8051', production_url)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated {filename}")
        else:
            print(f"⚠️  File {filename} not found")

def create_deployment_script():
    """Create deployment script for Hostinger VPS"""
    deployment_script = '''#!/bin/bash
# POSIFIT Hostinger VPS Deployment Script
# Run this script on your Hostinger VPS

echo "🚀 Starting POSIFIT deployment on Hostinger VPS..."

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

echo "✅ POSIFIT deployment completed!"
echo "🌐 Your website should be available at: https://renovation.legofit.eu"
echo "📊 Monitor logs with: sudo supervisorctl status"
'''
    
    with open('deploy_to_hostinger.sh', 'w') as f:
        f.write(deployment_script)
    
    # Make it executable
    os.chmod('deploy_to_hostinger.sh', 0o755)
    print("✅ Created deploy_to_hostinger.sh")

def create_requirements_production():
    """Create production requirements file"""
    production_requirements = '''dash>=2.14,<3
dash-bootstrap-components>=1.6,<2
pandas>=2.0,<3
plotly>=5.18,<6
numpy>=1.24,<2
scikit-learn>=1.3,<2
flask>=2.3,<3
gunicorn>=21.0,<22
supervisor>=4.2,<5
redis>=4.5,<5
flask-caching>=2.0,<3
'''
    
    with open('requirements_production.txt', 'w') as f:
        f.write(production_requirements)
    
    print("✅ Created requirements_production.txt")

def main():
    """Main deployment preparation"""
    print("🚀 Preparing POSIFIT for Hostinger VPS deployment...")
    print("🎯 Optimized for 25-30 concurrent users")
    print("🌐 Domain: renovation.legofit.eu")
    
    # Update URLs for production
    update_urls_for_production()
    
    # Create deployment script
    create_deployment_script()
    
    # Create production requirements
    create_requirements_production()
    
    print("\n✅ Hostinger deployment preparation complete!")
    print("\n📋 Next steps:")
    print("1. Purchase Hostinger VPS 2 plan ($7.99/month)")
    print("2. Register domain renovation.legofit.eu")
    print("3. Upload your code to the VPS")
    print("4. Run: bash deploy_to_hostinger.sh")
    print("5. Your site will be live at: https://renovation.legofit.eu")
    
    print("\n💰 Total monthly cost: $9.24")
    print("   - Hostinger VPS 2: $7.99")
    print("   - Domain: $1.25")
    
    print("\n🔧 Manual steps on Hostinger VPS:")
    print("1. SSH into your VPS: ssh root@your-server-ip")
    print("2. Upload your code (use SCP or Git)")
    print("3. Run: bash deploy_to_hostinger.sh")
    print("4. Configure domain DNS to point to your VPS IP")
    
    print("\n📞 Support:")
    print("- Check logs: sudo supervisorctl status")
    print("- Restart services: sudo supervisorctl restart all")
    print("- Nginx logs: sudo tail -f /var/log/nginx/error.log")

if __name__ == "__main__":
    main()
