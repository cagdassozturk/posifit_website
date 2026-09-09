#!/bin/bash
# Simple deployment script for Turkiye pages
# Assumes production runs from current directory

set -e

echo "======================================"
echo "  DEPLOYING TURKIYE PAGES"
echo "======================================"
echo ""

# Update Nginx config
echo "→ Updating Nginx configuration..."
sudo cp nginx_config.conf /etc/nginx/sites-available/legofit || \
sudo cp nginx_config.conf /etc/nginx/sites-available/default || \
sudo cp nginx_config.conf /etc/nginx/conf.d/legofit.conf

# Test nginx config
echo "→ Testing Nginx configuration..."
sudo nginx -t

# Reload Nginx
echo "→ Reloading Nginx..."
sudo systemctl reload nginx || sudo service nginx reload

echo ""
echo "→ Restarting Dash app via Supervisor..."
# Try supervisor restart
sudo supervisorctl restart legofit-dash 2>/dev/null || {
    echo "  (Supervisor not found, trying manual restart...)"
    
    # Find and kill dash_app.py process
    pkill -f "dash_app.py" || true
    sleep 2
    
    # Start dash_app in background
    cd /var/www/legofit-explorer.com
    nohup venv/bin/python dash_app.py > /var/log/legofit-dash.out.log 2>&1 &
    echo "  → Dash app restarted manually"
}

echo ""
echo "======================================"
echo "  ✓ DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "Turkiye pages should now be accessible at:"
echo "  → https://renovation.legofit.eu/pilot_tur_explorer"
echo "  → https://renovation.legofit.eu/pilot_tur_optimized"
echo ""
echo "To verify:"
echo "  curl -I https://renovation.legofit.eu/pilot_tur_explorer"
echo ""

