# Domain Migration Summary
## From: legofit-explorer.com → To: renovation.legofit.eu

## ✅ Files Updated

### 1. **nginx_config.conf**
- Changed `server_name` from `legofit-explorer.com www.legofit-explorer.com` to `renovation.legofit.eu www.renovation.legofit.eu`
- Updated domain references in comments

### 2. **supervisor_config.conf**
- Updated `BASE_URL` environment variable from `https://legofit-explorer.com` to `https://renovation.legofit.eu`
- Applied to both Flask and Dash server configurations

### 3. **main.py**
- Updated redirect URLs in:
  - `pilot_lux_explorer_redirect()` function
  - `pilot_lux_optimized_redirect()` function

### 4. **dash_app.py**
- Replaced all 35+ occurrences of `https://legofit-explorer.com` with `https://renovation.legofit.eu`
- Updated URLs in:
  - External stylesheets
  - Navigation bar links
  - Footer links
  - Image sources
  - All href attributes

### 5. **deploy_to_hostinger.sh**
- Updated Nginx config file path
- Updated SSL certificate domain parameters
- Updated deployment completion messages

### 6. **deploy_hostinger.py**
- Updated production URL variable
- Updated domain references in comments and print statements
- Updated bash script generation

### 7. **DEPLOYMENT_GUIDE_PRODUCTION.md**
- Updated all domain references in documentation
- Updated configuration examples
- Updated SSL setup instructions

## 🚀 Deployment Scripts Created

### 1. **apply_domain_changes.sh**
- Stops current services
- Removes old Nginx configuration
- Applies new configuration
- Restarts services
- **Run this first to apply changes**

### 2. **setup_ssl.sh**
- Installs certbot if needed
- Requests SSL certificate for new domain
- Configures HTTPS
- **Run this after verifying HTTP works**

## 📋 Deployment Steps

### Step 1: Apply Configuration Changes
```bash
cd /var/www/legofit-explorer.com
sudo bash apply_domain_changes.sh
```

### Step 2: Verify HTTP Access
```bash
# Test if your site is accessible
curl -I http://renovation.legofit.eu
```

### Step 3: Setup SSL Certificate
```bash
# Only run this after HTTP works
sudo bash setup_ssl.sh
```

### Step 4: Verify HTTPS Access
```bash
# Test if HTTPS works
curl -I https://renovation.legofit.eu
```

## 🔍 Troubleshooting

### If website is not accessible:
1. **Check DNS:**
   ```bash
   dig renovation.legofit.eu
   nslookup renovation.legofit.eu
   ```

2. **Check Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Check Services:**
   ```bash
   sudo supervisorctl status
   sudo tail -f /var/log/legofit-flask.err.log
   sudo tail -f /var/log/legofit-dash.err.log
   ```

4. **Check Firewall:**
   ```bash
   sudo ufw status
   # Ensure ports 80 and 443 are open
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

### If SSL setup fails:
1. **Verify DNS propagation** (may take up to 48 hours)
2. **Ensure ports 80 and 443 are accessible** from the internet
3. **Check if domain points to correct IP:**
   ```bash
   dig +short renovation.legofit.eu
   # Should return your VPS IP address
   ```

## ⚙️ Service Management Commands

### Restart Services:
```bash
sudo supervisorctl restart all
sudo systemctl restart nginx
```

### View Logs:
```bash
# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
sudo tail -f /var/log/legofit-flask.out.log
sudo tail -f /var/log/legofit-dash.out.log
```

### Service Status:
```bash
sudo supervisorctl status
sudo systemctl status nginx
```

## 🔒 SSL Certificate Renewal

Certbot automatically renews certificates. To test renewal:
```bash
sudo certbot renew --dry-run
```

## ✨ What Changed in the Application

### User-Visible Changes:
- All internal links now point to `renovation.legofit.eu`
- SSL certificate will be for the new domain
- All redirects updated to new domain

### Backend Changes:
- Environment variable `BASE_URL` updated
- Nginx reverse proxy configured for new domain
- Supervisor process management updated

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review application logs
3. Verify DNS settings with your domain provider
4. Ensure firewall allows HTTP/HTTPS traffic

## ⚡ Quick Reference

| Service | Port | Log Location |
|---------|------|--------------|
| Flask | 8050 | /var/log/legofit-flask.{out,err}.log |
| Dash | 8051 | /var/log/legofit-dash.{out,err}.log |
| Nginx | 80, 443 | /var/log/nginx/{access,error}.log |

## 🎯 Expected Result

After successful migration:
- ✅ Website accessible at `http://renovation.legofit.eu`
- ✅ HTTPS enabled at `https://renovation.legofit.eu`
- ✅ All internal links working correctly
- ✅ SSL certificate valid
- ✅ Auto-redirect from HTTP to HTTPS (if configured)

