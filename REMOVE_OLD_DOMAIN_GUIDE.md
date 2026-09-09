# Guide: Remove or Redirect Old Domain (legofit-explorer.com)

## Current Situation
- ✅ New domain `renovation.legofit.eu` is working
- ⚠️  Old domain `legofit-explorer.com` still accessible
- Both domains point to the same server

## Option 1: Redirect Old Domain to New (RECOMMENDED) ⭐

**Why?** Visitors with bookmarks or old links will automatically find your new site.

### Steps:

1. **Apply redirect configuration:**
   ```bash
   cd /var/www/legofit-explorer.com
   sudo bash setup_redirect.sh
   ```

2. **Test the redirect:**
   ```bash
   curl -I http://legofit-explorer.com
   # Should show: Location: https://renovation.legofit.eu
   ```

3. **Done!** Visitors to old domain will be automatically redirected.

### What happens:
- `http://legofit-explorer.com` → `https://renovation.legofit.eu`
- `https://legofit-explorer.com` → `https://renovation.legofit.eu`
- All pages preserve their paths (e.g., `/about` → `/about`)

---

## Option 2: Completely Remove Old Domain

**Why?** You want to completely disable the old domain immediately.

### Steps in Hostinger:

1. **Login to Hostinger:**
   - Go to https://hpanel.hostinger.com
   - Login with your credentials

2. **Go to DNS Management:**
   - Click on "Domains" in the left menu
   - Find `legofit-explorer.com`
   - Click "Manage"

3. **Remove or Modify DNS Records:**

   **Option 2A - Remove DNS Records (Domain becomes inaccessible):**
   - Click on "DNS / Nameservers"
   - Find the `A` record pointing to your server IP
   - Delete the `A` record
   - Click "Save"
   - **Note:** DNS changes take 24-48 hours to propagate

   **Option 2B - Point to Different Server:**
   - Change the `A` record IP to a different server
   - Or point to a placeholder page

4. **On Your Server - Remove Old Config:**
   ```bash
   # Remove any old nginx configurations
   sudo rm -f /etc/nginx/sites-enabled/legofit-explorer.com
   sudo rm -f /etc/nginx/sites-available/legofit-explorer.com
   
   # Reload Nginx
   sudo nginx -t
   sudo systemctl reload nginx
   ```

---

## Option 3: Let Domain Expire (No Action Needed)

If you own the domain through Hostinger:
- Just don't renew `legofit-explorer.com` when it expires
- Keep paying for `renovation.legofit.eu`
- The old domain will become unavailable after expiration

---

## Recommended Approach

### Phase 1: Redirect (Now - Next 3-6 months)
```bash
sudo bash setup_redirect.sh
```
- Keeps old links working
- Gives users time to update bookmarks
- SEO friendly (301 redirects)

### Phase 2: Monitor (3-6 months)
- Check server logs to see if old domain is still being used:
  ```bash
  sudo tail -f /var/log/nginx/access.log | grep legofit-explorer
  ```

### Phase 3: Remove (After 6 months)
- If traffic is minimal, remove DNS records in Hostinger
- Or let domain expire

---

## FAQ

### Q: Will this affect my SEO?
A: 301 redirects (Option 1) are SEO-friendly. Search engines will update to the new domain.

### Q: Can I keep both domains?
A: Yes! Either redirect or serve the same content on both. But having one canonical domain is cleaner.

### Q: Do I need to do anything about SSL for old domain?
A: If redirecting via HTTP only, no SSL needed for old domain. If you want HTTPS redirect, you'd need to keep the SSL cert for the old domain.

### Q: How long do DNS changes take?
A: Usually 1-4 hours, but can take up to 48 hours for full global propagation.

### Q: Will I lose the old domain?
A: 
- Option 1 (Redirect): You keep the domain, just redirect it
- Option 2 (Remove DNS): You keep the domain, but it won't resolve
- Option 3 (Expire): You lose the domain after expiration

---

## Current Hostinger Domain Management

Based on your hosting at Hostinger:

### To Access:
1. Go to: https://hpanel.hostinger.com
2. Login → Domains → Select `legofit-explorer.com`

### You'll see:
- Domain status
- Expiration date
- DNS records
- Nameservers

### DNS Records to Check:
```
Type: A
Name: @ (or legofit-explorer.com)
Points to: [Your Server IP - probably 72.60.180.76]
```

This is what makes the old domain still work!

---

## My Recommendation

**🎯 Use Option 1 (Redirect):**

```bash
cd /var/www/legofit-explorer.com
sudo bash setup_redirect.sh
```

**Benefits:**
- ✅ No broken links for users
- ✅ SEO preserved
- ✅ Professional approach
- ✅ Can remove later if needed
- ✅ Takes 30 seconds to implement

**Then in 6-12 months:**
- Remove DNS in Hostinger if you want
- Or just let the domain expire

---

## Need Help?

Check current nginx configs:
```bash
ls -la /etc/nginx/sites-enabled/
sudo nginx -t
```

View current redirects:
```bash
curl -I http://legofit-explorer.com
curl -I http://renovation.legofit.eu
```

