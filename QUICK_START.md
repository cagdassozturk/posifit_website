# 🚀 Quick Start Guide - Domain Migration

## ✅ Migration Status: READY TO DEPLOY

All code changes have been completed. Your DNS is already configured correctly!

## 📋 Deployment Steps (Run in order)

### Step 1: Verify Changes
```bash
cd /var/www/legofit-explorer.com
bash verify_migration.sh
```

### Step 2: Apply Domain Changes
```bash
sudo bash apply_domain_changes.sh
```
This will:
- Stop current services
- Update Nginx configuration
- Update Supervisor configuration
- Restart all services

### Step 3: Test HTTP
```bash
curl -I http://renovation.legofit.eu
```
Or open in browser: http://renovation.legofit.eu

### Step 4: Setup SSL Certificate
```bash
sudo bash setup_ssl.sh
```
This will:
- Install certbot (if needed)
- Request SSL certificate from Let's Encrypt
- Configure HTTPS
- Auto-renew setup

### Step 5: Test HTTPS
```bash
curl -I https://renovation.legofit.eu
```
Or open in browser: https://renovation.legofit.eu

## 🎯 What Was Changed

### Configuration Files:
- ✅ `nginx_config.conf` - Server name updated
- ✅ `supervisor_config.conf` - BASE_URL environment variable updated
- ✅ `main.py` - Redirect URLs updated
- ✅ `dash_app.py` - All 35+ domain references updated
- ✅ `deploy_to_hostinger.sh` - Deployment script updated
- ✅ `deploy_hostinger.py` - Python deployment script updated
- ✅ `DEPLOYMENT_GUIDE_PRODUCTION.md` - Documentation updated

### Scripts Created:
- ✅ `apply_domain_changes.sh` - Applies all configuration changes
- ✅ `setup_ssl.sh` - Sets up SSL certificate
- ✅ `verify_migration.sh` - Verifies all changes
- ✅ `DOMAIN_MIGRATION_SUMMARY.md` - Detailed migration documentation

## ⚡ One-Command Deployment

If you're confident, run all steps at once:
```bash
cd /var/www/legofit-explorer.com && \
sudo bash apply_domain_changes.sh && \
sleep 5 && \
curl -I http://renovation.legofit.eu && \
sudo bash setup_ssl.sh
```

## 🔍 Troubleshooting

### If site doesn't load:
```bash
# Check Nginx
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Check application services
sudo supervisorctl status
sudo tail -f /var/log/legofit-flask.err.log
sudo tail -f /var/log/legofit-dash.err.log
```

### If SSL fails:
1. Wait 5-10 minutes for DNS propagation
2. Ensure ports 80 and 443 are open:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```
3. Verify DNS:
   ```bash
   dig +short renovation.legofit.eu
   ```

## 📞 Service Management

```bash
# Restart everything
sudo supervisorctl restart all
sudo systemctl restart nginx

# View logs
sudo supervisorctl tail -f legofit-flask
sudo supervisorctl tail -f legofit-dash

# Service status
sudo supervisorctl status
```

## ✨ Expected Result

After successful migration:
- ✅ `http://renovation.legofit.eu` → Your website
- ✅ `https://renovation.legofit.eu` → Secure HTTPS
- ✅ All internal links working
- ✅ SSL certificate valid
- ✅ Auto-redirect HTTP → HTTPS

## 📝 Notes

- Your DNS is already configured and pointing to: 72.60.180.76 ✅
- The services show errors because they're still using old configuration
- After running `apply_domain_changes.sh`, services will restart with new config
- SSL setup takes 2-3 minutes
- Certificate auto-renews every 90 days

## 🎉 That's it!

Your website will be live at: **https://renovation.legofit.eu**

