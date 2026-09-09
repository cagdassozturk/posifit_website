#!/bin/bash
# Complete cleanup of legofit-explorer.com from the server

echo "🧹 COMPLETE CLEANUP: Removing all traces of legofit-explorer.com"
echo "================================================================"

# 1. Check DNS status first
echo ""
echo "1️⃣  Checking DNS status..."
DNS_IP=$(dig +short legofit-explorer.com 2>/dev/null | head -1)
if [ -n "$DNS_IP" ]; then
    echo "⚠️  WARNING: DNS still resolves to: $DNS_IP"
    echo "   You need to delete this from Hostinger DNS panel!"
else
    echo "✅ DNS not resolving (good!)"
fi

# 2. Remove any nginx configurations
echo ""
echo "2️⃣  Removing nginx configurations..."
sudo rm -f /etc/nginx/sites-enabled/legofit-explorer* 2>/dev/null
sudo rm -f /etc/nginx/sites-available/legofit-explorer* 2>/dev/null
echo "✅ Nginx configs removed"

# 3. Delete SSL certificates
echo ""
echo "3️⃣  Deleting SSL certificates for legofit-explorer.com..."
if [ -d "/etc/letsencrypt/live/legofit-explorer.com" ]; then
    sudo certbot delete --cert-name legofit-explorer.com --non-interactive
    echo "✅ SSL certificate deleted"
else
    echo "✅ No SSL certificate found (already clean)"
fi

# 4. Test and reload nginx
echo ""
echo "4️⃣  Testing and reloading nginx..."
if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx configuration error!"
    exit 1
fi

# 5. Final verification
echo ""
echo "5️⃣  Final verification..."
echo ""
echo "📊 Remaining SSL certificates:"
sudo ls -1 /etc/letsencrypt/live/ 2>/dev/null | grep -v README || echo "None"

echo ""
echo "📊 Active nginx sites:"
ls -1 /etc/nginx/sites-enabled/ 2>/dev/null || echo "None"

echo ""
echo "📊 Server names in nginx:"
sudo grep "server_name" /etc/nginx/sites-enabled/* 2>/dev/null || echo "None"

echo ""
echo "================================================================"
echo "✅ CLEANUP COMPLETE!"
echo ""
echo "📋 Summary:"
echo "   ✅ SSL certificate for legofit-explorer.com: DELETED"
echo "   ✅ Nginx configurations: REMOVED"
echo "   ✅ Server only responds to: renovation.legofit.eu"
echo ""

if [ -n "$DNS_IP" ]; then
    echo "⚠️  IMPORTANT: DNS STILL ACTIVE!"
    echo ""
    echo "To complete removal, go to Hostinger:"
    echo "1. Login: https://hpanel.hostinger.com"
    echo "2. Go to: Domains → legofit-explorer.com → DNS"
    echo "3. Delete the A record pointing to: $DNS_IP"
    echo "4. Save changes"
    echo ""
else
    echo "✅ All done! The old domain is completely removed."
fi

